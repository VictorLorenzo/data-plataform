FROM apache/nifi:1.27.0

USER root

RUN mkdir -p /opt/nifi/drivers
RUN chown -R nifi:nifi /opt/nifi/
RUN apt-get update && apt-get install -y curl 

USER nifi

RUN curl -L "https://go.microsoft.com/fwlink/?linkid=2166848" -o /opt/nifi/drivers/mssql-jdbc-9.4.0.jre8.jar
RUN curl -L "https://www.datanucleus.org/downloads/maven2/oracle/ojdbc6/11.2.0.3/ojdbc6-11.2.0.3.jar" -o /opt/nifi/drivers/ojdbc6-11.2.0.3.jar

# Start Apache NiFi
CMD ["nifi.sh", "run"]