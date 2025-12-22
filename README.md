# Description

This is a fully open-source data platform designed for efficient data ingestion, processing, storage, and analytics. It integrates multiple services to provide a seamless data pipeline, from collection to visualization.

![alt text](./assets/data_platform.png)

## Initial Setup

### All services must be started in the order below:

#### 1. SFTP – Secure file transfer for ingesting raw data.

* Run the comamnd at the terminal to up the containner
  ```sh
  cd sftp && make up
  ```

#### 2. MinIO – Object storage for scalable data management.

* Run the comamnd at the terminal to up the containner

  ```sh
  cd ../minio && make up
  ```
* Access the url http://localhost:9001/login
* Minio credentials

  ```
  user: accesskey
  password: secretkey
  ```
* At the minio UI, access the "Access Key" menu
  ![alt text](./assets/MInioUI.png)
* Create an Access Key with this credentials

  ```
  accessKey: nifi,
  secretKey: nifipass,
  ```

  ```
  Access Key: trino
  Secret Key: trinopass
  ```

#### 3. NiFi – Automates data movement, ingestion and transformation.

* Run the comamnd at the terminal to up the containner

  ```sh
  cd ../nifi && make up
  ```
* Access the url http://localhost:8443/nifi/
* At the nifi UI, upload your nifi template `./nifi/template/*.xml`
  ![alt text](./assets/nifiTemplateUpdate.png)
* Drag and drop to chose the uploaded template
  ![alt text](./assets/SFTP_INGESTION.png)
* Access the template and set the variables of the platform
  ![alt text](./assets/Variables.png)
  ![alt text](./assets/Variables_set.png)
* Change the password to LIST_SFTP AND FETCH_SFTP
  `pass: Sftp_Userpass12!@`
  ![alt text](./assets/Password.png)
* Run the pipeline
  ![alt text](./assets/Start_pipeline_nifi.png)
* Watch your files in Minio
  ![alt text](./assets/minio_landing.png)

#### 4. Spark – Distributed data processing and analytics engine.

* Run the comamnd at the terminal to up the containner

  ```sh
  cd ../spark && make up
  ```
* Access http://localhost:8082/ to watch your spark workers
  ![alt text](./assets/spark_workers.png)

#### 5. Hive – Data warehousing and querying for structured datasets.

* Run the comamnd at the terminal to up the containner
  ```sh
  cd ../hive && make up
  ```

#### 6. Airflow – Workflow orchestration platform for authoring, scheduling, and monitoring data pipelines.

* Run the comamnd at the terminal to up the containner

  ```sh
  cd ../airflow && make up
  ```
* Access the url http://localhost:8080/login/

  ```
  user: airflow
  pass: airflow
  ```
* Run your pipeline
  ![alt text](./assets/airflow_pipeline.png)
  ![alt text](./assets/airflow_pipeline_detailed.png)

Important for execute Spark Jobs.

Configure the Spark connection: In Airflow, go to Admin -> Connections and add a new connection. Set the Conn Id as spark_default, the Conn Type as Spark, and the Host as the address of your Spark master.
```
Connection Id: spark_default
Connection Type: Spark
Host: spark://spark-master:7077
```

#### 7. Jupyter – Interactive computing environment for creating and sharing documents with live code, visualizations, and narrative text.

* Run the comamnd at the terminal to up the containner

  ```sh
  cd ../jupyter && make up
  ```
* Access the url http://localhost:8888
* At the `/work/nba_analisy.ipynb` you can see the table at bronze layer with their respective schema

#### 8. Trino – Distributed SQL query engine for fast, interactive analytics across multiple data sources.

#### 9. Kyuubi – Distributed multi-tenant JDBC server for Apache Spark.

#### 10. Kafka – Distributed event streaming platform for building real-time data pipelines and applications.

#### 11. Debezium – Distributed platform for change data capture (CDC), streaming real-time changes from databases to other systems.

#### 12. DBeaver – Database management and visualization tool.

#### 13. Metabase – Open-source business intelligence tool for exploring, visualizing, and sharing data insights.

### More TODO
In the future i want to implement some ideas to automate some proccess:

* Use Unity Catalog for data governance and data quality, also as catalog

* Implement a more generic way to upload your ETL pipeline using json with jinja2

* Add more data graphics

* Add more data integration such as with steam API

* Implement CI/CD proccess to upload your pipeline without commiting any new code

* Add more new feature from databricks

* Add Compatibility with AWS and Databircks

* Create clusterized environment using Kubernetes

### Network

To the data plataform comunicate with each other, it need a network

```sh
make network-create NETWORK=data-plataform
```
