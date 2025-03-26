# Description
This is a fully open-source data platform designed for efficient data ingestion, processing, storage, and analytics. It integrates multiple services to provide a seamless data pipeline, from collection to visualization.
## Initial Setup

### All services must be started in the order below:

1. SFTP – Secure file transfer for ingesting raw data.
2. NiFi – Automates data movement, ingestion and transformation.
3. MinIO – Object storage for scalable data management.
4. Spark – Distributed data processing and analytics engine.
5. Hive – Data warehousing and querying for structured datasets.
6. DBeaver – Database management and visualization tool.
7. Airflow – Workflow orchestration for scheduling and monitoring data pipelines.

### Network
To the data plataform comunicate with each other, it need a network

```sh
  make network-create NETWORK=data-plataform
```

