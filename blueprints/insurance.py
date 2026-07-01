from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity

import models
from utils import json_error, parse_json_request, require_fields, role_required

bp = Blueprint("insurance", __name__)


@bp.route("/insurance/tiers", methods=["GET"])
def insurance_tiers():
    return jsonify(models.INSURANCE_TIERS), 200


@bp.route("/insurance/subscribe", methods=["POST"])
@role_required("user")
def subscribe_insurance():
    user_id = int(get_jwt_identity())
    data, error = parse_json_request()
    if error:
        return error

    if error := require_fields(data, ["tier"]):
        return error
    try:
        policy = models.subscribe_insurance(user_id, data["tier"])
        return jsonify(dict(policy)), 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@bp.route("/insurance/policy", methods=["GET"])
@role_required("user")
def my_insurance():
    user_id = int(get_jwt_identity())
    policy = models.get_insurance_policy(user_id)
    return jsonify(dict(policy) if policy else {}), 200


@bp.route("/insurance/coverage", methods=["POST"])
@role_required("user")
def check_coverage():
    user_id = int(get_jwt_identity())
    data, error = parse_json_request()
    if error:
        return error

    if error := require_fields(data, ["bill_amount"]):
        return error
    try:
        bill_amount = float(data["bill_amount"])
    except (TypeError, ValueError):
        return json_error("bill_amount must be numeric", 400)
    result = models.calculate_coverage(user_id, bill_amount)
    return jsonify(result), 200
