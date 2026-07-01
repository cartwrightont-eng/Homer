from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity

import models
from utils import json_error, parse_json_request, require_fields, role_required

bp = Blueprint("payments", __name__)


@bp.route("/payments/rent", methods=["POST"])
@role_required("user")
def pay_rent():
    user_id = int(get_jwt_identity())
    data, error = parse_json_request()
    if error:
        return error

    if error := require_fields(data, ["accommodation_id", "amount"]):
        return error
    is_first = data.get("is_first_payment", False)
    try:
        amount = float(data["amount"])
    except (TypeError, ValueError):
        return json_error("amount must be numeric", 400)
    surcharge = round(amount * 0.02, 2) if is_first else 0
    result = models.create_payment(user_id, data["accommodation_id"], amount, "rent", surcharge)
    return jsonify(dict(result)), 201


@bp.route("/payments/accommodation/<int:acc_id>", methods=["GET"])
@role_required("landlord")
def accommodation_payments(acc_id):
    user_id = int(get_jwt_identity())
    payments = models.get_payments_for_accommodation(acc_id, user_id)
    return jsonify([dict(p) for p in payments]), 200


@bp.route("/wallet", methods=["GET"])
@role_required("landlord", "service_provider")
def get_wallet():
    user_id = int(get_jwt_identity())
    wallet = models.get_wallet(user_id)
    data = dict(wallet)
    data["transactions"] = [dict(t) for t in (wallet.get("transactions") or [])]
    return jsonify(data), 200
