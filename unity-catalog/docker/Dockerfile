FROM unitycatalog/unitycatalog:v0.2.1

USER root

# Patch FileIOFactory to support S3-compatible stores (MinIO).
# The original class has hardcoded forcePathStyle(false) and no custom endpoint,
# making it impossible to read Iceberg metadata from MinIO.
#
# This patch adds:
# - S3_ENDPOINT env var: custom S3 endpoint URL (e.g. http://minio:9000)
# - When S3_ENDPOINT is set: forces path-style access + AwsBasicCredentials (no session token)

COPY patch/FileIOFactory.java /tmp/FileIOFactory.java

# Compile the patched class against the server classpath.
# server/target/classes is FIRST on the classpath, so our compiled class
# takes priority over any other location.
RUN rm -f /home/unitycatalog/server/target/classes/io/unitycatalog/server/service/iceberg/FileIOFactory.class && \
    javac -cp "$(cat /home/unitycatalog/server/target/classpath)" \
      -d /home/unitycatalog/server/target/classes \
      /tmp/FileIOFactory.java && \
    rm /tmp/FileIOFactory.java

USER unitycatalog
