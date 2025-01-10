import argparse

from pyspark.sql import SparkSession
import logging

def replicate_table(source_url: str, source_driver: str, target_url: str, target_driver: str, table: str):
    """
    Реплицирует таблицу из источника в приемник, учитывая возможные внешние ключи.

    Args:
        source_url (str): URL для подключения к источнику.
        source_driver (str): Драйвер для подключения к источнику.
        target_url (str): URL для подключения к приемнику.
        target_driver (str): Драйвер для подключения к приемнику.
        table (str): Имя таблицы для репликации.
    """
    # Настройка логирования
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    logger.info(f"Начинается репликация таблицы '{table}' из источника в приемник.")

    try:
        # Создание Spark сессии
        logger.info("Создание Spark сессии.")
        spark = (
            SparkSession.builder
            .appName(f"replicate_table_{table}")
            .getOrCreate()
        )

        # Чтение данных из источника
        logger.info(f"Чтение данных из таблицы '{table}' из источника.")
        source_df = (
            spark.read
            .format("jdbc")
            .option("driver", source_driver)
            .option("url", source_url)
            .option("dbtable", table)
            .load()
        )



        # Запись данных в приемник с overwrite
        logger.info(f"Запись данных в таблицу '{table}' в приемнике.")
        (
            source_df.write
            .format("jdbc")
            .option("driver", target_driver)
            .option("url", target_url)
            .option("dbtable", table)
            .mode("overwrite")
            .save()
        )


        logger.info(f"Репликация таблицы '{table}' завершена успешно.")

    except Exception as e:
        logger.error(f"Ошибка при репликации таблицы '{table}': {e}", exc_info=True)
        raise

    finally:
        # Остановка Spark сессии
        logger.info("Остановка Spark сессии.")
        spark.stop()



def main():
    """
    Точка входа. Парсит аргументы и запускает создание/перезапись соответствующей таблицы.

     Args:
        --source_url (str): URL для подключения к источнику.
        --source_driver (str): Драйвер для подключения к источнику.
        --target_url (str): URL для подключения к приемнику.
        --target_driver (str): Драйвер для подключения к приемнику.
        --table (str): Имя таблицы на источнике.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--source_url", type=str, required=True)
    parser.add_argument("--source_driver", type=str, required=True)
    parser.add_argument("--target_url", type=str, required=True)
    parser.add_argument("--target_driver", type=str, required=True)
    parser.add_argument("--table", type=str, required=True)
    
    args = parser.parse_args()
    replicate_table(args.source_url, args.source_driver, args.target_url, args.target_driver, args.table)


if __name__ == "__main__":
    main()