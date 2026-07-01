from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required

import models
from utils import json_error, parse_json_request, require_fields, require_enum, sanitize_fields, role_required

bp = Blueprint("jobs", __name__)


@bp.route("/jobs", methods=["POST"])
@role_required("user")
def create_job():
    user_id = int(get_jwt_identity())
    data, error = parse_json_request()
    if error:
        return error

    sanitized = sanitize_fields(data, {
        "category": 100,
        "description": 2000,
        "address": 300,
        "urgency": 20,
        "job_type": 50,
    })
    sanitized["accommodation_id"] = data.get("accommodation_id")
    sanitized["lat"] = data.get("lat")
    sanitized["lng"] = data.get("lng")

    if error := require_fields(sanitized, ["category", "description"]):
        return error
    result = models.create_job(
        user_id,
        sanitized["category"],
        sanitized["description"],
        address=sanitized.get("address"),
        urgency=sanitized.get("urgency", "normal"),
        accommodation_id=sanitized.get("accommodation_id"),
        lat=sanitized.get("lat"),
        lng=sanitized.get("lng"),
    )
    return jsonify(dict(result)), 201


@bp.route("/providers/online", methods=["PATCH"])
@role_required("service_provider")
def toggle_provider_online():
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
def category_price_range(category):
    result = models.get_category_price_range(category)
    return jsonify(dict(result) if result else {}), 200


@bp.route("/jobs/<int:job_id>/accept", methods=["POST"])
@role_required("service_provider")
def accept_job(job_id):
    user_id = int(get_jwt_identity())
    result = models.accept_job(job_id, user_id)
    if not result:
        return jsonify({"error": "Job not available or already taken"}), 404
    return jsonify(dict(result)), 200


@bp.route("/jobs/open", methods=["GET"])
@role_required("service_provider")
def open_jobs():
    category = request.args.get("category")
    lat = request.args.get("lat", type=float)
    lng = request.args.get("lng", type=float)
    jobs = models.get_open_jobs(category, provider_lat=lat, provider_lng=lng)
    return jsonify(jobs), 200


@bp.route("/jobs", methods=["GET"])
@jwt_required()
def list_jobs():
    user_id = int(get_jwt_identity())
    role = get_jwt().get("role")
    if role == "service_provider":
        jobs = models.get_provider_jobs(user_id)
    else:
        jobs = models.get_tenant_jobs(user_id)
    return jsonify([dict(j) for j in jobs]), 200


@bp.route("/jobs/<int:job_id>/seen", methods=["PATCH"])
@role_required("service_provider")
def mark_job_seen(job_id):
    user_id = int(get_jwt_identity())
    result = models.mark_job_seen(job_id, user_id)
    if not result:
        return jsonify({"error": "Not found or not authorised"}), 404
    return jsonify({"marked_seen": True}), 200


@bp.route("/jobs/<int:job_id>/status", methods=["PATCH"])
@role_required("service_provider")
def update_job_status(job_id):
    user_id = int(get_jwt_identity())
    data, error = parse_json_request()
    if error:
        return error

    valid = ("pending", "accepted", "en_route", "arrived", "in_progress", "completed", "cancelled")
    if error := require_fields(data, ["status"]):
        return error
    if error := require_enum(data["status"], set(valid), "status"):
        return error
    result = models.update_job_status(job_id, data["status"], user_id)
    if not result:
        return jsonify({"error": "Not found or not authorised"}), 404
    return jsonify(dict(result)), 200


@bp.route("/providers/category/<category>", methods=["GET"])
def providers_by_category(category):
    providers = models.get_providers_by_category(category)
    return jsonify([dict(p) for p in providers]), 200


@bp.route("/providers/<int:provider_user_id>/services", methods=["GET"])
def provider_services(provider_user_id):
    sp = models.get_provider_by_user_id(provider_user_id)
    if not sp:
        return jsonify({"error": "Not found"}), 404
    services = models.get_provider_services(sp["id"])
    return jsonify([dict(s) for s in services]), 200


@bp.route("/jobs/book", methods=["POST"])
@role_required("user")
def book_job():
    user_id = int(get_jwt_identity())
    data, error = parse_json_request()
    if error:
        return error

    sanitized = sanitize_fields(data, {
        "service_name": 150,
        "description": 2000,
        "address": 300,
        "urgency": 20,
        "job_type": 50,
    })
    sanitized["provider_user_id"] = data.get("provider_user_id")

    required = ["provider_user_id", "service_name", "description", "job_type"]
    if error := require_fields(sanitized, required):
        return error
    result = models.create_job_with_provider(
        user_id,
        sanitized["provider_user_id"],
        sanitized["service_name"],
        sanitized["description"],
        sanitized.get("address", ""),
        sanitized.get("urgency", "normal"),
        sanitized["job_type"],
    )
    if not result:
        return jsonify({"error": "Provider not found"}), 404
    return jsonify(dict(result)), 201


@bp.route("/jobs/<int:job_id>/quote", methods=["POST"])
@role_required("service_provider")
def send_quote(job_id):
    user_id = int(get_jwt_identity())
    data, error = parse_json_request()
    if error:
        return error

    if error := require_fields(data, ["amount"]):
        return error
    result = models.submit_quote(job_id, user_id, data["amount"])
    if not result:
        return jsonify({"error": "Not found or not authorised"}), 404
    return jsonify(dict(result)), 200


@bp.route("/jobs/<int:job_id>/quote/accept", methods=["PATCH"])
@role_required("user")
def accept_quote(job_id):
    user_id = int(get_jwt_identity())
    result = models.accept_quote(job_id, user_id)
    if not result:
        return jsonify({"error": "Not found or quote not sent yet"}), 404
    return jsonify(dict(result)), 200
