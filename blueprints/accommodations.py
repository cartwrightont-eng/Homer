from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

import models
from utils import parse_json_request, require_enum, require_fields, sanitize_fields, role_required

bp = Blueprint("accommodations", __name__)


@bp.route("/accommodations", methods=["GET"])
def list_accommodations():
    filters = {
        "listing_type": request.args.get("listing_type"),
        "min_price": request.args.get("min_price"),
        "max_price": request.args.get("max_price"),
        "location": request.args.get("location"),
    }
    accs = models.get_all_accommodations(filters)
    return jsonify([dict(a) for a in accs]), 200


@bp.route("/accommodations/matched", methods=["GET"])
@role_required("user")
def matched_accommodations():
    user_id = int(get_jwt_identity())
    accs = models.get_matched_accommodations(user_id)
    return jsonify([dict(a) for a in accs]), 200


@bp.route("/accommodations/<int:acc_id>", methods=["GET"])
def get_accommodation(acc_id):
    acc = models.get_accommodation_by_id(acc_id)
    if not acc:
        return jsonify({"error": "Not found"}), 404
    data = dict(acc)
    data["photos"] = [dict(photo) for photo in (acc.get("photos") or [])]
    data["amenities"] = [dict(amenity) for amenity in (acc.get("amenities") or [])]
    return jsonify(data), 200


@bp.route("/accommodations/landlord", methods=["GET"])
@role_required("landlord", "admin")
def landlord_accommodations():
    user_id = int(get_jwt_identity())
    accs = models.get_landlord_accommodations(user_id)
    return jsonify([dict(a) for a in accs]), 200


@bp.route("/accommodations", methods=["POST"])
@role_required("landlord")
def create_accommodation():
    user_id = int(get_jwt_identity())
    data, error = parse_json_request()
    if error:
        return error

    sanitized = sanitize_fields(data, {
        "name": 150,
        "description": 2000,
        "location": 255,
        "price": None,
        "latitude": None,
        "longitude": None,
    })
    sanitized["price"] = data.get("price")
    sanitized["latitude"] = data.get("latitude")
    sanitized["longitude"] = data.get("longitude")

    if error := require_fields(sanitized, ["name", "description", "price", "location"]):
        return error
    acc = models.create_accommodation(user_id, sanitized)
    return jsonify(dict(acc)), 201


@bp.route("/accommodations/<int:acc_id>/status", methods=["PATCH"])
@role_required("admin")
def update_accommodation_status(acc_id):
    data, error = parse_json_request()
    if error:
        return error

    if error := require_fields(data, ["status"]):
        return error
    if error := require_enum(data["status"], {"available", "pending", "approved", "rejected", "archived"}, "status"):
        return error
    result = models.update_accommodation_status(acc_id, data["status"])
    return jsonify({"updated": bool(result)}), 200
