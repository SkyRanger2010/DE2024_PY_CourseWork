from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.operators.empty import EmptyOperator

from airflow.providers.mysql.hooks.mysql import MySqlHook

from scripts.helpers.airflow_common import get_connection_uri

# Константы
ANALYTICAL_MARTS = ["user_activity", "average_check", "product_rating", "user_loyalty_points"]
JARS = "/opt/airflow/spark/jars/mysql-connector-java-8.3.0.jar"
PYSPARK_SCRIPT_PATH = '/opt/airflow/scripts/pyspark_scripts/populate_analytical_marts.py'

# Параметры по умолчанию для DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(year=2025,month=1,day=9),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 0,
    'retry_delay': timedelta(minutes=5),
    'catchup': False
}

with DAG(
    'create_analytical_marts',
    default_args=default_args,
    description='Создание витрин данных в MySQL через Spark',
    schedule_interval=timedelta(minutes=10),
    concurrency=1,
    max_active_runs=1
) as dag:
    # Креды и драйверы
    src_tgt_url = get_connection_uri(MySqlHook.get_connection('coursework_de_mysql'))
    src_tgt_driver = 'com.mysql.cj.jdbc.Driver'

    # EmptyOperator для начала и конца DAG
    start = EmptyOperator(task_id='start')
    finish = EmptyOperator(task_id='finish')

    for mart in ANALYTICAL_MARTS:
        spark_submit_task = SparkSubmitOperator(
            task_id=f'create_mart_{mart}',
            application=PYSPARK_SCRIPT_PATH,
            conn_id='coursework_de_spark',
            application_args=[
                '--src_tgt_url', src_tgt_url,
                '--src_tgt_driver', src_tgt_driver,
                '--target_mart', mart
            ],
            conf={
                "spark.driver.memory": "1g",
                "spark.worker.memory": "1g",
                "spark.worker.cores": 1,
                "spark.executor.memory": "1g"
            },
            jars=JARS
        )

        start >> spark_submit_task >> finish