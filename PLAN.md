# Unity Catalog OSS Implementation Plan

## Overview
Replace Hive Metastore with Unity Catalog OSS as the central metadata catalog for the data platform. This involves:
1. Adding a new `unity-catalog/` service
2. Upgrading Spark 3.4.1 → 3.5.3 and Delta Lake 2.4.0 → 3.2.1
3. Reconfiguring Trino, Kyuubi, Airflow to use Unity Catalog
4. Deprecating the Hive Metastore service

## Architecture Changes

```
BEFORE:
  Spark/Trino/Kyuubi → Hive Metastore (thrift:9083) → PostgreSQL → MinIO

AFTER:
  Spark → Unity Catalog (REST :8080) → PostgreSQL-UC → MinIO
  Trino → Unity Catalog (Iceberg REST :8080) → MinIO
  Kyuubi → (via Spark) Unity Catalog → MinIO
```

---

## Step 1: Create `unity-catalog/` Service Directory

### New files:
- `unity-catalog/docker-compose.yml`
- `unity-catalog/config/server.properties`
- `unity-catalog/config/hibernate.properties`
- `unity-catalog/Makefile`
- `unity-catalog/scripts/init-uc.sh` (register medallion tables)

### `unity-catalog/docker-compose.yml`:
```yaml
version: "3"

services:
  postgres-uc:
    hostname: postgres-uc
    container_name: postgres-uc
    image: postgres:13
    ports:
      - "5434:5432"
    environment:
      POSTGRES_USER: uc_admin
      POSTGRES_PASSWORD: uc_admin
      POSTGRES_DB: unity_catalog_db
    volumes:
      - uc_catalog:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U uc_admin -d unity_catalog_db"]
      interval: 5s
      timeout: 10s
      retries: 10

  unity-catalog-server:
    hostname: unity-catalog-server
    container_name: unity-catalog-server
    image: unitycatalog/unitycatalog:latest
    ports:
      - "8087:8080"     # UC REST API (8080 taken by Airflow)
    volumes:
      - ./config/server.properties:/opt/unitycatalog/etc/conf/server.properties
      - ./config/hibernate.properties:/opt/unitycatalog/etc/conf/hibernate.properties
      - uc_data:/opt/unitycatalog/etc/data
    depends_on:
      postgres-uc:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "sh", "-c", "curl --fail http://localhost:8080/api/2.1/unity-catalog/catalogs || exit 1"]
      interval: 15s
      timeout: 10s
      retries: 5

  unity-catalog-ui:
    hostname: unity-catalog-ui
    container_name: unity-catalog-ui
    image: unitycatalog/unitycatalog-ui:latest
    ports:
      - "3001:3000"     # UC UI (3000 taken by Metabase)
    environment:
      UC_API_URL: http://unity-catalog-server:8080
    depends_on:
      - unity-catalog-server

  uc-init:
    hostname: uc-init
    container_name: uc-init
    image: curlimages/curl:latest
    depends_on:
      unity-catalog-server:
        condition: service_healthy
    volumes:
      - ./scripts/init-uc.sh:/init-uc.sh
    entrypoint: ["sh", "/init-uc.sh"]

volumes:
  uc_catalog:
    driver: local
  uc_data:
    driver: local

networks:
  default:
    name: data-plataform
    external: true
```

### `unity-catalog/config/server.properties`:
```properties
server.env=dev

## S3/MinIO bucket configuration (for credential vending awareness)
s3.bucketPath.0=s3://datalake-landing
s3.accessKey.0=accesskey
s3.secretKey.0=secretkey
s3.sessionToken.0=

s3.bucketPath.1=s3://datalake-bronze
s3.accessKey.1=accesskey
s3.secretKey.1=secretkey
s3.sessionToken.1=

s3.bucketPath.2=s3://datalake-silver
s3.accessKey.2=accesskey
s3.secretKey.2=secretkey
s3.sessionToken.2=

s3.bucketPath.3=s3://datalake-gold
s3.accessKey.3=accesskey
s3.secretKey.3=secretkey
s3.sessionToken.3=
```

### `unity-catalog/config/hibernate.properties`:
```properties
hibernate.connection.driver_class=org.postgresql.Driver
hibernate.connection.url=jdbc:postgresql://postgres-uc:5432/unity_catalog_db
hibernate.connection.user=uc_admin
hibernate.connection.password=uc_admin
hibernate.hbm2ddl.auto=update
hibernate.show_sql=false
```

### `unity-catalog/scripts/init-uc.sh`:
Creates the medallion catalogs/schemas matching the platform's data zones:
```bash
#!/bin/sh
set -e
UC_API="http://unity-catalog-server:8080/api/2.1/unity-catalog"

# Wait for UC server
until curl -s "$UC_API/catalogs" > /dev/null 2>&1; do
  echo "Waiting for Unity Catalog server..."
  sleep 5
done

echo "=== Unity Catalog Init ==="

# Create catalogs for each medallion zone
for catalog in landing bronze silver gold; do
  echo "Creating catalog: $catalog"
  curl -s -X POST "$UC_API/catalogs" \
    -H "Content-Type: application/json" \
    -d "{\"name\": \"$catalog\", \"comment\": \"Medallion $catalog zone\"}" || true
done

# Create default schemas
for catalog in landing bronze silver gold; do
  echo "Creating schema: $catalog.games_analytics"
  curl -s -X POST "$UC_API/schemas" \
    -H "Content-Type: application/json" \
    -d "{\"name\": \"games_analytics\", \"catalog_name\": \"$catalog\", \"comment\": \"IGDB Games Analytics\"}" || true
done

echo "=== Unity Catalog Init Complete ==="
```

### `unity-catalog/Makefile`:
Standard Makefile following project pattern (same as other services).

---

## Step 2: Upgrade Spark from 3.4.1 → 3.5.3

### `spark/docker/spark/Dockerfile` changes:
```dockerfile
FROM bitnami/spark:3.5.3
USER root
ENV LIVY_HOME /opt/bitnami/livy

RUN apt-get update && apt install curl unzip -y

COPY ./start.sh ./start.sh
RUN chmod +x start.sh

COPY ./requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Download upgraded JARs for Delta 3.2.1 + AWS + Avro + UC connector
RUN curl "https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.367/aws-java-sdk-bundle-1.12.367.jar" \
      -o /opt/bitnami/spark/jars/aws-java-sdk-bundle-1.12.367.jar \
    && curl "https://repo1.maven.org/maven2/io/delta/delta-spark_2.12/3.2.1/delta-spark_2.12-3.2.1.jar" \
      -o /opt/bitnami/spark/jars/delta-spark_2.12-3.2.1.jar \
    && curl "https://repo1.maven.org/maven2/io/delta/delta-storage/3.2.1/delta-storage-3.2.1.jar" \
      -o /opt/bitnami/spark/jars/delta-storage-3.2.1.jar \
    && curl "https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.6/hadoop-aws-3.3.6.jar" \
      -o /opt/bitnami/spark/jars/hadoop-aws-3.3.6.jar \
    && curl "https://repo1.maven.org/maven2/org/apache/spark/spark-avro_2.12/3.5.3/spark-avro_2.12-3.5.3.jar" \
      -o /opt/bitnami/spark/jars/spark-avro_2.12-3.5.3.jar \
    && curl "https://repo1.maven.org/maven2/io/unitycatalog/unitycatalog-spark_2.12/0.2.0/unitycatalog-spark_2.12-0.2.0.jar" \
      -o /opt/bitnami/spark/jars/unitycatalog-spark_2.12-0.2.0.jar

# Install Livy 0.8.0
WORKDIR /opt/bitnami/
RUN curl "https://dlcdn.apache.org/incubator/livy/0.8.0-incubating/apache-livy-0.8.0-incubating_2.12-bin.zip" -O \
    && unzip "apache-livy-0.8.0-incubating_2.12-bin" \
    && rm -rf "apache-livy-0.8.0-incubating_2.12-bin.zip" \
    && mv "apache-livy-0.8.0-incubating_2.12-bin" $LIVY_HOME \
    && mkdir -p $LIVY_HOME/logs \
    && chown -R 1001:1001 $LIVY_HOME

WORKDIR /opt/bitnami/spark/
```

**Note**: Base image changes from `bitnamilegacy/spark:3.4.1` to `bitnami/spark:3.5.3`. Livy upgraded from `2.11-bin` to `2.12-bin` for Scala 2.12 compatibility.

### `spark/requirements.txt`:
```
delta-spark==3.2.1
```

### `spark/spark-config/spark-defaults.conf`:
```properties
# Delta Lake 3.2.1 + Unity Catalog
spark.jars = jars/delta-spark_2.12-3.2.1.jar,jars/delta-storage-3.2.1.jar,jars/hadoop-aws-3.3.6.jar,jars/aws-java-sdk-bundle-1.12.367.jar,jars/unitycatalog-spark_2.12-0.2.0.jar
spark.sql.extensions = io.delta.sql.DeltaSparkSessionExtension

# Unity Catalog as the catalog implementation
spark.sql.catalog.unity = io.unitycatalog.spark.UCSingleCatalog
spark.sql.catalog.unity.uri = http://unity-catalog-server:8080
spark.sql.catalog.unity.token =
spark.sql.defaultCatalog = unity

# S3/MinIO access (engines handle storage directly)
spark.hadoop.fs.s3a.impl = org.apache.hadoop.fs.s3a.S3AFileSystem
spark.hadoop.fs.s3a.endpoint = http://minio:9000
spark.hadoop.fs.s3a.access.key = accesskey
spark.hadoop.fs.s3a.secret.key = secretkey
spark.hadoop.fs.s3a.path.style.access = true
spark.hadoop.fs.s3a.connection.ssl.enabled = false

spark.sql.warehouse.dir = s3a://datalake-gold/warehouse
```

### `spark/spark-config/hive-site.xml`:
**Remove this file** — no longer needed since Hive Metastore is being replaced. Remove the volume mount from docker-compose.yml.

### `spark/docker-compose.yml` changes:
Remove the `hive-site.xml` volume mount from spark-master:
```yaml
    volumes:
      - ./spark-apps:/opt/spark-apps/
      - ./spark-config/spark-defaults.conf:/opt/bitnami/spark/conf/spark-defaults.conf
      # REMOVED: ./spark-config/hive-site.xml (no longer needed with UC)
      - ./conf/:/opt/bitnami/livy/conf/
      - ./target/:/target_livy/
      - ./data/:/data_livy/
```

---

## Step 3: Update Trino to Use Unity Catalog via Iceberg REST

### `trino/config/coordinator/catalog/deltalake.properties`:
**Rename to** `trino/config/coordinator/catalog/unity.properties`:
```properties
connector.name=iceberg
iceberg.catalog.type=rest
iceberg.rest-catalog.uri=http://unity-catalog-server:8080/api/2.1/unity-catalog/iceberg
iceberg.rest-catalog.security=OAUTH2
iceberg.rest-catalog.oauth2.token=not_used
fs.native-s3.enabled=true
s3.endpoint=http://minio:9000
s3.path-style-access=true
s3.aws-access-key=trino
s3.aws-secret-key=trinopass
s3.region=us-east-1
```

### `trino/config/worker/catalog/deltalake.properties`:
**Rename to** `trino/config/worker/catalog/unity.properties`:
Same content as coordinator catalog.

**Important Note**: Trino's Iceberg REST connector with UC OSS works for tables that have UniForm (Iceberg compatibility) enabled. For pure Delta tables, we also keep a `delta_lake` catalog pointing to the same S3 location as a fallback, but using UC's metadata registration for discovery.

---

## Step 4: Update Kyuubi

### `kyuubi/kyuubi-config/kyuubi-defaults.conf`:
```properties
# Unity Catalog instead of Hive Metastore
spark.sql.catalog.unity = io.unitycatalog.spark.UCSingleCatalog
spark.sql.catalog.unity.uri = http://unity-catalog-server:8080
spark.sql.catalog.unity.token =
spark.sql.defaultCatalog = unity

spark.master=spark://spark-master:7077
spark.executor.cores=4
spark.cores.max=4
spark.executor.memory=8g
spark.sql.adaptive.enabled=true
spark.sql.extensions = io.delta.sql.DeltaSparkSessionExtension

# Updated JARs for Delta 3.2.1 + UC connector
spark.jars=/opt/kyuubi/jars/delta-spark_2.12-3.2.1.jar,/opt/kyuubi/jars/hadoop-aws-3.3.2.jar,/opt/kyuubi/jars/delta-storage-3.2.1.jar,/opt/kyuubi/jars/aws-java-sdk-1.12.137.jar,/opt/kyuubi/jars/s3-2.18.41.jar,/opt/kyuubi/jars/aws-java-sdk-bundle-1.11.1026.jar,/opt/kyuubi/jars/unitycatalog-spark_2.12-0.2.0.jar

# S3/MinIO
spark.hadoop.fs.defaultFS = s3a://datalake-gold
spark.hadoop.fs.s3a.impl = org.apache.hadoop.fs.s3a.S3AFileSystem
spark.hadoop.fs.s3a.connection.ssl.enabled = false
spark.hadoop.fs.s3a.aws.credentials.provider = org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider
spark.hadoop.fs.s3a.access.key = accesskey
spark.hadoop.fs.s3a.secret.key = secretkey
spark.hadoop.fs.s3a.endpoint = http://minio:9000
spark.hadoop.fs.s3a.path.style.access = true

kyuubi.session.engine.initialize.timeout=2400000
```

### Kyuubi Dockerfile:
Will need to download UC connector JAR and updated Delta JARs.

---

## Step 5: Update Airflow

### `airflow/config/spark-defaults.conf`:
```properties
# Unity Catalog
spark.sql.catalog.unity=io.unitycatalog.spark.UCSingleCatalog
spark.sql.catalog.unity.uri=http://unity-catalog-server:8080
spark.sql.catalog.unity.token=
spark.sql.defaultCatalog=unity

spark.jars.packages=io.delta:delta-spark_2.12:3.2.1,org.apache.hadoop:hadoop-aws:3.3.4,org.apache.spark:spark-avro_2.12:3.5.3,io.unitycatalog:unitycatalog-spark_2.12:0.2.0
spark.hadoop.fs.s3a.access.key=accesskey
spark.hadoop.fs.s3a.secret.key=secretkey
spark.hadoop.fs.s3a.path.style.access=true
spark.hadoop.fs.s3a.impl=org.apache.hadoop.fs.s3a.S3AFileSystem
spark.hadoop.fs.s3a.endpoint=http://minio:9000
spark.sql.extensions=io.delta.sql.DeltaSparkSessionExtension
spark.sql.warehouse.dir=s3a://datalake-gold/warehouse
```

### `airflow/requirements.txt`:
Update `pyspark==3.4.1` → `pyspark==3.5.3`

---

## Step 6: Deprecate Hive Metastore

- The `hive/` directory remains in the repo but is no longer required in the startup order
- Add a note in `hive/README.md` marking it as deprecated (replaced by Unity Catalog)
- Remove references to `hive-metastore:9083` from all configs

---

## Step 7: Update MinIO

### `minio/docker-compose.yml`:
Add a `datalake-uc` bucket for Unity Catalog managed tables:
```bash
/usr/bin/mc mb myminio/datalake-uc;
/usr/bin/mc anonymous set public myminio/datalake-uc;
```

---

## Step 8: Update README

Update startup order:
1. Create network
2. Start MinIO
3. **Start Unity Catalog** (NEW — replaces Hive)
4. Start Spark
5. Start Airflow
6. Start Trino
7. Optional: Kyuubi, Jupyter, Metabase, DBeaver

---

## Port Mapping Summary

| Service | Internal Port | External Port | Notes |
|---------|:---:|:---:|---|
| UC REST API | 8080 | **8087** | 8080 taken by Airflow |
| UC UI | 3000 | **3001** | 3000 taken by Metabase |
| UC PostgreSQL | 5432 | **5434** | 5432 taken by Hive PG |
