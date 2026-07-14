FROM unitycatalog/unitycatalog:v0.5.0

USER root

# Patch 1: S3-compatible endpoint support for UC's own internal Iceberg reads.
# The original class has hardcoded forcePathStyle(false) and no custom endpoint,
# making it impossible to read Iceberg metadata from MinIO/R2/etc.
#
# This patch adds:
# - S3_ENDPOINT env var: custom S3 endpoint URL (e.g. https://<account>.r2.cloudflarestorage.com)
# - When S3_ENDPOINT is set: forces path-style access + AwsBasicCredentials (no session token)
COPY patch/FileIOFactory.java /tmp/FileIOFactory.java

# Patch 2: vend real R2 temporary credentials (locally-signed JWT, per
# https://developers.cloudflare.com/r2/api/s3/temporary-credentials/) to Spark
# clients instead of AWS STS AssumeRole, which R2 does not implement. Without
# this, UC's dynamic per-path credential vending (on by default since 0.3.0)
# sends R2-flavored fake credentials to real AWS, which correctly rejects them.
COPY patch/AwsCredentialGenerator.java /tmp/AwsCredentialGenerator.java

# lombok and java-jwt (com.auth0) are compile-time/runtime deps already on
# the image's own classpath but not exported to server/target/classpath, so
# they must be added explicitly here.
RUN rm -f /home/unitycatalog/server/target/classes/io/unitycatalog/server/service/iceberg/FileIOFactory.class && \
    rm -f "/home/unitycatalog/server/target/classes/io/unitycatalog/server/service/iceberg/FileIOFactory\$1.class" && \
    rm -f /home/unitycatalog/server/target/classes/io/unitycatalog/server/service/credential/aws/AwsCredentialGenerator*.class && \
    LOMBOK_JAR="$(find /home/unitycatalog/.cache -iname 'lombok-*.jar' | sort -V | tail -1)" && \
    javac -cp "$(cat /home/unitycatalog/server/target/classpath):${LOMBOK_JAR}" \
      -d /home/unitycatalog/server/target/classes \
      /tmp/FileIOFactory.java /tmp/AwsCredentialGenerator.java && \
    rm /tmp/FileIOFactory.java /tmp/AwsCredentialGenerator.java

USER unitycatalog
