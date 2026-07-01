from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity

import models
from utils import parse_json_request, require_enum, require_fields, role_required

bp = Blueprint("applications", __name__)


@bp.route("/applications", methods=["POST"])
@role_required("user")
def apply_for_accommodation():
    user_id = int(get_jwt_identity())
    data, error = parse_json_request()
    if error:
        return error

    if error := require_fields(data, ["accommodation_id"]):
        return error
    result = models.create_application(user_id, data["accommodation_id"], data.get("message", ""))
    return jsonify(dict(result) if result else {"error": "Already applied"}), 200 if result else 409


@bp.route("/applications", methods=["GET"])
@role_required("user")
def my_applications():
    user_id = int(get_jwt_identity())
    apps = models.get_user_applications(user_id)
    return jsonify([dict(a) for a in apps]), 200


@bp.route("/applications/<int:app_id>/status", methods=["PATCH"])
@role_required("landlord")
def update_application(app_id):
    user_id = int(get_jwt_identity())
    data, error = parse_json_request()
    if error:
        return error

    if error := require_fields(data, ["status"]):
        return error
    if error := require_enum(data["status"], {"approved", "rejected", "active"}, "status"):
        return error
    result = models.update_application_status(app_id, data["status"], user_id)
    if not result:
        return jsonify({"error": "Not found or not authorised"}), 404
    return jsonify(dict(result)), 200


@bp.route("/tenancy", methods=["GET"])
@role_required("user")
def active_tenancy():
    user_id = int(get_jwt_identity())
    tenancy = models.get_active_tenancy(user_id)
    return jsonify(dict(tenancy) if tenancy else {}), 200
