from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity

import models
from utils import parse_json_request, require_fields, sanitize_string, role_required

bp = Blueprint("photos", __name__)


@bp.route("/accommodations/<int:acc_id>/photos", methods=["GET"])
def get_photos(acc_id):
    photos = models.get_accommodation_photos(acc_id)
    return jsonify(photos), 200


@bp.route("/accommodations/<int:acc_id>/photos", methods=["POST"])
@role_required("landlord", "admin")
def add_photo(acc_id):
    user_id = int(get_jwt_identity())
    data, error = parse_json_request()
    if error:
        return error

    if error := require_fields(data, ["photo_url"]):
        return error
    photo_url = sanitize_string(data["photo_url"], max_length=2048)
    if not photo_url:
        return jsonify({"error": "photo_url is required"}), 400
    sort_order = data.get("sort_order", 0)
    photo_id = models.add_accommodation_photo(acc_id, photo_url, sort_order)
    return jsonify({"id": photo_id, "photo_url": photo_url}), 201


@bp.route("/photos/<int:photo_id>", methods=["DELETE"])
@role_required("landlord", "admin")
def delete_photo(photo_id):
    user_id = int(get_jwt_identity())
    result = models.delete_accommodation_photo(photo_id, user_id)
    if not result:
        return jsonify({"error": "Photo not found or unauthorized"}), 404
    return jsonify({"deleted": True}), 200
