FROM bitnami/spark:3.5.3
USER root
ENV LIVY_HOME /opt/bitnami/livy

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
    && curl "https://repo1.maven.org/maven2/io/unitycatalog/unitycatalog-spark_2.12/0.2.0/unitycatalog-spark_2.12-0.2.0.jar" -o /opt/bitnami/spark/jars/unitycatalog-spark_2.12-0.2.0.jar

WORKDIR /opt/bitnami/

# Livy 0.8.0 Scala 2.12 (compatible with Spark 3.5.x)
RUN install_packages unzip \
    && curl "https://archive.apache.org/dist/incubator/livy/0.8.0-incubating/apache-livy-0.8.0-incubating_2.12-bin.zip" -O \
    && unzip "apache-livy-0.8.0-incubating_2.12-bin" \
    && rm -rf "apache-livy-0.8.0-incubating_2.12-bin.zip" \
    && mv "apache-livy-0.8.0-incubating_2.12-bin" $LIVY_HOME \
    && mkdir -p $LIVY_HOME/logs \
    && chown -R 1001:1001 $LIVY_HOME

WORKDIR /opt/bitnami/spark/
