import argparse
from pyspark.sql import SparkSession
from pyspark.sql import functions as F


def create_user_activity_view(src_tgt_url: str, src_tgt_driver: str):
    """
    Создает/перезаписывает витрину активности пользователей (кол-во заказов, общая сумма, кол-во отзывов.

    Args:
        src_tgt_url (str): URL для подключения к источнику и приемнику.
        src_tgt_driver (str): Драйвер для подключения к СУБД.
        tgt_mart_name (str): Имя целевой витрины данных.
    """
    # Создание Spark сессии
    spark = (
        SparkSession.builder
        .appName(f"Create_mart_user_activity")
        .getOrCreate()
    )

    # Чтение данных из "STG" слоя
    users_df = ( 
        spark.read
        .format("jdbc")
        .option("url", src_tgt_url)
        .option("driver", src_tgt_driver)
        .option("dbtable", "users") \
        .load()
    )

    orders_df = (
        spark.read
        .format("jdbc")
        .option("url", src_tgt_url)
        .option("driver", src_tgt_driver)
        .option("dbtable", "orders")
        .load()
    )

    reviews_df = (
        spark.read
        .format("jdbc")
        .option("url", src_tgt_url)
        .option("driver", src_tgt_driver)
        .option("dbtable", "reviews")
        .load()
    )

    # Создание витрины активности пользователей с разбивкой по статусу заказа
    user_activity_orders_df = (
        orders_df.join(users_df, "user_id")
        .groupBy("user_id", "first_name", "last_name")
        .agg({"order_id": "count", "total_amount": "sum"})
        .withColumnRenamed("count(order_id)", "order_count")
        .withColumnRenamed("sum(total_amount)", "total_spent")
    )

    user_activity_df = (
        user_activity_orders_df.join(reviews_df, "user_id")
        .groupBy("user_id", "first_name", "last_name", "order_count", "total_spent")
        .agg({"review_id": "count", "rating": "mean"})
        .withColumnRenamed("count(review_id)", "total_reviews")
        .withColumnRenamed("avg(rating)", "average_rating")
        .withColumn("average_rating", F.round("average_rating",2))
    )


    # Overwrite в приемнике
    (
        user_activity_df.write
        .format("jdbc")
        .option("url", src_tgt_url)
        .option("driver", src_tgt_driver)
        .option("dbtable", f"mart_user_activity")
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

    create_user_activity_view(args.src_tgt_url, args.src_tgt_driver)

if __name__ == "__main__":
    main()