# backend_app/src/main.py
import os
import sys

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, jsonify
from flask_jwt_extended import JWTManager

# Import db instance from extensions.py
from src.extensions import db
# Import all models to ensure they are registered with SQLAlchemy
from src.models import models # This will import all classes from models.py

# Import Blueprints
from src.routes.auth import auth_bp, init_bcrypt
from src.routes.categories import categories_bp
from src.routes.menu_items import menu_items_bp
from src.routes.addresses import addresses_bp
from src.routes.orders import orders_bp
from src.routes.payments import payments_bp
from src.routes.admin import admin_bp # Import the admin blueprint

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a_very_secret_key_that_should_be_in_env_var_for_production')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'another_very_secret_jwt_key_for_production') # Change this!
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{os.getenv('DB_USERNAME', 'root')}:{os.getenv('DB_PASSWORD', 'password')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '3306')}/{os.getenv('DB_NAME', 'restaurant_db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
init_bcrypt(app) # Initialize Flask-Bcrypt
jwt = JWTManager(app) # Initialize Flask-JWT-Extended

# Create database tables if they don't exist
with app.app_context():
    db.create_all()

# Register Blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(categories_bp, url_prefix='/api') 
app.register_blueprint(menu_items_bp, url_prefix='/api') 
app.register_blueprint(addresses_bp, url_prefix='/api') 
app.register_blueprint(orders_bp, url_prefix='/api')      
app.register_blueprint(payments_bp, url_prefix='/api') 
app.register_blueprint(admin_bp, url_prefix='/api/admin') # Register the admin blueprint

@app.route('/api/health')
def health_check():
    return jsonify({"status": "healthy", "timestamp": models.datetime.utcnow().isoformat()}), 200

# Serve static files (e.g., for a frontend if co-hosted, or API docs)
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return jsonify({"message": "Welcome to the Restaurant API. No frontend index.html found at root."}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=True)

