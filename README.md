
# DE2024_PY_CourseWork

Итоговая работа по курсу "Python для инженеров данных" магистратуры ВШЭ "Инженерия данных".

---

## Этап 1: Создание базы данных PostgreSQL и генерация данных

### 1. Создание базы данных

В проекте используется база данных PostgreSQL. Для работы создан скрипт инициализации, который автоматически создает таблицы, связи между ними, ограничения и индексы.

#### Структура базы данных:

- **Users**: Информация о пользователях.
  - `user_id` (PK): Уникальный идентификатор пользователя.
  - `first_name`: Имя пользователя.
  - `last_name`: Фамилия пользователя.
  - `email`: Электронная почта (уникальное значение).
  - `phone`: Номер телефона.
  - `registration_date`: Дата регистрации.
  - `loyalty_status`: Статус лояльности (`Gold`, `Silver`, `Bronze`).

- **ProductCategories**: Иерархия категорий товаров.
  - `category_id` (PK): Уникальный идентификатор категории.
  - `name`: Название категории.
  - `parent_category_id` (FK): Ссылка на родительскую категорию.

- **Products**: Информация о товарах.
  - `product_id` (PK): Уникальный идентификатор товара.
  - `name`: Название товара.
  - `description`: Описание товара.
  - `category_id` (FK): Категория товара.
  - `price`: Цена товара.
  - `stock_quantity`: Количество товара на складе.
  - `creation_date`: Дата добавления товара.

- **Orders**: Информация о заказах.
  - `order_id` (PK): Уникальный идентификатор заказа.
  - `user_id` (FK): Пользователь, сделавший заказ.
  - `order_date`: Дата заказа.
  - `total_amount`: Общая сумма заказа.
  - `status`: Статус заказа (`Pending`, `Completed`, и т.д.).
  - `delivery_date`: Дата доставки.

- **OrderDetails**: Детали заказов.
  - `order_detail_id` (PK): Уникальный идентификатор детали заказа.
  - `order_id` (FK): Ссылка на заказ.
  - `product_id` (FK): Ссылка на товар.
  - `quantity`: Количество товаров в заказе.
  - `price_per_unit`: Цена за единицу товара.
  - `total_price`: Общая стоимость позиции.

- **Reviews**: Отзывы о товарах.
  - `review_id` (PK): Уникальный идентификатор отзыва.
  - `user_id` (FK): Пользователь, оставивший отзыв.
  - `product_id` (FK): Продукт, на который оставлен отзыв.
  - `rating`: Оценка товара (от 1 до 5).
  - `review_text`: Текст отзыва.
  - `created_at`: Дата создания отзыва.

- **LoyaltyPoints**: Система лояльности.
  - `loyalty_id` (PK): Уникальный идентификатор записи.
  - `user_id` (FK): Пользователь, получивший бонусные баллы.
  - `points`: Количество начисленных баллов.
  - `reason`: Причина начисления (например, "Order", "Promotion").
  - `created_at`: Дата начисления.

---

### 2. Генерация данных

Для наполнения базы данных реализован модуль генерации данных (`generator.py`), который:

- Очищает текущую базу данных перед заполнением.
- Создает пользователей, товары, категории, заказы, детали заказов, отзывы и бонусные баллы.
- Даты регистрации, заказа и доставки синхронизированы:
  - Дата заказа всегда после даты регистрации.
  - Дата доставки всегда позже даты заказа.

#### Настройки генерации

Параметры генерации, такие как количество пользователей, товаров, заказов, отзывов и бонусных баллов, задаются в конфигурационном файле `data_generation/config.py`:
```python
DATA_GENERATION_CONFIG = {
    "users_count": 1000,
    "products_count": 500,
    "orders_count": 1000,
    "order_details_min": 1,
    "order_details_max": 5,
    "reviews_count": 2000,
    "loyalty_points_count": 1500
}
```

---

### 3. Процесс создания базы данных

Для работы проекта используется база данных PostgreSQL, которая запускается в Docker-контейнере. Процесс включает запуск контейнера, создание структуры базы данных и начальную инициализацию.

#### 1. Настройка Docker-контейнера

В проекте уже настроен файл `docker-compose.yml`, который автоматизирует запуск базы данных PostgreSQL.

##### Основные параметры:
- **POSTGRES_DB:** Название создаваемой базы данных (`postgresdb`).
- **POSTGRES_USER:** Имя пользователя базы данных (`postgres`).
- **POSTGRES_PASSWORD:** Пароль для доступа (`qwerty`).
- **Volumes:**
  - `./Database_init:/docker-entrypoint-initdb.d`: Каталог для SQL-скриптов инициализации.
  - `postgres-data:/var/lib/postgresql/data`: Каталог для хранения данных.

---

#### 2. Скрипт инициализации базы данных

SQL-скрипты для создания структуры базы данных и начальных данных расположены в папке `Database_init/`. 

---

#### 3. Запуск контейнера PostgreSQL

1. Убедитесь, что у вас установлен [Docker](https://www.docker.com/) и [Docker Compose](https://docs.docker.com/compose/).
2. В корневой директории проекта выполните команду:
   ```bash
   docker-compose up -d
   ```

3. Проверьте состояние контейнера:
   ```bash
   docker ps
   ```

4. Убедитесь, что база данных запущена и доступна по следующим параметрам:
   - **Хост:** `localhost`
   - **Порт:** `5432`
   - **Имя базы данных:** `postgresdb`
   - **Имя пользователя:** `postgres`
   - **Пароль:** `qwerty`

---

#### Примечания

- Все данные хранятся в Docker Volume `postgres-data`. Они сохраняются между перезапусками контейнера.
- Если вам нужно пересоздать базу данных, удалите volume с помощью команды:
  ```bash
  docker-compose down -v
  ```

