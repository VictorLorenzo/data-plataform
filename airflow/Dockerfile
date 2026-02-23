FROM apache/airflow:2.9.1-python3.11

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

RUN curl -fSL -o ${SPARK_JARS_DIR}/delta-spark_2.12-3.2.1.jar \
      https://repo1.maven.org/maven2/io/delta/delta-spark_2.12/3.2.1/delta-spark_2.12-3.2.1.jar && \
    curl -fSL -o ${SPARK_JARS_DIR}/delta-storage-3.2.1.jar \
      https://repo1.maven.org/maven2/io/delta/delta-storage/3.2.1/delta-storage-3.2.1.jar && \
    curl -fSL -o ${SPARK_JARS_DIR}/antlr4-runtime-4.9.3.jar \
      https://repo1.maven.org/maven2/org/antlr/antlr4-runtime/4.9.3/antlr4-runtime-4.9.3.jar && \
    curl -fSL -o ${SPARK_JARS_DIR}/hadoop-aws-3.3.4.jar \
      https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.4/hadoop-aws-3.3.4.jar && \
    curl -fSL -o ${SPARK_JARS_DIR}/aws-java-sdk-bundle-1.12.262.jar \
      https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.262/aws-java-sdk-bundle-1.12.262.jar && \
    curl -fSL -o ${SPARK_JARS_DIR}/spark-avro_2.12-3.5.3.jar \
      https://repo1.maven.org/maven2/org/apache/spark/spark-avro_2.12/3.5.3/spark-avro_2.12-3.5.3.jar && \
    curl -fSL -o ${SPARK_JARS_DIR}/unitycatalog-spark_2.12-0.2.1.jar \
      https://repo1.maven.org/maven2/io/unitycatalog/unitycatalog-spark_2.12/0.2.1/unitycatalog-spark_2.12-0.2.1.jar && \
    curl -fSL -o ${SPARK_JARS_DIR}/unitycatalog-client-0.2.1.jar \
      https://repo1.maven.org/maven2/io/unitycatalog/unitycatalog-client/0.2.1/unitycatalog-client-0.2.1.jar

RUN chown -R airflow:0 ${SPARK_JARS_DIR}

USER airflow

COPY ./requirements.txt .
RUN pip install -r requirements.txt
