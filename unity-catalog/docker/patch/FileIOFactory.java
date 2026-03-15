package io.unitycatalog.server.service.iceberg;

import com.google.auth.oauth2.AccessToken;
import io.unitycatalog.server.exception.BaseException;
import io.unitycatalog.server.persist.utils.ServerPropertiesUtils;
import io.unitycatalog.server.service.credential.CredentialContext;
import io.unitycatalog.server.service.credential.CredentialOperations;
import io.unitycatalog.server.service.credential.aws.S3StorageConfig;
import io.unitycatalog.server.service.credential.azure.ADLSLocationUtils;
import io.unitycatalog.server.service.credential.azure.AzureCredential;
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
import software.amazon.awssdk.services.sts.model.Credentials;

import java.net.URI;
import java.util.Map;
import java.util.Set;

import static io.unitycatalog.server.utils.Constants.URI_SCHEME_ABFS;
import static io.unitycatalog.server.utils.Constants.URI_SCHEME_ABFSS;
import static io.unitycatalog.server.utils.Constants.URI_SCHEME_GS;
import static io.unitycatalog.server.utils.Constants.URI_SCHEME_S3;

/**
 * Patched FileIOFactory with S3-compatible object store support (MinIO, etc.).
 *
 * Environment variables:
 *   S3_ENDPOINT          - custom S3 endpoint (e.g. http://minio:9000)
 *   S3_PATH_STYLE_ACCESS - "true" to force path-style (auto-enabled when S3_ENDPOINT is set)
 *
 * When S3_ENDPOINT is set, credentials are sent as AwsBasicCredentials (no session token)
 * to avoid STS validation failures on S3-compatible stores.
 */
public class FileIOFactory {

  private final CredentialOperations credentialOps;

  private static final String S3_ENDPOINT = System.getenv("S3_ENDPOINT");

  public FileIOFactory(CredentialOperations credentialOps) {
    this.credentialOps = credentialOps;
  }

  public FileIO getFileIO(URI tableLocationUri) {
    return switch (tableLocationUri.getScheme()) {
      case URI_SCHEME_ABFS, URI_SCHEME_ABFSS -> getADLSFileIO(tableLocationUri);
      case URI_SCHEME_GS -> getGCSFileIO(tableLocationUri);
      case URI_SCHEME_S3 -> getS3FileIO(tableLocationUri);
      default -> new SimpleLocalFileIO();
    };
  }

  protected ADLSFileIO getADLSFileIO(URI tableLocationUri) {
    CredentialContext credentialContext = getCredentialContextFromTableLocation(tableLocationUri);
    AzureCredential credential = credentialOps.vendAzureCredential(credentialContext);
    ADLSLocationUtils.ADLSLocationParts locationParts =
        ADLSLocationUtils.parseLocation(tableLocationUri.toString());
    Map<String, String> properties =
        Map.of(AzureProperties.ADLS_SAS_TOKEN_PREFIX + locationParts.account(),
            credential.getSasToken());
    ADLSFileIO result = new ADLSFileIO();
    result.initialize(properties);
    return result;
  }

  protected GCSFileIO getGCSFileIO(URI tableLocationUri) {
    CredentialContext credentialContext = getCredentialContextFromTableLocation(tableLocationUri);
    AccessToken gcpToken = credentialOps.vendGcpToken(credentialContext);
    Map<String, String> properties =
        Map.of(GCPProperties.GCS_OAUTH2_TOKEN, gcpToken.getTokenValue());
    GCSFileIO result = new GCSFileIO();
    result.initialize(properties);
    return result;
  }

  protected S3FileIO getS3FileIO(URI tableLocationUri) {
    CredentialContext context = getCredentialContextFromTableLocation(tableLocationUri);
    S3StorageConfig s3StorageConfig =
        ServerPropertiesUtils.getInstance().getS3Configurations().get(context.getStorageBase());
    S3FileIO s3FileIO =
        new S3FileIO(() -> getS3Client(getAwsCredentialsProvider(context),
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

  private AwsCredentialsProvider getAwsCredentialsProvider(CredentialContext context) {
    try {
      Credentials creds = credentialOps.vendAwsCredential(context);

      // When using S3-compatible store (MinIO), use basic credentials without
      // session token. MinIO rejects fake session tokens with 403.
      if (S3_ENDPOINT != null && !S3_ENDPOINT.isEmpty()) {
        return StaticCredentialsProvider.create(
            AwsBasicCredentials.create(creds.accessKeyId(), creds.secretAccessKey()));
      }

      return StaticCredentialsProvider.create(
          AwsSessionCredentials.create(
              creds.accessKeyId(), creds.secretAccessKey(), creds.sessionToken()));
    } catch (BaseException e) {
      return DefaultCredentialsProvider.create();
    }
  }

  private CredentialContext getCredentialContextFromTableLocation(URI tableLocationUri) {
    return CredentialContext.create(tableLocationUri,
        Set.of(CredentialContext.Privilege.SELECT));
  }
}
