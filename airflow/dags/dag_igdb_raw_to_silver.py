from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.utils.task_group import TaskGroup
from airflow.operators.python import PythonOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from datetime import datetime
from modules.utils import list_files

# create Task Group for each step_raw_to_bronze and step_bronze_to_silver
def create_steps_task_group(silver_settings_file):
    group_id = silver_settings_file.split('/')[-1].split('.')[0] # each settings file will generate an id to task group
    
    with TaskGroup(group_id=group_id) as tg:
        step_raw_to_bronze = SparkSubmitOperator(
            task_id=f'step_raw_to_bronze',
            application='/opt/airflow/spark/run_silver_settings_job.py',
            application_args=[silver_settings_file, 'step_raw_to_bronze'], # the script will execute step_raw_to_bronze
            conn_id='spark_default',
            name=f'job_raw_to_bronze_{group_id}',
            driver_memory='1G',
            executor_memory='2G',
            total_executor_cores=2,
            properties_file='/opt/airflow/config/spark-defaults.conf'
        )

        step_bronze_to_silver = SparkSubmitOperator(
            task_id=f'step_bronze_to_silver',
            application='/opt/airflow/spark/run_silver_settings_job.py',
            application_args=[silver_settings_file, 'step_bronze_to_silver'], # the script will execute step_bronze_to_silver
            conn_id='spark_default',
            name=f'job_bronze_to_silver_{group_id}',
            driver_memory='1G',
            executor_memory='2G',
            total_executor_cores=2,
            properties_file='/opt/airflow/config/spark-defaults.conf'
        )

        step_raw_to_bronze >> step_bronze_to_silver

    return tg

def create_dag(dag_id, schedule, default_args, silver_settings_files):
    # DAG definition
    with DAG(
        dag_id=dag_id,
        default_args=default_args,
        description='DAG for tables pipelines from datalake landing zone to datalake silver zone',
        schedule_interval=schedule,
        start_date=days_ago(1),
        tags=['datalake', 'silver'],
        catchup=False,
        max_active_runs=1
    ) as dag:

        start = PythonOperator(
            task_id='start',
            python_callable=lambda: print(f'Starting DAG at: {datetime.now()}')
        )

        end = PythonOperator(
            task_id='end',
            python_callable=lambda: print(f'Finishing DAG at: {datetime.now()}')
        )

        task_groups = [create_steps_task_group(file) for file in silver_settings_files]
            
        start >> task_groups >> end
    
    return dag


dag_id = 'dag_igdb_raw_to_silver'
# schedule interval for the DAG
schedule = '@hourly'
# DAG default params
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
}

params_directory = '/opt/airflow/spark/params/process/silver/igdb'
silver_settings_files = list_files(params_directory)

globals()[dag_id] = create_dag(dag_id, schedule, default_args, silver_settings_files)