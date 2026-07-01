from flask import Blueprint, jsonify
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required

import models
from utils import json_error, parse_json_request, require_enum, require_fields, sanitize_fields, role_required

bp = Blueprint("auth", __name__)


@bp.route("/register", methods=["POST"])
def register():
    data, error = parse_json_request()
    if error:
        return error

    sanitized = sanitize_fields(data, {
        "name": 100,
        "email": 255,
        "password": 128,
        "role": 20,
    })

    required = ["name", "email", "password"]
    if error := require_fields(sanitized, required):
        return error

    role = sanitized.get("role") or "user"
    if error := require_enum(role, {"user", "landlord", "service_provider"}, "role"):
        return error

    try:
        user = models.create_user(data["name"], data["email"], data["password"], role)
        return jsonify({"message": "Account created. Please verify your email.", "user": dict(user)}), 201
    except Exception as exc:
        message = str(exc).lower()
        if "duplicate" in message or "unique" in message:
            return jsonify({"error": "Email already registered"}), 409
        return jsonify({"error": str(exc)}), 500


@bp.route("/login", methods=["POST"])
def login():
    data, error = parse_json_request()
    if error:
        return error

    sanitized = sanitize_fields(data, {"email": 255, "password": 128})
    if error := require_fields(sanitized, ["email", "password"]):
        return error

    user = models.authenticate_user(sanitized.get("email"), sanitized.get("password"))
    if not user:
        return jsonify({"error": "Invalid credentials or unverified email"}), 401

    token = create_access_token(
        identity=str(user["id"]),
        additional_claims={"role": user["role"], "name": user["name"]},
    )
    return jsonify({
        "access_token": token,
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "role": user["role"],
        },
    }), 200


@bp.route("/profile", methods=["GET"])
@jwt_required()
def get_profile():
    user_id = int(get_jwt_identity())
    user = models.get_user_by_id(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(dict(user)), 200


@bp.route("/profile", methods=["PATCH"])
@jwt_required()
def update_profile():
    user_id = int(get_jwt_identity())
    data, error = parse_json_request()
    if error:
        return error

    result = models.update_user_profile(user_id, data)
    return jsonify({"updated": bool(result)}), 200
