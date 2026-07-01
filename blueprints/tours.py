from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt, get_jwt_identity

import models
from utils import parse_json_request, require_fields, require_enum, role_required

bp = Blueprint("tours", __name__)


@bp.route("/tours", methods=["POST"])
@role_required("user")
def book_tour():
    user_id = int(get_jwt_identity())
    data, error = parse_json_request()
    if error:
        return error

    required = ["accommodation_id", "tour_type", "scheduled_at"]
    if error := require_fields(data, required):
        return error
    if error := require_enum(data["tour_type"], {"physical", "virtual"}, "tour_type"):
        return error
    result = models.book_tour(user_id, data["accommodation_id"], data["tour_type"], data["scheduled_at"])
    return jsonify(dict(result)), 201


@bp.route("/tours", methods=["GET"])
@role_required("user")
def list_tours():
    user_id = int(get_jwt_identity())
    role = get_jwt().get("role")
    if role == "landlord":
        tours = models.get_landlord_tours(user_id)
    else:
        tours = models.get_user_tours(user_id)
    return jsonify([dict(t) for t in tours]), 200
