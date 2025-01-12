import argparse
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
import logging


# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def get_spark_session(app_name: str, jars: str) -> SparkSession:
    """
    Создаёт и возвращает SparkSession.
    """
    return SparkSession.builder \
        .appName(app_name) \
        .config("spark.jars", jars) \
        .getOrCreate()


def fetch_unprocessed_changes(spark: SparkSession, source_url: str, source_driver: str):
    """
    Получает необработанные изменения из таблицы audit_log.
    """
    logger.info("Чтение необработанных изменений из audit_log.")
    audit_log_query = """
        SELECT change_id, table_name, operation, old_data, new_data
        FROM audit_log
        WHERE is_processed = FALSE
        ORDER BY change_id
    """
    return spark.read.format("jdbc") \
        .option("url", source_url) \
        .option("driver", source_driver) \
        .option("query", audit_log_query) \
        .load()


def process_changes_batch(spark: SparkSession, changes_df, target_url: str, target_driver: str):
    """
    Обрабатывает изменения, предварительно группируя их по операциям и таблицам.
    """
    logger.info("Начало групповой обработки изменений через Spark JDBC.")

    grouped_changes = changes_df.groupBy("table_name", "operation") \
                                .agg(F.collect_list(F.struct("old_data", "new_data")).alias("changes"))

    for row in grouped_changes.collect():
        table_name = row['table_name']
        operation = row['operation']
        changes = row['changes']

        logger.info(f"Обработка операции {operation} для таблицы {table_name} (количество изменений: {len(changes)})")

        if operation == 'INSERT':
            new_data = [change['new_data'] for change in changes]
            new_data_df = spark.read.json(spark.sparkContext.parallelize(new_data))

            # Чтение текущих данных из целевой таблицы
            existing_data_df = (
                spark.read
                .format("jdbc")
                .option("url", target_url)
                .option("driver", target_driver)
                .option("dbtable", table_name)
                .load()
            )

            # Убираем дубликаты: новые записи, которых нет в целевой таблице
            filtered_new_data_df = (
                new_data_df.join(existing_data_df, how="left_anti")
            # Предполагаем, что 'id' — уникальный ключ
            )

            # Пишем только новые записи
            filtered_new_data_df.write.format("jdbc") \
                .option("url", target_url) \
                .option("driver", target_driver) \
                .option("dbtable", table_name) \
                .mode("append") \
                .save()
        else:
            logger.warning(f"Неизвестная операция {operation} для таблицы {table_name}. Пропуск.")

    logger.info("Групповая обработка изменений завершена.")


def update_processed_status(spark: SparkSession, source_url: str, source_driver: str, max_change_id: int):
    """
    Вызывает функцию mark_changes_as_processed для обновления статуса записей в PostgreSQL.
    """
    logger.info(f"Обновление статуса изменений до ID {max_change_id} в PostgreSQL.")
    try:
        connection = spark._sc._gateway.jvm.java.sql.DriverManager.getConnection(source_url)
        cursor = connection.createStatement()

        function_call = f"SELECT mark_changes_as_processed({max_change_id});"
        cursor.execute(function_call)
        logger.info("Функция mark_changes_as_processed успешно вызвана.")
    except Exception as e:
        logger.error(f"Ошибка при вызове функции PostgreSQL: {e}", exc_info=True)
        raise
    finally:
        connection.close()




def main():
    parser = argparse.ArgumentParser(description="Incremental Replication with Spark")
    parser.add_argument('--source_url', required=True, help="JDBC URL для источника данных")
    parser.add_argument('--source_driver', required=True, help="JDBC драйвер для источника данных")
    parser.add_argument('--target_url', required=True, help="JDBC URL для целевой базы данных")
    parser.add_argument('--target_driver', required=True, help="JDBC драйвер для целевой базы данных")
    parser.add_argument('--jars', required=True, help="Список JAR файлов для Spark")

    args = parser.parse_args()

    # Вызов всех остальных функций с использованием аргументов
    spark = get_spark_session("Incremental Replication with Audit Log", args.jars)

    try:
        changes_df = fetch_unprocessed_changes(spark, args.source_url, args.source_driver)

        if changes_df.isEmpty():
            logger.info("Нет необработанных изменений. Завершение работы.")
            return

        process_changes_batch(spark, changes_df, args.target_url, args.target_driver)

        max_change_id = changes_df.agg({"change_id": "max"}).collect()[0][0]
        update_processed_status(spark, args.source_url, args.source_driver, max_change_id)

    except Exception as e:
        logger.error(f"Ошибка при выполнении: {e}", exc_info=True)
        raise

    finally:
        spark.stop()
        logger.info("Остановка Spark сессии.")

if __name__ == "__main__":
    main()
