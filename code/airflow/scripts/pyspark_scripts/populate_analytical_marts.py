import argparse
from pyspark.sql import SparkSession


def create_user_activity_view(src_tgt_url: str, src_tgt_driver: str, tgt_mart_name: str):
    """
    Создает/перезаписывает витрину активности пользователей с разбивкой по статусу заказа.

    Args:
        src_tgt_url (str): URL для подключения к источнику и приемнику.
        src_tgt_driver (str): Драйвер для подключения к СУБД.
        tgt_mart_name (str): Имя целевой витрины данных.
    """
    # Создание Spark сессии
    spark = (
        SparkSession.builder
        .appName(f"Create_mart_{tgt_mart_name}")
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

    # Создание витрины активности пользователей с разбивкой по статусу заказа
    user_activity_df = (
        orders_df.join(users_df, "user_id")
        .groupBy("user_id", "first_name", "last_name", "status")
        .agg({"order_id": "count", "total_amount": "sum"})
        .withColumnRenamed("count(order_id)", "order_count")
        .withColumnRenamed("sum(total_amount)", "total_spent")
    )

    # Overwrite в приемнике
    (
        user_activity_df.write
        .format("jdbc")
        .option("url", src_tgt_url)
        .option("driver", src_tgt_driver)
        .option("dbtable", f"mart_{tgt_mart_name}")
        .mode("overwrite")
        .save()
    )
    
    # Остановка Spark сессии
    spark.stop()


def create_product_rating_view(src_tgt_url: str, src_tgt_driver: str, tgt_mart_name: str):
    """
    Создает/перезаписывает витрину продаж продуктов с разбивкой по статусу заказа.
    
    Args:
        src_tgt_url (str): URL для подключения к источнику и приемнику.
        src_tgt_driver (str): Драйвер для подключения к СУБД.
        tgt_mart_name (str): Имя целевой витрины данных.
    """
    # Создание Spark сессии
    spark = (
        SparkSession.builder
        .appName(f"Create_mart_{tgt_mart_name}")
        .getOrCreate()
    )

   # Чтение данных из "STG" слоя
    products_df = ( 
        spark.read
        .format("jdbc")
        .option("url", src_tgt_url)
        .option("driver", src_tgt_driver)
        .option("dbtable", "products") \
        .load()
    )

    reviews_df = (
        spark.read
        .format("jdbc")
        .option("url", src_tgt_url)
        .option("driver", src_tgt_driver)
        .option("dbtable", "reviews") \
        .load()
    )

    # Создание витрины продаж продуктов с разбивкой по статусу заказа
    product_rating_df = (
        products_df.join(reviews_df, "product_id")
        .groupBy("product_id", "name")
        .agg({"rating": "avg"})
        .withColumnRenamed("avg(rating)", "rating")
        .orderBy(desc("rating"))
    )

    # Overwrite в приемнике
    (
        product_rating_df.write
        .format("jdbc")
        .option("url", src_tgt_url)
        .option("driver", src_tgt_driver)
        .option("dbtable", f"mart_{tgt_mart_name}")
        .mode("overwrite")
        .save()
    )

    # Остановка Spark сессии
    spark.stop()


def create_user_loyalty_points_view(src_tgt_url: str, src_tgt_driver: str, tgt_mart_name: str):
    """
    Создает/перезаписывает витрину бонусных баллов пользователей.

    Args:
        src_tgt_url (str): URL для подключения к источнику и приемнику.
        src_tgt_driver (str): Драйвер для подключения к СУБД.
        tgt_mart_name (str): Имя целевой витрины данных.
    """
    # Создание Spark сессии
    spark = (
        SparkSession.builder
        .appName(f"Create_mart_{tgt_mart_name}")
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

    loyaltypoints_df = (
        spark.read
        .format("jdbc")
        .option("url", src_tgt_url)
        .option("driver", src_tgt_driver)
        .option("dbtable", "loyaltypoints") .load() \
        .load()
    )

    # Создание витрины продаж продуктов с разбивкой по статусу заказа
    user_loyalty_points_df = (
        users_df.join(loyaltypoints_df, "user_id")
        .groupBy("user_id", "first_name", "last_name", "loyalty_status")
        .agg({"points": "sum"})
        .withColumnRenamed("sum(points)", "total_loyalty_points")
        .orderBy(desc("total_loyalty_points"))
    )

    # Overwrite в приемнике
    (
        user_loyalty_points_df.write
        .format("jdbc")
        .option("url", src_tgt_url)
        .option("driver", src_tgt_driver)
        .option("dbtable", f"mart_{tgt_mart_name}")
        .mode("overwrite")
        .save()
    )

    # Остановка Spark сессии
    spark.stop()

def create_average_check_view(src_tgt_url: str, src_tgt_driver: str, tgt_mart_name: str):
    """
    Создает/перезаписывает витрину среднего чека с разбивкой по статусу заказа и статусу лояльности.
    
    Args:
        src_tgt_url (str): URL для подключения к источнику и приемнику.
        src_tgt_driver (str): Драйвер для подключения к СУБД.
        tgt_mart_name (str): Имя целевой витрины данных.
    """
    # Создание Spark сессии
    spark = (
        SparkSession.builder
        .appName(f"Create_mart_{tgt_mart_name}")
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
    )

    # Overwrite в приемнике
    (
        average_check_df.write
        .format("jdbc")
        .option("url", src_tgt_url)
        .option("driver", src_tgt_driver)
        .option("dbtable", f"mart_{tgt_mart_name}")
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
    parser.add_argument('--target_mart', type=str, required=True, choices=['user_activity', 'product_rating', 'average_check', "user_loyalty_points"])
    args = parser.parse_args()

    if args.target_mart == "user_activity":
        create_user_activity_view(args.src_tgt_url, args.src_tgt_driver, args.target_mart)
    elif args.target_mart == "product_rating":
        create_product_rating_view(args.src_tgt_url, args.src_tgt_driver, args.target_mart)
    elif args.target_mart == "average_check":
        create_average_check_view(args.src_tgt_url, args.src_tgt_driver, args.target_mart)
    elif args.target_mart == "user_loyalty_points":
        create_user_loyalty_points_view(args.src_tgt_url, args.src_tgt_driver, args.target_mart)

if __name__ == "__main__":
    main()