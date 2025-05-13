# backend_app/src/routes/addresses.py

from flask import Blueprint, request, jsonify
from ..extensions import db
from ..models.models import Address, User
from flask_jwt_extended import jwt_required, get_jwt_identity

addresses_bp = Blueprint("addresses_bp", __name__)

@addresses_bp.route("/addresses", methods=["POST"])
@jwt_required()
def add_address():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    try:
        new_address = Address(
            user_id=current_user_id,
            address_line1=data.get("address_line1"),
            address_line2=data.get("address_line2"),
            city=data.get("city"),
            postal_code=data.get("postal_code"),
            country=data.get("country"),
            is_default=data.get("is_default", False)
        )
        if not new_address.address_line1 or not new_address.city or not new_address.postal_code or not new_address.country:
            return jsonify({"message": "Missing required address fields"}), 400

        # If this address is set as default, unset other defaults for this user
        if new_address.is_default:
            Address.query.filter_by(user_id=current_user_id, is_default=True).update({"is_default": False})

        db.session.add(new_address)
        db.session.commit()
        return jsonify({
            "id": new_address.id,
            "user_id": new_address.user_id,
            "address_line1": new_address.address_line1,
            "city": new_address.city,
            "is_default": new_address.is_default
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error adding address", "error": str(e)}), 500

@addresses_bp.route("/addresses", methods=["GET"])
@jwt_required()
def get_addresses():
    current_user_id = get_jwt_identity()
    try:
        addresses = Address.query.filter_by(user_id=current_user_id).order_by(Address.is_default.desc(), Address.created_at.desc()).all()
        return jsonify([{
            "id": addr.id,
            "user_id": addr.user_id,
            "address_line1": addr.address_line1,
            "address_line2": addr.address_line2,
            "city": addr.city,
            "postal_code": addr.postal_code,
            "country": addr.country,
            "is_default": addr.is_default
        } for addr in addresses]), 200
    except Exception as e:
        return jsonify({"message": "Error fetching addresses", "error": str(e)}), 500

@addresses_bp.route("/addresses/<int:address_id>", methods=["PUT"])
@jwt_required()
def update_address(address_id):
    current_user_id = get_jwt_identity()
    address = Address.query.filter_by(id=address_id, user_id=current_user_id).first()
    if not address:
        return jsonify({"message": "Address not found or access denied"}), 404

    data = request.get_json()
    try:
        address.address_line1 = data.get("address_line1", address.address_line1)
        address.address_line2 = data.get("address_line2", address.address_line2)
        address.city = data.get("city", address.city)
        address.postal_code = data.get("postal_code", address.postal_code)
        address.country = data.get("country", address.country)
        is_default_update = data.get("is_default")

        if is_default_update is not None and is_default_update and not address.is_default:
            Address.query.filter_by(user_id=current_user_id, is_default=True).update({"is_default": False})
            address.is_default = True
        elif is_default_update is not None:
            address.is_default = is_default_update

        db.session.commit()
        return jsonify({"message": "Address updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error updating address", "error": str(e)}), 500

@addresses_bp.route("/addresses/<int:address_id>", methods=["DELETE"])
@jwt_required()
def delete_address(address_id):
    current_user_id = get_jwt_identity()
    address = Address.query.filter_by(id=address_id, user_id=current_user_id).first()
    if not address:
        return jsonify({"message": "Address not found or access denied"}), 404
    
    try:
        if address.is_default:
             # Prevent deleting default if it's the only address, or handle by setting another as default
            other_addresses = Address.query.filter(Address.user_id == current_user_id, Address.id != address_id).count()
            if other_addresses == 0:
                # Or, allow deletion and remove default status. For now, prevent.
                # return jsonify({"message": "Cannot delete the only default address. Set another address as default first or update this one."}), 400
                pass # Allow deletion, default status will be gone.

        db.session.delete(address)
        db.session.commit()
        return jsonify({"message": "Address deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error deleting address", "error": str(e)}), 500

@addresses_bp.route("/addresses/<int:address_id>/default", methods=["PUT"])
@jwt_required()
def set_default_address(address_id):
    current_user_id = get_jwt_identity()
    address_to_set_default = Address.query.filter_by(id=address_id, user_id=current_user_id).first()

    if not address_to_set_default:
        return jsonify({"message": "Address not found or access denied"}), 404

    try:
        # Unset any other default addresses for this user
        Address.query.filter_by(user_id=current_user_id, is_default=True).update({"is_default": False})
        # Set the new default address
        address_to_set_default.is_default = True
        db.session.commit()
        return jsonify({"message": "Address set as default successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error setting default address", "error": str(e)}), 500

