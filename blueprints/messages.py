from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required

import models
from utils import parse_json_request, require_fields, role_required

bp = Blueprint("messages", __name__)


@bp.route("/conversations", methods=["GET"])
@jwt_required()
def list_conversations():
    user_id = int(get_jwt_identity())
    role = get_jwt().get("role")
    convos = models.get_user_conversations(user_id, role)
    return jsonify([dict(c) for c in convos]), 200


@bp.route("/conversations", methods=["POST"])
@role_required("user")
def start_conversation():
    user_id = int(get_jwt_identity())
    data, error = parse_json_request()
    if error:
        return error

    if error := require_fields(data, ["landlord_id", "accommodation_id"]):
        return error
    convo = models.get_or_create_conversation(user_id, data["landlord_id"], data["accommodation_id"])
    return jsonify(dict(convo)), 200


@bp.route("/conversations/<int:convo_id>/messages", methods=["GET"])
@jwt_required()
def get_messages(convo_id):
    user_id = int(get_jwt_identity())
    convo = models.get_conversation_messages(convo_id, user_id)
    if not convo:
        return jsonify({"error": "Not found"}), 404
    data = dict(convo)
    data["messages"] = [dict(message) for message in (convo.get("messages") or [])]
    return jsonify(data), 200


@bp.route("/conversations/<int:convo_id>/messages", methods=["POST"])
@jwt_required()
def send_message(convo_id):
    user_id = int(get_jwt_identity())
    data, error = parse_json_request()
    if error:
        return error

    if error := require_fields(data, ["content"]):
        return error
    msg = models.send_message(convo_id, user_id, data["content"])
    return jsonify(dict(msg)), 201
