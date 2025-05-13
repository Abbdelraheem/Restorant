# backend_app/src/routes/menu_items.py

from flask import Blueprint, request, jsonify
from ..extensions import db
from ..models.models import MenuItem, Category # Import Category to check if parent category is active
from sqlalchemy.orm import joinedload # To efficiently load category info

menu_items_bp = Blueprint("menu_items_bp", __name__)

@menu_items_bp.route("/menu-items", methods=["GET"])
def get_menu_items():
    try:
        # Optionally, add query parameters for filtering, e.g., by category_id or search term
        query = MenuItem.query.options(joinedload(MenuItem.category)).filter(MenuItem.is_available==True, Category.is_active==True)
        
        category_id_filter = request.args.get("category_id")
        if category_id_filter:
            query = query.filter(MenuItem.category_id == category_id_filter)
            
        search_term = request.args.get("search")
        if search_term:
            query = query.filter(MenuItem.name.ilike(f"%{search_term}%"))

        items = query.all()
        
        return jsonify([{
            "id": item.id,
            "category_id": item.category_id,
            "category_name": item.category.name if item.category else None, # Include category name
            "name": item.name,
            "description": item.description,
            "price": str(item.price),
            "image_url": item.image_url,
            "is_available": item.is_available
        } for item in items]), 200
    except Exception as e:
        return jsonify({"message": "Error fetching menu items", "error": str(e)}), 500

@menu_items_bp.route("/menu-items/<int:item_id>", methods=["GET"])
def get_menu_item_detail(item_id):
    try:
        item = MenuItem.query.options(joinedload(MenuItem.category)).filter(MenuItem.id == item_id, MenuItem.is_available==True, Category.is_active==True).first()
        if not item:
            return jsonify({"message": "Menu item not found or not available"}), 404
        
        return jsonify({
            "id": item.id,
            "category_id": item.category_id,
            "category_name": item.category.name if item.category else None,
            "name": item.name,
            "description": item.description,
            "price": str(item.price),
            "image_url": item.image_url,
            "is_available": item.is_available,
            "preparation_time_minutes": item.preparation_time_minutes,
            "calories": item.calories
        }), 200
    except Exception as e:
        return jsonify({"message": "Error fetching menu item details", "error": str(e)}), 500

# Admin routes for menu items will be in a separate admin blueprint.

