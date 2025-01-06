-- Создание таблицы "Users"
CREATE TABLE "Users" (
    "user_id" SERIAL PRIMARY KEY,
    "first_name" VARCHAR(100) NOT NULL,
    "last_name" VARCHAR(100) NOT NULL,
    "email" VARCHAR(255) UNIQUE NOT NULL,
    "phone" VARCHAR(20),
    "registration_date" TIMESTAMP NOT NULL,
    "loyalty_status" VARCHAR(20) CHECK ("loyalty_status" IN ('Gold', 'Silver', 'Bronze'))
);

-- Создание таблицы "ProductCategories"
CREATE TABLE "ProductCategories" (
    "category_id" SERIAL PRIMARY KEY,
    "name" VARCHAR(100) NOT NULL,
    "parent_category_id" INT REFERENCES "ProductCategories"("category_id") ON DELETE SET NULL
);

-- Создание таблицы "Products"
CREATE TABLE "Products" (
    "product_id" SERIAL PRIMARY KEY,
    "name" VARCHAR(100) NOT NULL,
    "description" TEXT,
    "category_id" INT REFERENCES "ProductCategories"("category_id") ON DELETE CASCADE,
    "price" NUMERIC(10, 2) NOT NULL CHECK ("price" >= 0),
    "stock_quantity" INT NOT NULL CHECK ("stock_quantity" >= 0),
    "creation_date" TIMESTAMP DEFAULT NOW()
);

-- Создание таблицы "Orders"
CREATE TABLE "Orders" (
    "order_id" SERIAL PRIMARY KEY,
    "user_id" INT REFERENCES "Users"("user_id") ON DELETE CASCADE,
    "order_date" TIMESTAMP NOT NULL,
    "total_amount" NUMERIC(10, 2) NOT NULL CHECK ("total_amount" >= 0),
    "status" VARCHAR(20) NOT NULL CHECK ("status" IN ('Pending', 'Completed', 'Canceled', 'Processing', 'Shipped', 'Delivered', 'Returned', 'Failed')),
    "delivery_date" TIMESTAMP
);

-- Создание таблицы "OrderDetails"
CREATE TABLE "OrderDetails" (
    "order_detail_id" SERIAL PRIMARY KEY,
    "order_id" INT REFERENCES "Orders"("order_id") ON DELETE CASCADE,
    "product_id" INT REFERENCES "Products"("product_id") ON DELETE CASCADE,
    "quantity" INT NOT NULL CHECK ("quantity" > 0),
    "price_per_unit" NUMERIC(10, 2) NOT NULL CHECK ("price_per_unit" >= 0),
    "total_price" NUMERIC(10, 2) NOT NULL CHECK ("total_price" >= 0)
);

-- Создание таблицы Reviews
CREATE TABLE "Reviews" (
    "review_id" SERIAL PRIMARY KEY,
    "user_id" INT NOT NULL REFERENCES "Users"("user_id") ON DELETE CASCADE,
    "product_id" INT NOT NULL REFERENCES "Products"("product_id") ON DELETE CASCADE,
    "rating" INT NOT NULL CHECK ("rating" BETWEEN 1 AND 5),
    "review_text" TEXT,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Создание таблицы LoyaltyPoints
CREATE TABLE "LoyaltyPoints" (
    "loyalty_id" SERIAL PRIMARY KEY,
    "user_id" INT NOT NULL REFERENCES "Users"("user_id") ON DELETE CASCADE,
    "points" INT NOT NULL,
    "reason" VARCHAR(255) NOT NULL,
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- Индексы для ускорения выборок
CREATE INDEX "idx_users_email" ON "Users"("email");
CREATE INDEX "idx_products_category_id" ON "Products"("category_id");
CREATE INDEX "idx_orders_user_id" ON "Orders"("user_id");
CREATE INDEX "idx_orderdetails_order_id" ON "OrderDetails"("order_id");
CREATE INDEX "idx_orderdetails_product_id" ON "OrderDetails"("product_id");
CREATE INDEX "idx_reviews_user_id" ON "Reviews"("user_id");
CREATE INDEX "idx_reviews_product_id" ON "Reviews"("product_id");
CREATE INDEX "idx_loyalty_points_user_id" ON "LoyaltyPoints"("user_id");
