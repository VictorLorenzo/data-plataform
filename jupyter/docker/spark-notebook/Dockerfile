FROM jupyter/all-spark-notebook:python-3.11

USER root

COPY requirements.txt ./requirements.txt

RUN apt-get update && apt-get install -y net-tools

RUN pip install --no-cache-dir -r requirements.txt

# Spark 4.1.1
RUN curl -O https://archive.apache.org/dist/spark/spark-4.1.1/spark-4.1.1-bin-hadoop3.tgz \
    && tar zxvf spark-4.1.1-bin-hadoop3.tgz \
    && rm -rf spark-4.1.1-bin-hadoop3.tgz \
    && mv spark-4.1.1-bin-hadoop3/ /usr/local/ \
    && rm -rf /usr/local/spark \
    && rm -rf /usr/local/spark-3.3.0-bin-hadoop3 \
    && rm -rf /usr/local/spark-3.4.1-bin-hadoop3 \
    && ln -s /usr/local/spark-4.1.1-bin-hadoop3 /usr/local/spark

# Delta Lake 4.3.1 + AWS SDK v2 + Kyuubi JDBC client + Unity Catalog connector
# Note: kyuubi-extension-spark-jdbc-dialect has no Scala 2.13 build (checked
# Maven Central as of the Spark 4.1 migration), so it's dropped here along
# with its spark.sql.extensions entry in jupyter-config/spark-defaults.conf.
# kyuubi-hive-jdbc-shaded (the JDBC client itself, not the Spark extension)
# has no Scala suffix and is kept unchanged.
RUN curl -O https://repo1.maven.org/maven2/software/amazon/awssdk/bundle/2.29.52/bundle-2.29.52.jar \
    && curl -O https://repo1.maven.org/maven2/io/delta/delta-storage/4.3.1/delta-storage-4.3.1.jar \
    && curl -O https://repo1.maven.org/maven2/io/delta/delta-spark_4.1_2.13/4.3.1/delta-spark_4.1_2.13-4.3.1.jar \
    && curl -O https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.4.2/hadoop-aws-3.4.2.jar \
    && curl -O https://repo1.maven.org/maven2/org/apache/kyuubi/kyuubi-hive-jdbc-shaded/1.9.1/kyuubi-hive-jdbc-shaded-1.9.1.jar \
    && curl -O https://repo1.maven.org/maven2/org/apache/spark/spark-avro_2.13/4.1.1/spark-avro_2.13-4.1.1.jar \
    && curl -O https://repo1.maven.org/maven2/io/unitycatalog/unitycatalog-spark_4.1_2.13/0.5.0/unitycatalog-spark_4.1_2.13-0.5.0.jar \
    && curl -O https://repo1.maven.org/maven2/io/unitycatalog/unitycatalog-client/0.5.0/unitycatalog-client-0.5.0.jar \
    && curl -O https://repo1.maven.org/maven2/io/unitycatalog/unitycatalog-hadoop/0.5.0/unitycatalog-hadoop-0.5.0.jar \
    && mv bundle-2.29.52.jar /usr/local/spark/jars \
    && mv delta-storage-4.3.1.jar /usr/local/spark/jars \
    && mv delta-spark_4.1_2.13-4.3.1.jar /usr/local/spark/jars \
    && mv hadoop-aws-3.4.2.jar /usr/local/spark/jars \
    && mv kyuubi-hive-jdbc-shaded-1.9.1.jar /usr/local/spark/jars \
    && mv spark-avro_2.13-4.1.1.jar /usr/local/spark/jars \
    && mv unitycatalog-spark_4.1_2.13-0.5.0.jar /usr/local/spark/jars \
    && mv unitycatalog-client-0.5.0.jar /usr/local/spark/jars \
    && mv unitycatalog-hadoop-0.5.0.jar /usr/local/spark/jars \
    && curl -O https://repo1.maven.org/maven2/io/delta/delta-iceberg_2.13/4.3.1/delta-iceberg_2.13-4.3.1.jar \
    && mv delta-iceberg_2.13-4.3.1.jar /usr/local/spark/jars

COPY jupyter-config/spark-defaults.conf /usr/local/spark/conf/spark-defaults.conf
