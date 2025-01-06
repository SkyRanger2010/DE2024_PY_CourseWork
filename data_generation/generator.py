from faker import Faker
import random
from postgresdb.models import User, ProductCategory, Product, Order, OrderDetail, Review, LoyaltyPoint
from postgresdb_schemas.loyalty_schema import LoyaltyPointCreate
from postgresdb_schemas.review_schema import ReviewCreate
from postgresdb_schemas.user_schema import UserCreate
from postgresdb_schemas.category_schema import CategoryCreate
from postgresdb_schemas.product_schema import ProductCreate
from postgresdb_schemas.order_schema import OrderCreate, OrderDetailCreate
from postgresdb.db_config import get_session
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import timedelta
from data_generation.config import DATA_GENERATION_CONFIG


def clean_phone(phone: str) -> str:
    """Очистка телефонного номера от лишних символов и обрезка до 20 символов"""
    import re
    cleaned = re.sub(r"[^\d+]", "", phone)
    return cleaned[:20]


def clear_database(session):
    """Очистка всех данных из базы перед генерацией."""
    print("Очистка базы данных...")
    session.execute(text("TRUNCATE TABLE \"OrderDetails\" CASCADE;"))
    session.execute(text("TRUNCATE TABLE \"Orders\" CASCADE;"))
    session.execute(text("TRUNCATE TABLE \"Reviews\" CASCADE;"))
    session.execute(text("TRUNCATE TABLE \"LoyaltyPoints\" CASCADE;"))
    session.execute(text("TRUNCATE TABLE \"Products\" CASCADE;"))
    session.execute(text("TRUNCATE TABLE \"ProductCategories\" CASCADE;"))
    session.execute(text("TRUNCATE TABLE \"Users\" CASCADE;"))
    session.commit()
    print("База данных очищена.")


def generate_data():
    """Функция для очистки базы и генерации большого количества тестовых данных."""
    fake = Faker()
    session: Session = get_session()

    try:
        # Очистка базы данных
        clear_database(session)

        # Генерация пользователей
        print("Генерация пользователей...")
        generated_emails = set()
        user_registration_dates = {}  # Словарь для хранения дат регистрации пользователей

        for _ in range(DATA_GENERATION_CONFIG["users_count"]):
            while True:
                email = fake.email()
                if email not in generated_emails:
                    generated_emails.add(email)
                    break

            registration_date = fake.date_time_between(start_date='-1y', end_date='now')  # Случайная дата регистрации

            user_data = {
                "first_name": fake.first_name(),
                "last_name": fake.last_name(),
                "email": email,
                "phone": clean_phone(fake.phone_number()),
                "registration_date": registration_date,
                "loyalty_status": random.choice(['Gold', 'Silver', 'Bronze']),
            }

            user_schema = UserCreate(**user_data)
            user = User(**user_schema.model_dump())
            session.add(user)
            session.flush()

            # Сохраняем дату регистрации
            user_registration_dates[user.user_id] = registration_date

        session.commit()

        # Генерация категорий товаров
        print("Генерация категорий товаров...")
        expanded_categories = {
            "Electronics": ["Smartphones", "Laptops", "Tablets", "Audio", "Televisions", "Smart Devices", "Cameras"],
            "Books": ["Fiction", "Non-Fiction", "Children’s Books", "Educational", "Comics & Graphic Novels", "Cookbooks"],
            "Clothing": ["Men's Clothing", "Women's Clothing", "Children's Clothing", "Sportswear", "Accessories"],
            "Home Appliances": ["Kitchen Appliances", "Cleaning Appliances", "Heating & Cooling"],
            "Toys": ["Action Figures", "Educational Toys", "Board Games", "Dolls", "Puzzles"],
        }

        category_ids = {}
        for group, subcategories in expanded_categories.items():
            category_data = {"name": group, "parent_category_id": None}
            category_schema = CategoryCreate(**category_data)
            group_category = ProductCategory(**category_schema.model_dump())
            session.add(group_category)
            session.flush()

            subcategory_ids = []
            for subcategory in subcategories:
                subcategory_data = {"name": subcategory, "parent_category_id": group_category.category_id}
                subcategory_schema = CategoryCreate(**subcategory_data)
                subcategory_instance = ProductCategory(**subcategory_schema.model_dump())
                session.add(subcategory_instance)
                session.flush()
                subcategory_ids.append(subcategory_instance.category_id)

            category_ids[group] = {"group_id": group_category.category_id, "subcategories": subcategory_ids}

        session.commit()

        # Генерация товаров
        print("Генерация товаров...")
        for _ in range(DATA_GENERATION_CONFIG["products_count"]):
            group = random.choice(list(expanded_categories.keys()))
            subcategory_id = random.choice(category_ids[group]["subcategories"])
            product_data = {
                "name": fake.word(),
                "description": fake.text(max_nb_chars=200),
                "category_id": subcategory_id,
                "price": round(random.uniform(10, 1000), 2),
                "stock_quantity": random.randint(0, 100),
            }
            product_schema = ProductCreate(**product_data)
            product = Product(**product_schema.model_dump())
            session.add(product)

        session.commit()

        # Получение существующих user_id и product_id
        user_ids = [row[0] for row in session.execute(text("SELECT user_id FROM \"Users\"")).fetchall()]
        product_ids = [row[0] for row in session.execute(text("SELECT product_id FROM \"Products\"")).fetchall()]

        # Генерация заказов и деталей заказов
        print("Генерация заказов...")
        order_statuses = [
            "Pending",     # В ожидании
            "Completed",   # Завершен
            "Canceled",    # Отменен
            "Processing",  # В обработке
            "Shipped",     # Отправлен
            "Delivered",   # Доставлен
            "Returned",    # Возвращен
            "Failed",      # Неудачный
        ]

        for _ in range(DATA_GENERATION_CONFIG["orders_count"]):
            user_id = random.choice(user_ids)
            registration_date = user_registration_dates[user_id]

            # Дата заказа должна быть после даты регистрации
            order_date = fake.date_time_between(start_date=registration_date, end_date='now')
            delivery_date = fake.date_time_between(start_date=order_date, end_date=order_date + timedelta(days=30))

            total_amount = 0  # Инициализация общей суммы заказа

            # Генерация деталей заказа
            order_details = []
            for _ in range(random.randint(DATA_GENERATION_CONFIG["order_details_min"], DATA_GENERATION_CONFIG["order_details_max"])):
                product_id = random.choice(product_ids)
                quantity = random.randint(1, 5)
                price_per_unit = round(random.uniform(10, 1000), 2)
                total_price = quantity * price_per_unit
                total_amount += total_price

                order_details.append({
                    "product_id": product_id,
                    "quantity": quantity,
                    "price_per_unit": price_per_unit,
                    "total_price": round(total_price,2),
                })

            order_data = {
                "user_id": user_id,
                "order_date": order_date,
                "status": random.choice(order_statuses),
                "delivery_date": delivery_date,
                "total_amount": round(total_amount,2)
            }

            order_schema = OrderCreate(**order_data)
            order = Order(**order_schema.model_dump())
            session.add(order)
            session.flush()

            # Добавление деталей заказа в базу
            for detail in order_details:
                order_detail_schema = OrderDetailCreate(**detail)
                order_detail = OrderDetail(order_id=order.order_id, **order_detail_schema.model_dump())
                session.add(order_detail)

        session.commit()

        # Генерация отзывов
        print("Генерация отзывов...")
        for _ in range(DATA_GENERATION_CONFIG["reviews_count"]):
            user_id = random.choice(user_ids)
            product_id = random.choice(product_ids)
            review_data = {
                "user_id": user_id,
                "product_id": product_id,
                "rating": random.randint(1, 5),
                "review_text": fake.text(max_nb_chars=200)
            }
            review_schema = ReviewCreate(**review_data)
            review = Review(**review_schema.model_dump())
            session.add(review)
        session.commit()

        # Генерация бонусных баллов
        print("Генерация бонусных баллов...")
        for _ in range(DATA_GENERATION_CONFIG["loyalty_points_count"]):
            user_id = random.choice(user_ids)
            loyalty_data = {
                "user_id": user_id,
                "points": random.randint(10, 500),
                "reason": random.choice(["Order", "Promotion", "Event Participation"])
            }
            loyalty_schema = LoyaltyPointCreate(**loyalty_data)
            loyalty_point = LoyaltyPoint(**loyalty_schema.model_dump())
            session.add(loyalty_point)
        session.commit()

        print("Данные успешно сгенерированы!")

    except Exception as e:
        print(f"Ошибка генерации данных: {e}")
        session.rollback()
    finally:
        session.close()
