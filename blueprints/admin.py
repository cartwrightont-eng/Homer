from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity

import models
from utils import role_required

bp = Blueprint("admin", __name__)


@bp.route("/admin/stats", methods=["GET"])
@role_required("admin")
def admin_stats():
    stats = models.get_platform_stats()
    return jsonify(dict(stats)), 200


@bp.route("/admin/verifications", methods=["GET"])
@role_required("admin")
def pending_verifications():
    docs = models.get_pending_verifications()
    return jsonify([dict(d) for d in docs]), 200


@bp.route("/landlord/analytics", methods=["GET"])
@role_required("landlord", "admin")
def landlord_analytics():
    import json
    from datetime import datetime, date

    user_id = int(get_jwt_identity())
    data = models.get_landlord_analytics(user_id)

    def default(o):
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        raise TypeError

    return jsonify(json.loads(json.dumps(data, default=default))), 200
