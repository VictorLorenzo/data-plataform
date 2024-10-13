FROM bitnami/spark:3.4.1
USER root
ENV LIVY_HOME /opt/bitnami/livy

RUN apt-get update
RUN apt install curl -y

COPY ./start.sh ./start.sh
RUN chmod +x start.sh

COPY ./requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

RUN curl "https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.367/aws-java-sdk-bundle-1.12.367.jar" -o /opt/bitnami/spark/jars/aws-java-sdk-1.12.367.jar \
    && curl "https://repo.maven.apache.org/maven2/io/delta/delta-core_2.12/2.4.0/delta-core_2.12-2.4.0.jar" -o /opt/bitnami/spark/jars/delta-core_2.12-2.4.0.jar \
    && curl "https://repo1.maven.org/maven2/io/delta/delta-storage/2.4.0/delta-storage-2.4.0.jar" -o /opt/bitnami/spark/jars/delta-storage-2.4.0.jar \
    && curl "https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.6/hadoop-aws-3.3.6.jar" -o /opt/bitnami/spark/jars/hadoop-aws-3.3.6.jar

WORKDIR /opt/bitnami/

RUN install_packages unzip \
    && curl "https://dlcdn.apache.org/incubator/livy/0.8.0-incubating/apache-livy-0.8.0-incubating_2.11-bin.zip" -O \
    && unzip "apache-livy-0.8.0-incubating_2.11-bin" \
    && rm -rf "apache-livy-0.8.0-incubating_2.11-bin.zip" \
    && mv "apache-livy-0.8.0-incubating_2.11-bin" $LIVY_HOME \
    && mkdir $LIVY_HOME/logs \
    && chown -R 1001:1001 $LIVY_HOME

WORKDIR /opt/bitnami/spark/