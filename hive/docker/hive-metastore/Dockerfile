FROM apache/hive:3.1.3

WORKDIR /opt

COPY ./hive-config/entrypoint.sh /entrypoint.sh

USER root

RUN apt-get update && \
    apt install curl -y && \
    apt-get install -y net-tools

# Download S3A Connector and AWS SDK
RUN curl -L "https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.1.0/hadoop-aws-3.1.0.jar" -o /opt/hive/lib/hadoop-aws-3.1.0.jar \
    && curl -L "https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.11.271/aws-java-sdk-bundle-1.11.271.jar" -o /opt/hive/lib/aws-java-sdk-bundle-1.11.271.jar

USER hive
EXPOSE 9083

ENTRYPOINT ["bash", "/entrypoint.sh"]