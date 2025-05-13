# backend_app/src/models/models.py

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.mysql import ENUM
from datetime import datetime

# Initialize SQLAlchemy. This will be configured with the Flask app in main.py
# For now, we just create the object. It will be properly initialized in main.py
# db = SQLAlchemy() 
# It's better to define db in main.py and import it here to avoid circular imports if models need the app context or db instance upon definition.
# However, for simple model definitions, this can work if db is initialized before models are used.
# Let's assume db will be imported from the main application file or a shared extension file.

# It's a common pattern to have an extensions.py or similar where db is initialized and then imported.
# For the template structure: `create_flask_app` usually sets up db in `main.py` or expects it there.
# Let's assume `db` will be imported from `src.main` or a dedicated `extensions.py` later.
# For now, to make this file self-contained for writing, I'll define a placeholder `db`
# and note that it needs to be the actual `db` instance from the Flask app.

# Correction: The template `create_flask_app` initializes `db = SQLAlchemy()` in `main.py`
# and it's expected that models will import this `db` instance.
# So, the models file should look like:
# from .. import db  <-- This would be if db is in __init__.py of src or similar
# Or more directly if main.py is structured to allow it:
# from src.main import db # This might cause circular dependency if main.py imports models.

# A common pattern for Flask-SQLAlchemy is to have an `extensions.py`:
# src/extensions.py
# from flask_sqlalchemy import SQLAlchemy
# db = SQLAlchemy()

# Then in src/main.py:
# from .extensions import db
# db.init_app(app)

# And in src/models/models.py:
# from ..extensions import db

# Given the template structure, let's assume we will adjust main.py to make `db` available for import.
# For now, I will write the models assuming `db` is an available SQLAlchemy instance.

# Let's create a new file `extensions.py` in `src` directory for `db` initialization.

# Content for /home/ubuntu/restaurant_app/backend_app/src/extensions.py
# from flask_sqlalchemy import SQLAlchemy
# db = SQLAlchemy()

# Then this file (models.py) will be:
from ..extensions import db # Assuming extensions.py is created in parent directory 'src'

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False) # Increased length for hash
    email = db.Column(db.String(120), unique=True, nullable=False)
    full_name = db.Column(db.String(120))
    phone_number = db.Column(db.String(20), unique=True)
    role = db.Column(ENUM('customer', 'admin', 'staff', name='user_roles_enum'), nullable=False, default='customer')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    addresses = db.relationship('Address', backref='user', lazy=True)
    orders = db.relationship('Order', backref='user', lazy=True)

class Address(db.Model):
    __tablename__ = 'addresses'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    address_line1 = db.Column(db.String(255), nullable=False)
    address_line2 = db.Column(db.String(255))
    city = db.Column(db.String(100), nullable=False)
    postal_code = db.Column(db.String(20), nullable=False)
    country = db.Column(db.String(100), nullable=False)
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    orders = db.relationship('Order', backref='delivery_address', lazy=True)

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    menu_items = db.relationship('MenuItem', backref='category', lazy=True)

class MenuItem(db.Model):
    __tablename__ = 'menu_items'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    image_url = db.Column(db.String(255))
    is_available = db.Column(db.Boolean, default=True)
    preparation_time_minutes = db.Column(db.Integer)
    calories = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    order_items = db.relationship('OrderItem', backref='menu_item', lazy=True)

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    delivery_address_id = db.Column(db.Integer, db.ForeignKey('addresses.id'), nullable=False)
    # restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant_info.id')) # Assuming single restaurant for now
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(ENUM('pending', 'confirmed', 'preparing', 'out_for_delivery', 'delivered', 'cancelled', name='order_status_enum'), nullable=False, default='pending')
    payment_status = db.Column(ENUM('pending', 'paid', 'failed', name='payment_status_enum'), nullable=False, default='pending')
    payment_method = db.Column(db.String(50))
    transaction_id = db.Column(db.String(100))
    delivery_instructions = db.Column(db.Text)
    estimated_delivery_time = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    order_items = db.relationship('OrderItem', backref='order', lazy=True, cascade="all, delete-orphan")
    payment = db.relationship('Payment', backref='order', uselist=False, cascade="all, delete-orphan") # One-to-one

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_items.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    price_at_order = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)

class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, unique=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_gateway_transaction_id = db.Column(db.String(100), nullable=False)
    status = db.Column(ENUM('success', 'failed', 'pending', name='payment_process_status_enum'), nullable=False)
    payment_method_details = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class RestaurantInfo(db.Model):
    __tablename__ = 'restaurant_info'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(150), nullable=False)
    address = db.Column(db.String(255))
    phone_number = db.Column(db.String(20))
    email = db.Column(db.String(120))
    logo_url = db.Column(db.String(255))
    operating_hours = db.Column(db.JSON)
    delivery_zones = db.Column(db.JSON)

