FROM apache/spark:4.1.1
USER root
WORKDIR /opt/spark/

RUN apt-get update
RUN apt install curl -y

COPY ./start.sh ./start.sh
RUN chmod +x start.sh

COPY ./requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Delta Lake 4.3.1 + AWS SDK v2 + Avro + Unity Catalog Spark connector
RUN curl "https://repo1.maven.org/maven2/software/amazon/awssdk/bundle/2.29.52/bundle-2.29.52.jar" -o /opt/spark/jars/bundle-2.29.52.jar \
    && curl "https://repo1.maven.org/maven2/io/delta/delta-spark_4.1_2.13/4.3.1/delta-spark_4.1_2.13-4.3.1.jar" -o /opt/spark/jars/delta-spark_4.1_2.13-4.3.1.jar \
    && curl "https://repo1.maven.org/maven2/io/delta/delta-storage/4.3.1/delta-storage-4.3.1.jar" -o /opt/spark/jars/delta-storage-4.3.1.jar \
    && curl "https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.4.2/hadoop-aws-3.4.2.jar" -o /opt/spark/jars/hadoop-aws-3.4.2.jar \
    && curl "https://repo1.maven.org/maven2/org/apache/spark/spark-avro_2.13/4.1.1/spark-avro_2.13-4.1.1.jar" -o /opt/spark/jars/spark-avro_2.13-4.1.1.jar \
    && curl "https://repo1.maven.org/maven2/io/unitycatalog/unitycatalog-spark_4.1_2.13/0.5.0/unitycatalog-spark_4.1_2.13-0.5.0.jar" -o /opt/spark/jars/unitycatalog-spark_4.1_2.13-0.5.0.jar \
    && curl "https://repo1.maven.org/maven2/io/unitycatalog/unitycatalog-client/0.5.0/unitycatalog-client-0.5.0.jar" -o /opt/spark/jars/unitycatalog-client-0.5.0.jar \
    && curl "https://repo1.maven.org/maven2/io/unitycatalog/unitycatalog-hadoop/0.5.0/unitycatalog-hadoop-0.5.0.jar" -o /opt/spark/jars/unitycatalog-hadoop-0.5.0.jar \
    && curl "https://repo1.maven.org/maven2/io/delta/delta-iceberg_2.13/4.3.1/delta-iceberg_2.13-4.3.1.jar" -o /opt/spark/jars/delta-iceberg_2.13-4.3.1.jar
