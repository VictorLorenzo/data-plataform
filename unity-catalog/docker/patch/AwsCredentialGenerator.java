package io.unitycatalog.server.service.credential.aws;

import com.auth0.jwt.JWT;
import com.auth0.jwt.algorithms.Algorithm;
import io.unitycatalog.server.model.AwsIamRoleResponse;
import io.unitycatalog.server.persist.dao.CredentialDAO;
import io.unitycatalog.server.service.credential.CredentialContext;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Duration;
import java.time.Instant;
import java.util.Base64;
import java.util.Optional;
import java.util.UUID;
import software.amazon.awssdk.auth.credentials.AwsBasicCredentials;
import software.amazon.awssdk.auth.credentials.AwsCredentialsProvider;
import software.amazon.awssdk.auth.credentials.DefaultCredentialsProvider;
import software.amazon.awssdk.auth.credentials.StaticCredentialsProvider;
import software.amazon.awssdk.core.exception.SdkClientException;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.regions.providers.DefaultAwsRegionProviderChain;
import software.amazon.awssdk.services.sts.StsClient;
import software.amazon.awssdk.services.sts.StsClientBuilder;
import software.amazon.awssdk.services.sts.model.AssumeRoleRequest;
import software.amazon.awssdk.services.sts.model.Credentials;

/**
 * Generates credentials based on the provided {@link CredentialContext}.
 *
 * <p>Currently supported implementations include:
 *
 * <ul>
 *   <li>{@link StaticAwsCredentialGenerator}: returns fixed credentials defined in configuration.
 *   <li>{@link StsAwsCredentialGenerator}: retrieves temporary, expiring credentials from AWS STS.
 * </ul>
 *
 * <p>Test scenarios can provide custom {@link AwsCredentialGenerator} implementations. For example,
 * a time-based generator can be used in end-to-end tests to validate credential renewal behavior.
 */
public interface AwsCredentialGenerator {
  Credentials generate(CredentialContext ctx);

  class StaticAwsCredentialGenerator implements AwsCredentialGenerator {
    private final String accessKeyId;
    private final String secretKey;
    private final String sessionToken;

    // Cloudflare R2 (S3-compatible, but not real AWS: no STS AssumeRole support).
    // When S3_ENDPOINT points at R2, vend R2's own locally-signed temporary
    // credentials instead of a static/fake session token, per:
    // https://developers.cloudflare.com/r2/api/s3/temporary-credentials/
    private static final String S3_ENDPOINT = System.getenv("S3_ENDPOINT");
    private static final boolean IS_R2 =
        S3_ENDPOINT != null && S3_ENDPOINT.contains("r2.cloudflarestorage.com");

    public StaticAwsCredentialGenerator(S3StorageConfig config) {
      this.accessKeyId = config.getAccessKey();
      this.secretKey = config.getSecretKey();
      this.sessionToken = config.getSessionToken();
    }

    @Override
    public Credentials generate(CredentialContext ctx) {
      if (IS_R2) {
        return generateR2TemporaryCredentials(ctx);
      }
      return Credentials.builder()
          .accessKeyId(accessKeyId)
          .secretAccessKey(secretKey)
          .sessionToken(sessionToken)
          .build();
    }

    /**
     * Locally signs an R2 temporary-credential JWT using the parent (static) secret key as the
     * HMAC signing key — no network round trip to R2's Temporary Credentials API is needed.
     * Per Cloudflare's spec: accessKeyId is reused unchanged, secretAccessKey becomes the SHA-256
     * hex digest of the signed JWT, and sessionToken is base64("jwt/" + signedJwt).
     */
    private Credentials generateR2TemporaryCredentials(CredentialContext ctx) {
      String accountId = S3_ENDPOINT.replaceFirst("^https?://", "").split("\\.")[0];
      String audience = S3_ENDPOINT.replaceFirst("^https?://", "");
      String bucket = extractBucket(ctx);

      Instant now = Instant.now();
      Instant expiry = now.plus(Duration.ofHours(1));

      String signedJwt =
          JWT.create()
              .withIssuer(accessKeyId)
              .withSubject(accountId)
              .withAudience(audience)
              .withIssuedAt(now)
              .withExpiresAt(expiry)
              .withClaim("bucket", bucket)
              .withClaim("scope", "object-read-write")
              .sign(Algorithm.HMAC256(secretKey));

      String derivedSecretKey = sha256Hex(signedJwt);
      String derivedSessionToken =
          Base64.getEncoder()
              .encodeToString(("jwt/" + signedJwt).getBytes(StandardCharsets.UTF_8));

      return Credentials.builder()
          .accessKeyId(accessKeyId)
          .secretAccessKey(derivedSecretKey)
          .sessionToken(derivedSessionToken)
          .expiration(expiry)
          .build();
    }

    private static String extractBucket(CredentialContext ctx) {
      // storageBase is a NormalizedURL like "s3://bucket"; the bucket name is its host component.
      return ctx.getStorageBase().toUri().getHost();
    }

    private static String sha256Hex(String input) {
      try {
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        byte[] hash = digest.digest(input.getBytes(StandardCharsets.UTF_8));
        StringBuilder sb = new StringBuilder(hash.length * 2);
        for (byte b : hash) {
          sb.append(String.format("%02x", b));
        }
        return sb.toString();
      } catch (NoSuchAlgorithmException e) {
        throw new RuntimeException(e);
      }
    }
  }

  class StsAwsCredentialGenerator implements AwsCredentialGenerator {
    private final StsClient stsClient;
    // This is the role ARN to assume for the per-bucket config. Otherwise, the CredentialContext
    // contains a CredentialDAO and it will assume the role ARN in CredentialDAO instead.
    private final String staticAwsRoleArn;

    public StsAwsCredentialGenerator(StsClientBuilder builder, S3StorageConfig config) {
      // Get STS region
      Region region;
      if (config.getRegion() != null && !config.getRegion().isEmpty()) {
        region = Region.of(config.getRegion());
      } else {
        try {
          region = DefaultAwsRegionProviderChain.builder().build().getRegion();
        } catch (SdkClientException e) {
          region = Region.AWS_GLOBAL;
        }
      }

      AwsCredentialsProvider credentialsProvider;
      if (config.getAccessKey() != null && !config.getAccessKey().isEmpty()) {
        // Build STS client using keys if they are specified in the config.
        credentialsProvider =
            StaticCredentialsProvider.create(
                AwsBasicCredentials.create(config.getAccessKey(), config.getSecretKey()));
      } else {
        // Otherwise just defer to DefaultCredentialsProvider
        credentialsProvider = DefaultCredentialsProvider.create();
      }

      this.stsClient = builder.region(region).credentialsProvider(credentialsProvider).build();
      this.staticAwsRoleArn = config.getAwsRoleArn();
    }

    @Override
    public Credentials generate(CredentialContext ctx) {
      Optional<AwsIamRoleResponse> awsIamRole =
          ctx.getCredentialDAO().map(CredentialDAO::getAwsIamRoleResponse);
      // Assume the role along with the externalId specified in CredentialDAO. If there's no
      // CredentialDAO, assume staticAwsRoleArn from the per-bucket config.
      String roleArn = awsIamRole.map(AwsIamRoleResponse::getRoleArn).orElse(staticAwsRoleArn);
      // externalId is only from CredentialDAO. Per-bucket config does not need it.
      Optional<String> externalId = awsIamRole.map(AwsIamRoleResponse::getExternalId);

      String awsPolicy = AwsPolicyGenerator.generatePolicy(ctx.getPrivileges(), ctx.getLocations());
      String roleSessionName = "uc-%s".formatted(UUID.randomUUID());

      AssumeRoleRequest.Builder roleRequestBuilder =
          AssumeRoleRequest.builder()
              .roleArn(roleArn)
              .policy(awsPolicy)
              .roleSessionName(roleSessionName)
              .durationSeconds((int) Duration.ofHours(1).toSeconds());
      externalId.ifPresent(roleRequestBuilder::externalId);

      return stsClient.assumeRole(roleRequestBuilder.build()).credentials();
    }
  }
}
