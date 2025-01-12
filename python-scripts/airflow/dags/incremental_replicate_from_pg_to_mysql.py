from airflow import DAG
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.operators.empty import EmptyOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.mysql.hooks.mysql import MySqlHook
from datetime import datetime, timedelta
from scripts.helpers.airflow_common import get_connection_uri

# Константы
JARS = "/opt/airflow/spark/jars/postgresql-42.2.18.jar,/opt/airflow/spark/jars/mysql-connector-java-8.3.0.jar"
PYSPARK_REPLICATION_SCRIPT_PATH = f'/opt/airflow/scripts/pyspark_scripts/incremental_replicate_by_spark.py'


# Параметры по умолчанию для DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(year=2025, month=1, day=9),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 0,
    'retry_delay': timedelta(minutes=3),
    'catchup': False,
    'concurrency': 1
}

with DAG(
        'incremental_replicate_with_audit_log',
        default_args=default_args,
        description='Инкрементальная репликация данных через Spark и audit_log',
        schedule_interval=timedelta(minutes=10),
        concurrency=4,
        max_active_runs=1
) as dag:
    # Креды и драйверы
    source_url = get_connection_uri(PostgresHook.get_connection('coursework_de_postgresql'))
    source_driver = 'org.postgresql.Driver'
    target_url = get_connection_uri(MySqlHook.get_connection('coursework_de_mysql'))
    target_driver = 'com.mysql.cj.jdbc.Driver'

    start = EmptyOperator(task_id='start')
    finish = EmptyOperator(task_id='finish')

    replicate_task = SparkSubmitOperator(
        task_id='replicate_changes_with_spark',
        application=PYSPARK_REPLICATION_SCRIPT_PATH,
        conn_id='coursework_de_spark',
        application_args=[
            '--source_url', source_url,
            '--source_driver', source_driver,
            '--target_url', target_url,
            '--target_driver', target_driver,
            '--jars', JARS
        ],
        conf={
            "spark.driver.memory": "1g",
            "spark.worker.memory": "1g",
            "spark.worker.cores": 1,
            "spark.executor.memory": "1g"
        },
        jars=JARS
    )

    start >> replicate_task >> finish
