FROM bitnamilegacy/spark:3.5.3
USER root

RUN apt-get update
RUN apt install curl -y

COPY ./start.sh ./start.sh
RUN chmod +x start.sh

COPY ./requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Delta Lake 3.2.1 + AWS SDK + Avro + Unity Catalog Spark connector
RUN curl "https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.367/aws-java-sdk-bundle-1.12.367.jar" -o /opt/bitnami/spark/jars/aws-java-sdk-bundle-1.12.367.jar \
    && curl "https://repo1.maven.org/maven2/io/delta/delta-spark_2.12/3.2.1/delta-spark_2.12-3.2.1.jar" -o /opt/bitnami/spark/jars/delta-spark_2.12-3.2.1.jar \
    && curl "https://repo1.maven.org/maven2/io/delta/delta-storage/3.2.1/delta-storage-3.2.1.jar" -o /opt/bitnami/spark/jars/delta-storage-3.2.1.jar \
    && curl "https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.6/hadoop-aws-3.3.6.jar" -o /opt/bitnami/spark/jars/hadoop-aws-3.3.6.jar \
    && curl "https://repo1.maven.org/maven2/org/apache/spark/spark-avro_2.12/3.5.3/spark-avro_2.12-3.5.3.jar" -o /opt/bitnami/spark/jars/spark-avro_2.12-3.5.3.jar \
    && curl "https://repo1.maven.org/maven2/io/unitycatalog/unitycatalog-spark_2.12/0.2.1/unitycatalog-spark_2.12-0.2.1.jar" -o /opt/bitnami/spark/jars/unitycatalog-spark_2.12-0.2.1.jar \
    && curl "https://repo1.maven.org/maven2/io/delta/delta-iceberg_2.12/3.2.1/delta-iceberg_2.12-3.2.1.jar" -o /opt/bitnami/spark/jars/delta-iceberg_2.12-3.2.1.jar

WORKDIR /opt/bitnami/spark/
