# backend_app/src/routes/orders.py

from flask import Blueprint, request, jsonify
from ..extensions import db
from ..models.models import Order, OrderItem, MenuItem, Address, User
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError
from datetime import datetime

orders_bp = Blueprint("orders_bp", __name__)

@orders_bp.route("/orders", methods=["POST"])
@jwt_required()
def create_order():
    current_user_id = get_jwt_identity()
    data = request.get_json()

    delivery_address_id = data.get("delivery_address_id")
    payment_method = data.get("payment_method", "cash_on_delivery") # Default or from request
    delivery_instructions = data.get("delivery_instructions")
    items_data = data.get("items") # Expected: [{"menu_item_id": 1, "quantity": 2}, ...]

    if not delivery_address_id or not items_data:
        return jsonify({"message": "Delivery address and items are required"}), 400

    # Verify address belongs to user
    address = Address.query.filter_by(id=delivery_address_id, user_id=current_user_id).first()
    if not address:
        return jsonify({"message": "Delivery address not found or does not belong to user"}), 404

    total_amount = 0
    order_items_to_create = []

    try:
        for item_data in items_data:
            menu_item_id = item_data.get("menu_item_id")
            quantity = item_data.get("quantity")

            if not menu_item_id or not quantity or int(quantity) <= 0:
                return jsonify({"message": "Invalid menu item ID or quantity"}), 400

            menu_item = MenuItem.query.filter_by(id=menu_item_id, is_available=True).first()
            if not menu_item:
                return jsonify({"message": f"Menu item with ID {menu_item_id} not found or not available"}), 404
            
            price_at_order = menu_item.price
            subtotal = price_at_order * int(quantity)
            total_amount += subtotal

            order_item = OrderItem(
                menu_item_id=menu_item_id,
                quantity=int(quantity),
                price_at_order=price_at_order,
                subtotal=subtotal
            )
            order_items_to_create.append(order_item)
        
        if not order_items_to_create:
            return jsonify({"message": "Order must contain at least one item"}), 400

        new_order = Order(
            user_id=current_user_id,
            delivery_address_id=delivery_address_id,
            total_amount=total_amount,
            payment_method=payment_method,
            delivery_instructions=delivery_instructions,
            status=\"pending\", # Initial status
            payment_status=\"pending\" # Initial payment status
        )

        for oi in order_items_to_create:
            new_order.order_items.append(oi)

        db.session.add(new_order)
        db.session.commit()

        # Prepare response (can be more detailed)
        return jsonify({
            "message": "Order created successfully",
            "order_id": new_order.id,
            "total_amount": str(new_order.total_amount),
            "status": new_order.status,
            "items_count": len(new_order.order_items)
        }), 201

    except IntegrityError as e:
        db.session.rollback()
        return jsonify({"message": "Database integrity error, possibly invalid foreign key", "error": str(e)}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error creating order", "error": str(e)}), 500

@orders_bp.route("/orders", methods=["GET"])
@jwt_required()
def get_user_orders():
    current_user_id = get_jwt_identity()
    try:
        orders = Order.query.filter_by(user_id=current_user_id).order_by(Order.created_at.desc()).all()
        orders_list = []
        for order in orders:
            orders_list.append({
                "id": order.id,
                "total_amount": str(order.total_amount),
                "status": order.status,
                "payment_status": order.payment_status,
                "created_at": order.created_at.isoformat(),
                "items_preview": [{"name": oi.menu_item.name, "quantity": oi.quantity} for oi in order.order_items[:2]] # Preview first 2 items
            })
        return jsonify(orders_list), 200
    except Exception as e:
        return jsonify({"message": "Error fetching orders", "error": str(e)}), 500

@orders_bp.route("/orders/<int:order_id>", methods=["GET"])
@jwt_required()
def get_order_details(order_id):
    current_user_id = get_jwt_identity()
    try:
        order = Order.query.filter_by(id=order_id, user_id=current_user_id).first()
        if not order:
            return jsonify({"message": "Order not found or access denied"}), 404

        order_details = {
            "id": order.id,
            "user_id": order.user_id,
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
    except Exception as e:
        return jsonify({"message": "Error fetching order details", "error": str(e)}), 500

@orders_bp.route("/orders/<int:order_id>/cancel", methods=["POST"])
@jwt_required()
def cancel_order(order_id):
    current_user_id = get_jwt_identity()
    try:
        order = Order.query.filter_by(id=order_id, user_id=current_user_id).first()
        if not order:
            return jsonify({"message": "Order not found or access denied"}), 404

        # Define cancellable statuses
        cancellable_statuses = ["pending", "confirmed"]
        if order.status not in cancellable_statuses:
            return jsonify({"message": f"Order cannot be cancelled. Current status: {order.status}"}), 400

        order.status = "cancelled"
        # Potentially, also update payment_status if applicable (e.g., to "refund_pending" or "cancelled")
        db.session.commit()
        return jsonify({"message": "Order cancelled successfully", "order_id": order.id, "new_status": order.status}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error cancelling order", "error": str(e)}), 500

# Admin routes for orders will be in a separate admin blueprint.

