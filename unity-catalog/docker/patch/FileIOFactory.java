package io.unitycatalog.server.service.iceberg;

import io.unitycatalog.server.exception.BaseException;
import io.unitycatalog.server.model.AwsCredentials;
import io.unitycatalog.server.model.AzureUserDelegationSAS;
import io.unitycatalog.server.model.GcpOauthToken;
import io.unitycatalog.server.service.credential.CredentialContext;
import io.unitycatalog.server.service.credential.StorageCredentialVendor;
import io.unitycatalog.server.service.credential.aws.S3StorageConfig;
import io.unitycatalog.server.service.credential.azure.ADLSLocationUtils;
import io.unitycatalog.server.utils.NormalizedURL;
import io.unitycatalog.server.utils.ServerProperties;
import io.unitycatalog.server.utils.UriScheme;
import lombok.SneakyThrows;
import org.apache.iceberg.aws.s3.S3FileIO;
import org.apache.iceberg.azure.AzureProperties;
import org.apache.iceberg.azure.adlsv2.ADLSFileIO;
import org.apache.iceberg.gcp.GCPProperties;
import org.apache.iceberg.gcp.gcs.GCSFileIO;
import org.apache.iceberg.io.FileIO;
import software.amazon.awssdk.auth.credentials.AwsBasicCredentials;
import software.amazon.awssdk.auth.credentials.AwsCredentialsProvider;
import software.amazon.awssdk.auth.credentials.AwsSessionCredentials;
import software.amazon.awssdk.auth.credentials.DefaultCredentialsProvider;
import software.amazon.awssdk.auth.credentials.StaticCredentialsProvider;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.S3ClientBuilder;

import java.net.URI;
import java.util.Map;
import java.util.Set;

/**
 * Patched FileIOFactory with S3-compatible object store support (MinIO, etc.), re-derived
 * against the v0.5.0 StorageCredentialVendor/NormalizedURL API (the v0.2.1 patch targeted the
 * older CredentialOperations/URI-based API and does not apply here).
 *
 * Environment variables:
 *   S3_ENDPOINT          - custom S3 endpoint (e.g. http://minio:9000)
 *   S3_PATH_STYLE_ACCESS - "true" to force path-style (auto-enabled when S3_ENDPOINT is set)
 *
 * When S3_ENDPOINT is set, credentials are sent as AwsBasicCredentials (no session token)
 * to avoid STS validation failures on S3-compatible stores.
 */
public class FileIOFactory {

  private final StorageCredentialVendor storageCredentialVendor;
  private final Map<NormalizedURL, S3StorageConfig> s3Configurations;
  // FIXME!! privileges are defaulted to READ only here for now as Iceberg REST impl doesn't
  //  support write
  private final Set<CredentialContext.Privilege> privileges =
      Set.of(CredentialContext.Privilege.SELECT);

  private static final String S3_ENDPOINT = System.getenv("S3_ENDPOINT");

  public FileIOFactory(
      StorageCredentialVendor storageCredentialVendor, ServerProperties serverProperties) {
    this.storageCredentialVendor = storageCredentialVendor;
    this.s3Configurations = serverProperties.getS3Configurations();
  }

  // TODO: Cache fileIOs
  public FileIO getFileIO(NormalizedURL location) {
    return switch (UriScheme.fromURI(location.toUri())) {
      case ABFS, ABFSS -> getADLSFileIO(location);
      case GS -> getGCSFileIO(location);
      case S3 -> getS3FileIO(location);
      case FILE, NULL -> new SimpleLocalFileIO();
    };
  }

  protected ADLSFileIO getADLSFileIO(NormalizedURL location) {
    AzureUserDelegationSAS credential =
        storageCredentialVendor.vendCredential(location, privileges).getAzureUserDelegationSas();
    ADLSLocationUtils.ADLSLocationParts locationParts = ADLSLocationUtils.parseLocation(location);

    // NOTE: when fileio caching is implemented, need to set/deal with expiry here
    Map<String, String> properties =
        Map.of(AzureProperties.ADLS_SAS_TOKEN_PREFIX + locationParts.account(),
            credential.getSasToken());

    ADLSFileIO result = new ADLSFileIO();
    result.initialize(properties);
    return result;
  }

  @SneakyThrows
  protected GCSFileIO getGCSFileIO(NormalizedURL location) {
    GcpOauthToken gcpToken =
        storageCredentialVendor.vendCredential(location, privileges).getGcpOauthToken();

    // NOTE: when fileio caching is implemented, need to set/deal with expiry here
    Map<String, String> properties =
        Map.of(GCPProperties.GCS_OAUTH2_TOKEN, gcpToken.getOauthToken());

    GCSFileIO result = new GCSFileIO();
    result.initialize(properties);
    return result;
  }

  protected S3FileIO getS3FileIO(NormalizedURL location) {
    S3StorageConfig s3StorageConfig = s3Configurations.get(location.getStorageBase());

    S3FileIO s3FileIO =
        new S3FileIO(() -> getS3Client(getAwsCredentialsProvider(location),
            s3StorageConfig.getRegion()));

    s3FileIO.initialize(Map.of());

    return s3FileIO;
  }

  protected S3Client getS3Client(AwsCredentialsProvider awsCredentialsProvider, String region) {
    S3ClientBuilder builder = S3Client.builder()
        .region(Region.of(region))
        .credentialsProvider(awsCredentialsProvider);

    if (S3_ENDPOINT != null && !S3_ENDPOINT.isEmpty()) {
      builder.endpointOverride(URI.create(S3_ENDPOINT));
      builder.forcePathStyle(true);
    } else {
      builder.forcePathStyle(false);
    }

    return builder.build();
  }

  private static final boolean IS_R2 =
      S3_ENDPOINT != null && S3_ENDPOINT.contains("r2.cloudflarestorage.com");

  private AwsCredentialsProvider getAwsCredentialsProvider(NormalizedURL location) {
    try {
      AwsCredentials awsSessionCredentials =
          storageCredentialVendor.vendCredential(location, privileges).getAwsTempCredentials();

      // R2's locally-signed JWT credential scheme (see AwsCredentialGenerator) derives
      // secretAccessKey = sha256Hex(jwt) and packs the JWT itself into the session
      // token (sessionToken = base64("jwt/" + jwt)). R2 needs that session token to
      // validate the request signature at all - dropping it (as done below for MinIO)
      // makes every request fail with "signature we calculated does not match".
      if (IS_R2) {
        return StaticCredentialsProvider.create(
            AwsSessionCredentials.create(
                awsSessionCredentials.getAccessKeyId(),
                awsSessionCredentials.getSecretAccessKey(),
                awsSessionCredentials.getSessionToken()));
      }

      // When using a generic S3-compatible store (e.g. MinIO) with static/placeholder
      // credentials, use basic credentials without session token. MinIO rejects fake
      // session tokens with 403.
      if (S3_ENDPOINT != null && !S3_ENDPOINT.isEmpty()) {
        return StaticCredentialsProvider.create(
            AwsBasicCredentials.create(
                awsSessionCredentials.getAccessKeyId(),
                awsSessionCredentials.getSecretAccessKey()));
      }

      return StaticCredentialsProvider.create(
          AwsSessionCredentials.create(
              awsSessionCredentials.getAccessKeyId(),
              awsSessionCredentials.getSecretAccessKey(),
              awsSessionCredentials.getSessionToken()));
    } catch (BaseException e) {
      return DefaultCredentialsProvider.create();
    }
  }
}
