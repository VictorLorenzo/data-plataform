from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.utils.task_group import TaskGroup
from airflow.operators.python import PythonOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from datetime import datetime
from modules.utils import list_files

# create Task Group for each step_silver_to_gold
def create_steps_task_group(gold_settings_file):
    group_id = gold_settings_file.split('/')[-1].split('.')[0] # each settings file will generate an id to task group
    
    with TaskGroup(group_id=group_id) as tg:
        step_silver_to_gold = SparkSubmitOperator(
            task_id=f'step_silver_to_gold',
            application='/opt/airflow/spark/run_gold_settings_job.py',
            application_args=[gold_settings_file, 'step_silver_to_gold'], # the script will execute step_silver_to_gold
            conn_id='spark_default',
            name=f'job_silver_to_gold_{group_id}',
            driver_memory='1G',
            executor_memory='2G',
            total_executor_cores=2,
            properties_file='/opt/airflow/config/spark-defaults.conf'
        )

        step_silver_to_gold

    return tg

def create_dag(dag_id, schedule, default_args, gold_settings_files):
    # DAG definition
    with DAG(
        dag_id=dag_id,
        default_args=default_args,
        description='DAG for tables pipelines from datalake silver zone to datalake gold zone',
        schedule_interval=schedule,
        start_date=days_ago(1),
        tags=['datalake', 'gold'],
        catchup=False
    ) as dag:

        start = PythonOperator(
            task_id='start',
            python_callable=lambda: print(f'Starting DAG at: {datetime.now()}')
        )

        end = PythonOperator(
            task_id='end',
            python_callable=lambda: print(f'Finishing DAG at: {datetime.now()}')
        )

        task_groups = [create_steps_task_group(file) for file in gold_settings_files]
            
        start >> task_groups >> end
    
    return dag


dag_id = 'dag_igdb_silver_to_gold'
# schedule interval for the DAG
schedule = '0 */1 * * *'
# DAG default params
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
}

params_directory = '/opt/airflow/spark/params/process/gold/igdb'
gold_settings_files = list_files(params_directory)

globals()[dag_id] = create_dag(dag_id, schedule, default_args, gold_settings_files)