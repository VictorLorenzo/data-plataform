FROM apache/kyuubi:1.8.0-spark

USER root 

# Delta Lake 3.2.1 + AWS SDK + Unity Catalog connector
RUN curl -O https://repo1.maven.org/maven2/software/amazon/awssdk/s3/2.18.41/s3-2.18.41.jar \
    && curl -O https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk/1.12.136/aws-java-sdk-1.12.137.jar \
    && curl -O https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.11.1026/aws-java-sdk-bundle-1.11.1026.jar \
    && curl -O https://repo1.maven.org/maven2/io/delta/delta-storage/3.2.1/delta-storage-3.2.1.jar \
    && curl -O https://repo1.maven.org/maven2/io/delta/delta-spark_2.12/3.2.1/delta-spark_2.12-3.2.1.jar \
    && curl -O https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.2/hadoop-aws-3.3.2.jar \
    && curl -O https://repo1.maven.org/maven2/org/apache/spark/spark-avro_2.12/3.5.3/spark-avro_2.12-3.5.3.jar \
    && curl -O https://repo1.maven.org/maven2/io/unitycatalog/unitycatalog-spark_2.12/0.2.0/unitycatalog-spark_2.12-0.2.0.jar \
    && mv s3-2.18.41.jar /opt/kyuubi/jars \
    && mv aws-java-sdk-1.12.137.jar /opt/kyuubi/jars \
    && mv aws-java-sdk-bundle-1.11.1026.jar /opt/kyuubi/jars \
    && mv delta-storage-3.2.1.jar /opt/kyuubi/jars \
    && mv delta-spark_2.12-3.2.1.jar /opt/kyuubi/jars \
    && mv hadoop-aws-3.3.2.jar /opt/kyuubi/jars \
    && mv spark-avro_2.12-3.5.3.jar /opt/kyuubi/jars \
    && mv unitycatalog-spark_2.12-0.2.0.jar /opt/kyuubi/jars \
    && curl -O https://repo1.maven.org/maven2/io/delta/delta-iceberg_2.12/3.2.1/delta-iceberg_2.12-3.2.1.jar \
    && mv delta-iceberg_2.12-3.2.1.jar /opt/kyuubi/jars

USER kyuubi