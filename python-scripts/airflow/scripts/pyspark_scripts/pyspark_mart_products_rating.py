import argparse
from pyspark.sql import SparkSession
import pyspark.sql.functions as F

def create_products_rating_view(src_tgt_url: str, src_tgt_driver: str):
    """
    Создает/перезаписывает витрину рейтинга продуктов по категориям.

    Args:
        src_tgt_url (str): URL для подключения к источнику и приемнику.
        src_tgt_driver (str): Драйвер для подключения к СУБД.
    """
    # Создание Spark сессии
    spark = (
        SparkSession.builder
        .appName(f"Create_mart_products_rating_view")
        .getOrCreate()
    )

    # Чтение данных из "STG" слоя
    products_df = (
        spark.read
        .format("jdbc")
        .option("url", src_tgt_url)
        .option("driver", src_tgt_driver)
        .option("dbtable", "products")
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

    categories_df = (
        spark.read
        .format("jdbc")
        .option("url", src_tgt_url)
        .option("driver", src_tgt_driver)
        .option("dbtable", "productcategories")  # Таблица категорий
        .load()
    )


    # Создание витрины с добавлением общего количества отзывов
    product_rating_df = (
        products_df.join(reviews_df, "product_id")
        .groupBy("product_id", "name", "category_id" )  # Группировка по продукту, имени и категории
        .agg({"rating": "avg", "review_id": "count"})  # Общее количество отзывов
        .withColumnRenamed("avg(rating)", "average_rating")
        .withColumn("average_rating", F.round("average_rating",2))
        .withColumnRenamed("count(review_id)", "total_reviews")
        .withColumnRenamed("name", "product_name")
    )

    # Присоединяем категории
    products_with_categories_df = (
        product_rating_df
        .join(categories_df, "category_id")
        .withColumnRenamed("name", "category_name")
        .drop("parent_category_id")
        .select("product_id", "product_name", "category_name", "average_rating", "total_reviews")
        .orderBy(F.desc("average_rating"))  # Сортировка по рейтингу
    )


    # Overwrite в приемнике
    (
        products_with_categories_df.write
        .format("jdbc")
        .option("url", src_tgt_url)
        .option("driver", src_tgt_driver)
        .option("dbtable", "mart_products_rating")
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

    create_products_rating_view(args.src_tgt_url, args.src_tgt_driver)

if __name__ == "__main__":
    main()