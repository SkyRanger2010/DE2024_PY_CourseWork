import time
import json
import random
import logging
from kafka import KafkaProducer
from sqlalchemy import create_engine, select, text
from faker import Faker
import os

def clean_phone(phone: str) -> str:
    """Очистка телефонного номера от лишних символов и обрезка до 20 символов"""
    import re
    cleaned = re.sub(r"[^\d+]", "", phone)
    return cleaned[:20]

def generate_user_msg(fake: Faker):
    """
    Генерирует случайные данные пользователя в формате JSON.

    Args:
        fake (Faker): Экземпляр Faker, используемый для генерации случайных данных.
    """
    return {
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "email": fake.email(),
        "phone": clean_phone(fake.phone_number()),
        "registration_date": fake.date_time_between(start_date='-1y', end_date='now').isoformat(),
        "loyalty_status": random.choice(["Gold", "Silver", "Bronze"])
    }

def generate_review_msg(fake: Faker, users: list, products: list):
    """
    Генерация случайного отзыва в формате JSON.

    Args:
        fake (Faker): Экземпляр Faker для генерации текста отзыва.
        users (list): Список существующих пользователей.
        products (list): Список существующих продуктов.
    """
    return {
        "user_id": random.choice(users),
        "product_id": random.choice(products),
        "rating": random.randint(1, 5),
        "review_text": fake.text(max_nb_chars=200),
        "created_at": fake.date_time_between(start_date='-1m', end_date='now').isoformat()
    }

def fetch_users_and_products(db_url: str):
    """
    Получение списка пользователей и продуктов из PostgreSQL без использования MetaData.

    Args:
        db_url (str): Строка подключения к базе данных.

    Returns:
        tuple: Список идентификаторов пользователей и продуктов.
    """
    schema = os.getenv("POSTGRESQL_APP_SCHEMA", "source")  # Учитываем схему
    engine = create_engine(db_url)

    query_users = f"SET search_path TO {schema}; SELECT user_id FROM users"
    query_products = f"SET search_path TO {schema}; SELECT product_id FROM products"

    with engine.connect() as conn:
        try:
            # Получение списка пользователей
            result_users = conn.execute(text(query_users))
            users = [row[0] for row in result_users]

            # Получение списка продуктов
            result_products = conn.execute(text(query_products))
            products = [row[0] for row in result_products]

        except Exception as e:
            raise ValueError(f"Ошибка при выполнении запросов: {e}")

    return users, products

def get_postgres_connection_url():
    """
    Формирует строку подключения к PostgreSQL на основе переменных окружения.
    """
    user = os.getenv("POSTGRESQL_APP_USER", "db_user")
    password = os.getenv("POSTGRESQL_APP_PASSWORD", "qwerty")
    host = os.getenv("POSTGRESQL_APP_HOST", "postgresql")
    db = os.getenv("POSTGRESQL_APP_DB", "postgres_db")
    return f"postgresql://{user}:{password}@{host}:5432/{db}"

def main():
    """Непрерывная генерация и отправка данных пользователей и отзывов в Kafka."""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Конфигурации Kafka
    kafka_bootstrap_servers = os.getenv("KAFKA_INTERNAL_CONNECT_PATH")
    kafka_user_topic = os.getenv("KAFKA_USER_TOPIC_NAME")
    kafka_review_topic = os.getenv("KAFKA_REVIEW_TOPIC_NAME")
    msg_gen_period = os.getenv("KAFKA_DATAGEN_PERIOD_SECS", "1")
    db_url = get_postgres_connection_url()  # Формируем строку подключения

    try:
        msg_gen_period = float(msg_gen_period)
    except ValueError:
        logger.error("Неверное значение KAFKA_DATAGEN_PERIOD_SECS. Установлено значение по умолчанию: 1 секунда.")
        msg_gen_period = 1

    # Инициализация продьюсера Kafka
    producer = KafkaProducer(bootstrap_servers=kafka_bootstrap_servers, value_serializer=lambda v: json.dumps(v).encode('utf-8'))
    fake = Faker()

    try:
        # Загрузка данных из базы
        users, products = fetch_users_and_products(db_url)
        if not users or not products:
            logger.error("Списки пользователей и продуктов пусты. Проверьте содержимое базы данных.")
            return

        msg_id = 1

        while True:
            try:
                # Генерация сообщения пользователя
                user_msg = generate_user_msg(fake)
                producer.send(kafka_user_topic, value=user_msg)
                logger.info(f"User message №{msg_id} отправлено в Kafka: {user_msg}")
                time.sleep(msg_gen_period)
                msg_id += 1

                # Генерация сообщения отзыва
                review_msg = generate_review_msg(fake, users, products)
                producer.send(kafka_review_topic, value=review_msg)
                logger.info(f"Review message №{msg_id} отправлено в Kafka: {review_msg}")
                time.sleep(msg_gen_period)
                msg_id += 1

            except Exception as e:
                logger.error(f"Ошибка при генерации или отправке сообщения: {e}")
                time.sleep(msg_gen_period)

    except Exception as e:
        logger.error(f"Ошибка подключения к базе данных: {e}")

if __name__ == "__main__":
    main()
