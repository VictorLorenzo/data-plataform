FROM apache/airflow:3.2.2-python3.11

USER root
RUN apt-get update
RUN apt install -y default-jdk curl
RUN apt-get autoremove -yqq --purge
RUN apt-get clean
RUN rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

# Pre-download Spark JARs at build time to avoid re-downloading on every container restart
ENV SPARK_JARS_DIR=/home/airflow/spark-jars
RUN mkdir -p ${SPARK_JARS_DIR}

# antlr4-runtime dropped: ANTLR is shaded into Delta/Catalyst as of Delta 4.x,
# no longer a standalone dependency. aws-java-sdk-bundle (SDK v1) replaced by
# the SDK v2 bundle (hadoop-aws 3.4.2 requires it); pinned to 2.29.52 rather
# than latest since SDK v2 >=2.30.0 is documented as broken against
# S3-compatible stores.
RUN curl -fSL -o ${SPARK_JARS_DIR}/delta-spark_4.1_2.13-4.3.1.jar \
      https://repo1.maven.org/maven2/io/delta/delta-spark_4.1_2.13/4.3.1/delta-spark_4.1_2.13-4.3.1.jar && \
    curl -fSL -o ${SPARK_JARS_DIR}/delta-storage-4.3.1.jar \
      https://repo1.maven.org/maven2/io/delta/delta-storage/4.3.1/delta-storage-4.3.1.jar && \
    curl -fSL -o ${SPARK_JARS_DIR}/hadoop-aws-3.4.2.jar \
      https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.4.2/hadoop-aws-3.4.2.jar && \
    curl -fSL -o ${SPARK_JARS_DIR}/bundle-2.29.52.jar \
      https://repo1.maven.org/maven2/software/amazon/awssdk/bundle/2.29.52/bundle-2.29.52.jar && \
    curl -fSL -o ${SPARK_JARS_DIR}/spark-avro_2.13-4.1.1.jar \
      https://repo1.maven.org/maven2/org/apache/spark/spark-avro_2.13/4.1.1/spark-avro_2.13-4.1.1.jar && \
    curl -fSL -o ${SPARK_JARS_DIR}/unitycatalog-spark_4.1_2.13-0.5.0.jar \
      https://repo1.maven.org/maven2/io/unitycatalog/unitycatalog-spark_4.1_2.13/0.5.0/unitycatalog-spark_4.1_2.13-0.5.0.jar && \
    curl -fSL -o ${SPARK_JARS_DIR}/unitycatalog-client-0.5.0.jar \
      https://repo1.maven.org/maven2/io/unitycatalog/unitycatalog-client/0.5.0/unitycatalog-client-0.5.0.jar && \
    curl -fSL -o ${SPARK_JARS_DIR}/unitycatalog-hadoop-0.5.0.jar \
      https://repo1.maven.org/maven2/io/unitycatalog/unitycatalog-hadoop/0.5.0/unitycatalog-hadoop-0.5.0.jar && \
    curl -fSL -o ${SPARK_JARS_DIR}/delta-iceberg_2.13-4.3.1.jar \
      https://repo1.maven.org/maven2/io/delta/delta-iceberg_2.13/4.3.1/delta-iceberg_2.13-4.3.1.jar

RUN chown -R airflow:0 ${SPARK_JARS_DIR}

USER airflow

COPY ./requirements.txt .
RUN pip install -r requirements.txt
