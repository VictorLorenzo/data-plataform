FROM apache/nifi:2.8.0

USER root

RUN mkdir -p /opt/nifi/drivers
RUN chown -R nifi:nifi /opt/nifi/
RUN apt-get update && apt-get install -y curl

USER nifi

# MSSQL JDBC 13.4.0 (Java 11+ / Java 21 compatible)
RUN curl -L "https://repo1.maven.org/maven2/com/microsoft/sqlserver/mssql-jdbc/13.4.0.jre11/mssql-jdbc-13.4.0.jre11.jar" \
    -o /opt/nifi/drivers/mssql-jdbc-13.4.0.jre11.jar

# Oracle JDBC ojdbc11 (Java 11+ / Java 21 compatible)
RUN curl -L "https://repo1.maven.org/maven2/com/oracle/database/jdbc/ojdbc11/23.5.0.24.07/ojdbc11-23.5.0.24.07.jar" \
    -o /opt/nifi/drivers/ojdbc11-23.5.0.24.07.jar

# Start Apache NiFi
CMD ["nifi.sh", "run"]
