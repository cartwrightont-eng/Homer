from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity

import models
from utils import parse_json_request, require_enum, require_fields, sanitize_fields, role_required

bp = Blueprint("verification", __name__)


@bp.route("/verification/submit", methods=["POST"])
@role_required("user", "landlord", "service_provider")
def submit_verification():
    user_id = int(get_jwt_identity())
    data, error = parse_json_request()
    if error:
        return error

    sanitized = sanitize_fields(data, {"doc_type": 50, "file_url": 2048})
    sanitized["accommodation_id"] = data.get("accommodation_id")

    valid_types = {"national_id", "business_permit", "title_deed", "kra_pin", "other"}
    if error := require_fields(sanitized, ["doc_type", "file_url"]):
        return error
    if error := require_enum(sanitized["doc_type"], valid_types, "doc_type"):
        return error
    result = models.submit_verification_document(user_id, sanitized["doc_type"], sanitized["file_url"], sanitized.get("accommodation_id"))
    return jsonify(dict(result)), 201


@bp.route("/verification/status", methods=["GET"])
@role_required("user", "landlord", "service_provider")
def verification_status():
    user_id = int(get_jwt_identity())
    return jsonify(models.get_user_verification_status(user_id)), 200


@bp.route("/verification/<int:doc_id>/review", methods=["PATCH"])
@role_required("admin")
def review_document(doc_id):
    data, error = parse_json_request()
    if error:
        return error

    if error := require_fields(data, ["status"]):
        return error
    if error := require_enum(data["status"], {"approved", "rejected"}, "status"):
        return error
    result = models.admin_review_document(doc_id, status, data.get("rejection_reason"))
    return jsonify(dict(result)), 200
