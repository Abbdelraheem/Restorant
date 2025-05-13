# backend_app/src/routes/payments.py

from flask import Blueprint, request, jsonify
from ..extensions import db
from ..models.models import Order, Payment # Assuming Payment model is defined
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

payments_bp = Blueprint("payments_bp", __name__)

@payments_bp.route("/payments/initiate", methods=["POST"])
@jwt_required()
def initiate_payment():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    order_id = data.get("order_id")
    # payment_method_details = data.get("payment_method_details") # e.g., card info, etc.

    if not order_id:
        return jsonify({"message": "Order ID is required"}), 400

    order = Order.query.filter_by(id=order_id, user_id=current_user_id).first()
    if not order:
        return jsonify({"message": "Order not found or access denied"}), 404

    if order.payment_status == "paid":
        return jsonify({"message": "Order is already paid"}), 400

    # Simulate payment gateway interaction
    # In a real scenario, you would redirect to a payment gateway or use their SDK
    # For now, let's assume payment is successful for demonstration if payment_method is not cash_on_delivery
    
    transaction_id = f"SIMULATED_TXN_{order_id}_{datetime.utcnow().timestamp()}"
    payment_status_update = "pending" # Default to pending, webhook would update it

    if order.payment_method != "cash_on_delivery":
        # Simulate a successful payment for non-COD orders for now
        payment_status_update = "success"
        order.payment_status = "paid"
        order.status = "confirmed" # Or some other appropriate status after payment
    else:
        # For COD, payment is pending until delivery
        order.payment_status = "pending" # Or could be 'due_on_delivery'
        order.status = "confirmed" # Confirm order even for COD

    try:
        # Create a payment record
        new_payment = Payment(
            order_id=order.id,
            amount=order.total_amount,
            payment_gateway_transaction_id=transaction_id,
            status=payment_status_update, # 'success', 'failed', 'pending'
            payment_method_details=data.get("payment_method_details", {})
        )
        db.session.add(new_payment)
        db.session.commit()

        return jsonify({
            "message": "Payment process initiated",
            "order_id": order.id,
            "payment_id": new_payment.id,
            "transaction_id": transaction_id,
            "payment_status": order.payment_status,
            "order_status": order.status,
            # "payment_url": "https://simulated-payment-gateway.com/pay?txn_id=" + transaction_id # Example
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error initiating payment", "error": str(e)}), 500

@payments_bp.route("/payments/webhook", methods=["POST"])
def payment_webhook():
    # This endpoint would be called by the payment gateway to notify about payment status changes
    # It should be secured (e.g., by checking a signature from the gateway)
    data = request.get_json()
    
    # Example: gateway_transaction_id, status (success, failed), order_id (or some reference)
    gateway_txn_id = data.get("gateway_transaction_id")
    payment_outcome = data.get("status") # e.g., "success", "failure"
    order_reference_id = data.get("order_id") # Assuming gateway sends back our order_id

    if not gateway_txn_id or not payment_outcome or not order_reference_id:
        return jsonify({"message": "Invalid webhook data"}), 400

    payment_record = Payment.query.filter_by(payment_gateway_transaction_id=gateway_txn_id, order_id=order_reference_id).first()
    if not payment_record:
        # Or, if order_id is the primary reference from webhook:
        # order = Order.query.get(order_reference_id)
        # if order and order.payment:
        #    payment_record = order.payment
        # else:
        return jsonify({"message": "Payment record not found for this transaction"}), 404

    order = Order.query.get(payment_record.order_id)
    if not order:
        return jsonify({"message": "Associated order not found"}), 404

    try:
        if payment_outcome == "success":
            payment_record.status = "success"
            order.payment_status = "paid"
            order.status = "confirmed" # Or "preparing" if payment confirmation triggers preparation
            # Potentially trigger other actions: send confirmation email, notify kitchen, etc.
        elif payment_outcome == "failed":
            payment_record.status = "failed"
            order.payment_status = "failed"
            # Potentially trigger other actions: notify user, etc.
        else:
            # Handle other statuses like 'pending', 'cancelled' from gateway if any
            payment_record.status = payment_outcome 

        db.session.commit()
        return jsonify({"message": "Webhook received and processed"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error processing webhook", "error": str(e)}), 500


