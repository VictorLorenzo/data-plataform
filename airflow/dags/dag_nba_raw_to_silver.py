from airflow import DAG
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.utils.dates import days_ago
from datetime import datetime, timedelta
from airflow.operators.dummy_operator import DummyOperator

default_args = {
    'owner': 'spark',
    'retries': 0,
}

with DAG(
    dag_id="spark_submit_operator_nba_agg_delta",
    description='A simple DAG to demonstrate SparkSubmitOperator with nba dataset',
    default_args=default_args,
    start_date=datetime.now(),
    catchup=False, 
    schedule_interval=None,       
) as dag:

    start = DummyOperator(task_id="start", dag=dag)

    spark_task_submit_operator_nba = SparkSubmitOperator(
        task_id='spark_task_submit_operator_nba',
        application='/opt/airflow/spark/spark_job/nba_raw_to_silver_processor.py',  # Caminho para o arquivo do job Spark
        conn_id='spark_default',  # ID da conexão do Spark definida no Airflow
        name='spark_nba_job',  # Nome do job Spark
        driver_memory='1g',  # Memória do driver
        executor_memory='2g',  # Memória do executor
        executor_cores=2,  # Número de núcleos do executor
        properties_file='/opt/airflow/config/spark-defaults.conf',  # Caminho para o arquivo de configuração do Spark
    )

    end = DummyOperator(task_id="end", dag=dag)

start >> spark_task_submit_operator_nba >> end