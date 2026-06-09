FROM apache/nifi:2.8.0

USER root

RUN mkdir -p /opt/nifi/drivers /opt/nifi/scrapper_scripts
RUN chown -R nifi:nifi /opt/nifi/
RUN apt-get update && apt-get install -y curl python3 python3-pip python3-venv libpq-dev

# Python venv for scrapper scripts (isolado do Python interno do NiFi)
RUN python3 -m venv /opt/nifi/scrapper_venv \
    && /opt/nifi/scrapper_venv/bin/pip install --no-cache-dir \
        requests==2.32.3 \
        beautifulsoup4==4.12.3 \
        psycopg2-binary==2.9.9 \
        python-dotenv==1.0.1 \
    && chown -R nifi:nifi /opt/nifi/scrapper_venv

USER nifi

# MSSQL JDBC 13.4.0 (Java 11+ / Java 21 compatible)
RUN curl -L "https://repo1.maven.org/maven2/com/microsoft/sqlserver/mssql-jdbc/13.4.0.jre11/mssql-jdbc-13.4.0.jre11.jar" \
    -o /opt/nifi/drivers/mssql-jdbc-13.4.0.jre11.jar

# Oracle JDBC ojdbc11 (Java 11+ / Java 21 compatible)
RUN curl -L "https://repo1.maven.org/maven2/com/oracle/database/jdbc/ojdbc11/23.5.0.24.07/ojdbc11-23.5.0.24.07.jar" \
    -o /opt/nifi/drivers/ojdbc11-23.5.0.24.07.jar

# PostgreSQL JDBC 42.7.3 (Java 8+ compatible)
RUN curl -L "https://repo1.maven.org/maven2/org/postgresql/postgresql/42.7.3/postgresql-42.7.3.jar" \
    -o /opt/nifi/drivers/postgresql-42.7.3.jar

# Start Apache NiFi
CMD ["nifi.sh", "run"]
