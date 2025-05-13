# backend_app/src/routes/admin.py

from flask import Blueprint, request, jsonify
from ..extensions import db
from ..models.models import Category, MenuItem, Order, User, RestaurantInfo
from flask_jwt_extended import jwt_required, get_jwt_identity
from functools import wraps

admin_bp = Blueprint("admin_bp", __name__)

# Decorator to check for admin role
def admin_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if not user or user.role not in ["admin", "staff"]:
            return jsonify({"message": "Admins or staff only!"}), 403
        return fn(*args, **kwargs)
    return wrapper

# Category Management (Admin)
@admin_bp.route("/categories", methods=["POST"])
@admin_required
def create_category():
    data = request.get_json()
    try:
        new_category = Category(
            name=data.get("name"),
            description=data.get("description"),
            image_url=data.get("image_url"),
            is_active=data.get("is_active", True)
        )
        if not new_category.name:
            return jsonify({"message": "Category name is required"}), 400
        db.session.add(new_category)
        db.session.commit()
        return jsonify({"id": new_category.id, "name": new_category.name, "message": "Category created"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error creating category", "error": str(e)}), 500

@admin_bp.route("/categories", methods=["GET"])
@admin_required
def get_all_categories_admin():
    categories = Category.query.all()
    return jsonify([{
        "id": cat.id, "name": cat.name, "description": cat.description, 
        "image_url": cat.image_url, "is_active": cat.is_active
    } for cat in categories]), 200

@admin_bp.route("/categories/<int:category_id>", methods=["PUT"])
@admin_required
def update_category(category_id):
    category = Category.query.get_or_404(category_id)
    data = request.get_json()
    try:
        category.name = data.get("name", category.name)
        category.description = data.get("description", category.description)
        category.image_url = data.get("image_url", category.image_url)
        category.is_active = data.get("is_active", category.is_active)
        db.session.commit()
        return jsonify({"id": category.id, "message": "Category updated"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error updating category", "error": str(e)}), 500

@admin_bp.route("/categories/<int:category_id>", methods=["DELETE"])
@admin_required
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)
    try:
        # Soft delete by setting is_active to False, or hard delete
        # For now, let's do a hard delete for simplicity, or check if items exist
        if category.menu_items:
            return jsonify({"message": "Cannot delete category with associated menu items. Set to inactive instead."}), 400
        db.session.delete(category)
        db.session.commit()
        return jsonify({"message": "Category deleted"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error deleting category", "error": str(e)}), 500

# Menu Item Management (Admin)
@admin_bp.route("/menu-items", methods=["POST"])
@admin_required
def create_menu_item():
    data = request.get_json()
    try:
        new_item = MenuItem(
            category_id=data.get("category_id"),
            name=data.get("name"),
            description=data.get("description"),
            price=data.get("price"),
            image_url=data.get("image_url"),
            is_available=data.get("is_available", True),
            preparation_time_minutes=data.get("preparation_time_minutes"),
            calories=data.get("calories")
        )
        if not all([new_item.category_id, new_item.name, new_item.description, new_item.price is not None]):
            return jsonify({"message": "Category ID, name, description, and price are required"}), 400
        db.session.add(new_item)
        db.session.commit()
        return jsonify({"id": new_item.id, "name": new_item.name, "message": "Menu item created"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error creating menu item", "error": str(e)}), 500

@admin_bp.route("/menu-items", methods=["GET"])
@admin_required
def get_all_menu_items_admin():
    items = MenuItem.query.all()
    return jsonify([{
        "id": item.id, "category_id": item.category_id, "name": item.name, 
        "description": item.description, "price": str(item.price), 
        "image_url": item.image_url, "is_available": item.is_available
    } for item in items]), 200

@admin_bp.route("/menu-items/<int:item_id>", methods=["PUT"])
@admin_required
def update_menu_item(item_id):
    item = MenuItem.query.get_or_404(item_id)
    data = request.get_json()
    try:
        item.category_id = data.get("category_id", item.category_id)
        item.name = data.get("name", item.name)
        item.description = data.get("description", item.description)
        item.price = data.get("price", item.price)
        item.image_url = data.get("image_url", item.image_url)
        item.is_available = data.get("is_available", item.is_available)
        item.preparation_time_minutes = data.get("preparation_time_minutes", item.preparation_time_minutes)
        item.calories = data.get("calories", item.calories)
        db.session.commit()
        return jsonify({"id": item.id, "message": "Menu item updated"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error updating menu item", "error": str(e)}), 500

@admin_bp.route("/menu-items/<int:item_id>", methods=["DELETE"])
@admin_required
def delete_menu_item(item_id):
    item = MenuItem.query.get_or_404(item_id)
    try:
        db.session.delete(item)
        db.session.commit()
        return jsonify({"message": "Menu item deleted"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error deleting menu item", "error": str(e)}), 500

# Order Management (Admin)
@admin_bp.route("/orders", methods=["GET"])
@admin_required
def get_all_orders_admin():
    # Add pagination and filtering later if needed
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return jsonify([{
        "id": order.id, "user_id": order.user_id, "user_email": order.user.email, 
        "total_amount": str(order.total_amount), "status": order.status, 
        "payment_status": order.payment_status, "created_at": order.created_at.isoformat()
    } for order in orders]), 200

@admin_bp.route("/orders/<int:order_id>", methods=["GET"])
@admin_required
def get_order_details_admin(order_id):
    order = Order.query.get_or_404(order_id)
    # Similar to user-facing GET order details, but for admin
    order_details = {
            "id": order.id,
            "user_id": order.user_id,
            "user_info": {"email": order.user.email, "full_name": order.user.full_name, "phone": order.user.phone_number},
            "total_amount": str(order.total_amount),
            "status": order.status,
            "payment_status": order.payment_status,
            "payment_method": order.payment_method,
            "delivery_instructions": order.delivery_instructions,
            "estimated_delivery_time": order.estimated_delivery_time.isoformat() if order.estimated_delivery_time else None,
            "created_at": order.created_at.isoformat(),
            "updated_at": order.updated_at.isoformat(),
            "delivery_address": {
                "address_line1": order.delivery_address.address_line1,
                "address_line2": order.delivery_address.address_line2,
                "city": order.delivery_address.city,
                "postal_code": order.delivery_address.postal_code,
                "country": order.delivery_address.country
            },
            "order_items": [{
                "menu_item_id": oi.menu_item_id,
                "menu_item_name": oi.menu_item.name,
                "quantity": oi.quantity,
                "price_at_order": str(oi.price_at_order),
                "subtotal": str(oi.subtotal)
            } for oi in order.order_items]
        }
    return jsonify(order_details), 200

@admin_bp.route("/orders/<int:order_id>/status", methods=["PUT"])
@admin_required
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    data = request.get_json()
    new_status = data.get("status")
    allowed_statuses = ["pending", "confirmed", "preparing", "out_for_delivery", "delivered", "cancelled"]
    if new_status not in allowed_statuses:
        return jsonify({"message": f"Invalid status. Allowed: {', '.join(allowed_statuses)}"}), 400
    try:
        order.status = new_status
        # Potentially update payment_status if order is cancelled and payment was made (needs refund logic)
        if new_status == "delivered" and order.payment_method == "cash_on_delivery":
            order.payment_status = "paid"
            # Create payment record for COD if not already done
            if not order.payment:
                cod_payment = Payment(
                    order_id=order.id,
                    amount=order.total_amount,
                    payment_gateway_transaction_id=f"COD_{order.id}",
                    status="success",
                    payment_method_details={"method": "cash_on_delivery"}
                )
                db.session.add(cod_payment)

        db.session.commit()
        return jsonify({"id": order.id, "status": order.status, "message": "Order status updated"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error updating order status", "error": str(e)}), 500

# User Management (Admin)
@admin_bp.route("/users", methods=["GET"])
@admin_required # Potentially only for "admin" role, not "staff"
def get_all_users():
    # Add check for "admin" role specifically if needed
    # current_user_id = get_jwt_identity()
    # user = User.query.get(current_user_id)
    # if user.role != "admin":
    #     return jsonify({"message": "Super admins only!"}), 403
        
    users = User.query.all()
    return jsonify([{
        "id": u.id, "username": u.username, "email": u.email, 
        "full_name": u.full_name, "phone_number": u.phone_number, "role": u.role, 
        "created_at": u.created_at.isoformat()
    } for u in users]), 200

@admin_bp.route("/users/<int:user_id>/role", methods=["PUT"])
@admin_required # Potentially only for "admin" role
def update_user_role(user_id):
    # Add check for "admin" role specifically if needed
    user_to_update = User.query.get_or_404(user_id)
    data = request.get_json()
    new_role = data.get("role")
    allowed_roles = ["customer", "staff", "admin"]
    if new_role not in allowed_roles:
        return jsonify({"message": f"Invalid role. Allowed: {', '.join(allowed_roles)}"}), 400
    try:
        user_to_update.role = new_role
        db.session.commit()
        return jsonify({"id": user_to_update.id, "role": user_to_update.role, "message": "User role updated"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error updating user role", "error": str(e)}), 500

# Restaurant Info Management (Admin)
@admin_bp.route("/restaurant-info", methods=["GET"])
# No auth needed for GET, or use @jwt_required() if some info is sensitive
def get_restaurant_info():
    info = RestaurantInfo.query.first() # Assuming single restaurant
    if not info:
        # Create a default one if it doesn't exist
        info = RestaurantInfo(name="My Restaurant")
        db.session.add(info)
        db.session.commit()
    return jsonify({
        "id": info.id, "name": info.name, "address": info.address, "phone_number": info.phone_number,
        "email": info.email, "logo_url": info.logo_url, "operating_hours": info.operating_hours,
        "delivery_zones": info.delivery_zones
    }), 200

@admin_bp.route("/restaurant-info", methods=["PUT"])
@admin_required # Only admins should update this
def update_restaurant_info():
    info = RestaurantInfo.query.first()
    if not info:
        return jsonify({"message": "Restaurant info not found. Initialize first?"}), 404 # Should not happen if GET creates it
    
    data = request.get_json()
    try:
        info.name = data.get("name", info.name)
        info.address = data.get("address", info.address)
        info.phone_number = data.get("phone_number", info.phone_number)
        info.email = data.get("email", info.email)
        info.logo_url = data.get("logo_url", info.logo_url)
        info.operating_hours = data.get("operating_hours", info.operating_hours) # Expects JSON
        info.delivery_zones = data.get("delivery_zones", info.delivery_zones) # Expects JSON
        db.session.commit()
        return jsonify({"id": info.id, "message": "Restaurant info updated"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error updating restaurant info", "error": str(e)}), 500

# Delivery logic is mostly part of order status updates ("out_for_delivery", "delivered")
# More complex delivery (driver assignment, live tracking) is out of scope for this initial build
# but could be added as a separate module/microservice later.

