FROM apache/airflow:2.9.1-python3.11

USER root
RUN apt-get update
RUN apt install -y default-jdk
RUN apt-get autoremove -yqq --purge
RUN apt-get clean
RUN rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
   
USER airflow

COPY ./requirements.txt .
RUN pip install -r requirements.txt