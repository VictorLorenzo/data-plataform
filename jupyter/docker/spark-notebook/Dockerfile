FROM jupyter/all-spark-notebook:python-3.8

USER root 

COPY requirements.txt ./requirements.txt

RUN apt-get update && apt-get install -y net-tools

RUN pip install --no-cache-dir -r requirements.txt

RUN curl -O https://archive.apache.org/dist/spark/spark-3.4.1/spark-3.4.1-bin-hadoop3.tgz \
    && tar zxvf spark-3.4.1-bin-hadoop3.tgz \
    && rm -rf spark-3.4.1-bin-hadoop3.tgz \
    && mv spark-3.4.1-bin-hadoop3/ /usr/local/ \
    && rm -rf /usr/local/spark \
    && rm -rf /usr/local/spark-3.3.0-bin-hadoop3 \
    && ln -s /usr/local/spark-3.4.1-bin-hadoop3 /usr/local/spark

RUN curl -O https://repo1.maven.org/maven2/software/amazon/awssdk/s3/2.18.41/s3-2.18.41.jar \
    && curl -O https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk/1.12.136/aws-java-sdk-1.12.137.jar \
    && curl -O https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.11.1026/aws-java-sdk-bundle-1.11.1026.jar \
    && curl -O https://repo1.maven.org/maven2/io/delta/delta-storage/2.4.0/delta-storage-2.4.0.jar \
    && curl -O https://repo1.maven.org/maven2/io/delta/delta-core_2.12/2.4.0/delta-core_2.12-2.4.0.jar \
    && curl -O https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.2/hadoop-aws-3.3.2.jar \
    && curl -O https://repo1.maven.org/maven2/org/apache/kyuubi/kyuubi-hive-jdbc-shaded/1.9.1/kyuubi-hive-jdbc-shaded-1.9.1.jar \    
    && curl -O https://repo1.maven.org/maven2/org/apache/kyuubi/kyuubi-extension-spark-jdbc-dialect_2.12/1.9.1/kyuubi-extension-spark-jdbc-dialect_2.12-1.9.1.jar \
    && curl -O https://repo1.maven.org/maven2/org/apache/spark/spark-avro_2.12/3.4.1/spark-avro_2.12-3.4.1.jar \
    && mv s3-2.18.41.jar /usr/local/spark/jars \
    && mv aws-java-sdk-1.12.137.jar /usr/local/spark/jars \
    && mv aws-java-sdk-bundle-1.11.1026.jar /usr/local/spark/jars \
    && mv delta-storage-2.4.0.jar /usr/local/spark/jars \
    && mv delta-core_2.12-2.4.0.jar /usr/local/spark/jars \
    && mv hadoop-aws-3.3.2.jar /usr/local/spark/jars \
    && mv kyuubi-hive-jdbc-shaded-1.9.1.jar /usr/local/spark/jars \
    && mv kyuubi-extension-spark-jdbc-dialect_2.12-1.9.1.jar /usr/local/spark/jars \
    && mv spark-avro_2.12-3.4.1.jar /usr/local/spark/jars

COPY jupyter-config/spark-defaults.conf /usr/local/spark/conf/spark-defaults.conf