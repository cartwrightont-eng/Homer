from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity

import models
from utils import role_required

bp = Blueprint("favourites", __name__)


@bp.route("/favourites", methods=["GET"])
@role_required("user")
def get_favourites():
    user_id = int(get_jwt_identity())
    return jsonify([dict(favourite) for favourite in models.get_user_favourites(user_id)]), 200


@bp.route("/favourites/<int:acc_id>", methods=["POST"])
@role_required("user")
def add_favourite(acc_id):
    user_id = int(get_jwt_identity())
    result = models.add_favourite(user_id, acc_id)
    return jsonify({"added": bool(result)}), 200


@bp.route("/favourites/<int:acc_id>", methods=["DELETE"])
@role_required("user")
def remove_favourite(acc_id):
    user_id = int(get_jwt_identity())
    result = models.remove_favourite(user_id, acc_id)
    return jsonify({"removed": bool(result)}), 200
