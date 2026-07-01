from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity

import models
from utils import parse_json_request, require_fields, sanitize_fields, role_required

bp = Blueprint("providers", __name__)


@bp.route("/providers", methods=["GET"])
def list_providers():
    category = request.args.get("category")
    providers = models.get_service_providers(category=category)
    return jsonify([dict(p) for p in providers]), 200


@bp.route("/providers/profile", methods=["GET"])
@role_required("service_provider")
def my_provider_profile():
    user_id = int(get_jwt_identity())
    profile = models.get_provider_by_user_id(user_id)
    return jsonify(dict(profile) if profile else {}), 200


@bp.route("/providers/profile", methods=["POST"])
@role_required("service_provider")
def upsert_provider_profile():
    user_id = int(get_jwt_identity())
    data, error = parse_json_request()
    if error:
        return error

    sanitized = sanitize_fields(data, {"category": 100})
    if error := require_fields(sanitized, ["category"]):
        return error
    result = models.create_service_provider_profile(user_id, sanitized)
    return jsonify(dict(result)), 200


@bp.route("/providers/location", methods=["POST"])
@role_required("service_provider")
def update_location():
    user_id = int(get_jwt_identity())
    data, error = parse_json_request()
    if error:
        return error

    if error := require_fields(data, ["lat", "lng"]):
        return error
    models.update_provider_location(user_id, data["lat"], data["lng"])
    return jsonify({"updated": True}), 200


@bp.route("/providers/online", methods=["PATCH"])
@role_required("service_provider")
def toggle_online():
    user_id = int(get_jwt_identity())
    data, error = parse_json_request()
    if error:
        return error
    is_online = bool(data.get("is_online", False))
    result = models.set_provider_online(user_id, is_online)
    if not result:
        return jsonify({"error": "Provider profile not found"}), 404
    return jsonify(dict(result)), 200


@bp.route("/providers/price-range/<category>", methods=["GET"])
def price_range(category):
    result = models.get_category_price_range(category)
    return jsonify(dict(result) if result else {}), 200


@bp.route("/providers/category/<category>", methods=["GET"])
def providers_by_category(category):
    providers = models.get_service_providers(category=category, verified_only=False)
    return jsonify([dict(p) for p in providers]), 200


@bp.route("/providers/<int:provider_user_id>/services", methods=["GET"])
def provider_services(provider_user_id):
    # Returns empty list for now — services table coming in next phase
    return jsonify([]), 200
