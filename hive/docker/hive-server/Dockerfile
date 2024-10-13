FROM apache/hive:3.1.3

USER root

RUN apt-get update && \
    apt install curl -y && \
    apt-get install -y net-tools

RUN curl "https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.1.0/hadoop-aws-3.1.0.jar" -o lib/hadoop-aws-3.1.0.jar \
    && curl "https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.11.271/aws-java-sdk-bundle-1.11.271.jar " -o lib/aws-java-sdk-bundle-1.11.271.jar