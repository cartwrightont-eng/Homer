from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required

import models
from utils import json_error, parse_json_request, require_fields, require_enum, role_required

bp = Blueprint("content", __name__)


@bp.route("/reviews", methods=["POST"])
@jwt_required()
def submit_review():
    user_id = int(get_jwt_identity())
    data, error = parse_json_request()
    if error:
        return error

    required = ["target_id", "target_type", "rating"]
    if error := require_fields(data, required):
        return error
    if error := require_enum(data["target_type"], {"user", "accommodation", "service_provider"}, "target_type"):
        return error
    try:
        rating = float(data["rating"])
    except (TypeError, ValueError):
        return json_error("Rating must be a number between 1 and 5", 400)
    if not 1 <= rating <= 5:
        return json_error("Rating must be 1–5", 400)
    result = models.create_review(user_id, data["target_id"], data["target_type"], rating, data.get("comment", ""))
    return jsonify(dict(result)), 201


@bp.route("/reviews/<target_type>/<int:target_id>", methods=["GET"])
def get_reviews(target_type, target_id):
    if target_type not in ("user", "accommodation", "service_provider"):
        return jsonify({"error": "Invalid target_type"}), 400
    reviews = models.get_reviews(target_id, target_type)
    return jsonify([dict(r) for r in reviews]), 200
