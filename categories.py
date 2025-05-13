# backend_app/src/routes/categories.py

from flask import Blueprint, request, jsonify
from ..extensions import db
from ..models.models import Category, MenuItem
from flask_jwt_extended import jwt_required, get_jwt # For admin-only access if needed later

categories_bp = Blueprint("categories_bp", __name__)

@categories_bp.route("/categories", methods=["GET"])
def get_categories():
    try:
        categories = Category.query.filter_by(is_active=True).all()
        return jsonify([{
            "id": cat.id,
            "name": cat.name,
            "description": cat.description,
            "image_url": cat.image_url
        } for cat in categories]), 200
    except Exception as e:
        return jsonify({"message": "Error fetching categories", "error": str(e)}), 500

@categories_bp.route("/categories/<int:category_id>/items", methods=["GET"])
def get_items_by_category(category_id):
    try:
        category = Category.query.get(category_id)
        if not category or not category.is_active:
            return jsonify({"message": "Category not found or not active"}), 404

        menu_items = MenuItem.query.filter_by(category_id=category_id, is_available=True).all()
        return jsonify([{
            "id": item.id,
            "name": item.name,
            "description": item.description,
            "price": str(item.price), # Convert Decimal to string for JSON
            "image_url": item.image_url,
            "is_available": item.is_available
        } for item in menu_items]), 200
    except Exception as e:
        return jsonify({"message": "Error fetching menu items for category", "error": str(e)}), 500

# Admin routes for categories will be in a separate admin blueprint.

