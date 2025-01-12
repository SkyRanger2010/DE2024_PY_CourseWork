import argparse
from pyspark.sql import SparkSession
from pyspark.sql import functions as F


def create_average_check_view(src_tgt_url: str, src_tgt_driver: str):
    """
    Создает/перезаписывает витрину среднего чека с разбивкой по статусу заказа и статусу лояльности.

    Args:
        src_tgt_url (str): URL для подключения к источнику и приемнику.
        src_tgt_driver (str): Драйвер для подключения к СУБД.
    """
    # Создание Spark сессии
    spark = (
        SparkSession.builder
        .appName(f"Create_mart_average_check")
        .getOrCreate()
    )

    # Чтение данных из "STG" слоя
    orders_df = (
        spark.read
        .format("jdbc")
        .option("url", src_tgt_url)
        .option("driver", src_tgt_driver)
        .option("dbtable", "orders") \
        .load()
    )

    users_df = (
        spark.read
        .format("jdbc")
        .option("url", src_tgt_url)
        .option("driver", src_tgt_driver)
        .option("dbtable", "users") \
        .load()
    )

    # Создание витрины
    average_check_df = (
        orders_df.join(users_df, "user_id")
        .groupBy("status", "loyalty_status")
        .agg({"total_amount": "avg"})
        .withColumnRenamed("avg(total_amount)", "average_check")
        .withColumnRenamed("status", "order_status")
        .withColumn("average_check", F.round("average_check",2))
    )

    # Overwrite в приемнике
    (
        average_check_df.write
        .format("jdbc")
        .option("url", src_tgt_url)
        .option("driver", src_tgt_driver)
        .option("dbtable", f"mart_average_check")
        .mode("overwrite")
        .save()
    )

    # Остановка Spark сессии
    spark.stop()


def main():
    """
    Точка входа. Парсит аргументы и запускает создание/перезапись соответствующей витрины.

    Args:
        --src_tgt_url (str): URL для подключения к источнику и приемнику.
        --src_tgt_driver (str): Драйвер для подключения к СУБД.
        --target_mart (str): Имя целевой витрины данных. Возможные значения: 'user_activity', 'product_rating', 'average_check' , 'user_loyalty_points'.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--src_tgt_url', type=str, required=True)
    parser.add_argument("--src_tgt_driver", type=str, required=True)

    args = parser.parse_args()

    create_average_check_view(args.src_tgt_url, args.src_tgt_driver)

if __name__ == "__main__":
    main()