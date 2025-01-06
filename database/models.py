from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Numeric, CheckConstraint, Text, Float
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

# Модель пользователей
class User(Base):
    __tablename__ = 'Users'

    user_id = Column(Integer, primary_key=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    phone = Column(String(20))
    registration_date = Column(DateTime, default=datetime.now)
    loyalty_status = Column(String(20), CheckConstraint("loyalty_status IN ('Gold', 'Silver', 'Bronze')"), nullable=False)

    # Связь с заказами
    orders = relationship("Order", back_populates="user")


# Модель категорий товаров
class ProductCategory(Base):
    __tablename__ = 'ProductCategories'

    category_id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    parent_category_id = Column(Integer, ForeignKey('ProductCategories.category_id'))

    # Связь с дочерними категориями
    subcategories = relationship("ProductCategory", backref="parent", remote_side=[category_id])
    products = relationship("Product", back_populates="category")


# Модель товаров
class Product(Base):
    __tablename__ = 'Products'

    product_id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    category_id = Column(Integer, ForeignKey('ProductCategories.category_id'))
    price = Column(Numeric(10, 2), nullable=False)
    stock_quantity = Column(Integer, default=0)
    creation_date = Column(DateTime, default=datetime.now)

    # Связь с категорией
    category = relationship("ProductCategory", back_populates="products")
    # Связь с деталями заказа
    order_details = relationship("OrderDetail", back_populates="product")


# Модель заказов
class Order(Base):
    __tablename__ = "Orders"

    order_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("Users.user_id"), nullable=False)
    order_date = Column(DateTime, nullable=False)
    total_amount = Column(Float, nullable=True)
    status = Column(String, nullable=False)
    delivery_date = Column(DateTime, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "status IN ('Pending', 'Completed', 'Canceled', 'Processing', 'Shipped', 'Delivered', 'Returned', 'Failed')",
            name="Orders_status_check"
        ),
    )

    user = relationship("User", back_populates="orders")
    order_details = relationship("OrderDetail", back_populates="order")


# Модель деталей заказа
class OrderDetail(Base):
    __tablename__ = "OrderDetails"

    order_detail_id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("Orders.order_id"), nullable=False)
    product_id = Column(Integer, ForeignKey("Products.product_id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    price_per_unit = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)

    order = relationship("Order", back_populates="order_details")
    product = relationship("Product")
