from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_jwt_extended import (
    JWTManager, create_access_token,
    jwt_required, get_jwt_identity, get_jwt,
)
from flask_cors import CORS
from functools import wraps
from datetime import timedelta
import models
from config import JWT_SECRET_KEY

app = Flask(__name__)
limiter = Limiter(get_remote_address, app=app, default_limits=[])
app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=7)
CORS(app, resources={r"/*": {"origins": "*"}})

jwt = JWTManager(app)

# ─────────────────────────────────────────────
#  DECORATORS
# ─────────────────────────────────────────────

def role_required(*roles):
    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            if claims.get("role") not in roles:
                return jsonify({"error": "Forbidden"}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator


# ─────────────────────────────────────────────
#  AUTH
# ─────────────────────────────────────────────

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    required = ["name", "email", "password"]
    if missing := [f for f in required if not data.get(f)]:
        return jsonify({"error": f"Missing: {', '.join(missing)}"}), 400

    role = data.get("role", "user")
    if role not in ("user", "landlord", "service_provider"):
        return jsonify({"error": "Invalid role"}), 400

    try:
        user = models.create_user(
            data["name"], data["email"], data["password"], role
        )
        return jsonify({
            "message": "Account created. Please verify your email.",
            "user": dict(user),
        }), 201
    except Exception as e:
        if "duplicate" in str(e).lower() or "unique" in str(e).lower():
            return jsonify({"error": "Email already registered"}), 409
        return jsonify({"error": str(e)}), 500


@app.route("/login", methods=["POST"])
@limiter.limit("10 per minute")
def login():
    data = request.get_json() or {}
    user = models.authenticate_user(data.get("email"), data.get("password"))
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


@app.route("/profile", methods=["GET"])
@jwt_required()
def get_profile():
    user_id = int(get_jwt_identity())
    user = models.get_user_by_id(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(dict(user)), 200


@app.route("/profile", methods=["PATCH"])
@jwt_required()
def update_profile():
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    result = models.update_user_profile(user_id, data)
    return jsonify({"updated": bool(result)}), 200


# ─────────────────────────────────────────────
#  ACCOMMODATIONS
# ─────────────────────────────────────────────

@app.route("/accommodations", methods=["GET"])
def list_accommodations():
    filters = {
        "listing_type": request.args.get("listing_type"),
        "min_price":    request.args.get("min_price"),
        "max_price":    request.args.get("max_price"),
        "location":     request.args.get("location"),
    }
    accs = models.get_all_accommodations(filters)
    return jsonify([dict(a) for a in accs]), 200


@app.route("/accommodations/matched", methods=["GET"])
@role_required("user")
def matched_accommodations():
    user_id = int(get_jwt_identity())
    accs = models.get_matched_accommodations(user_id)
    return jsonify([dict(a) for a in accs]), 200


@app.route("/accommodations/<int:acc_id>", methods=["GET"])
def get_accommodation(acc_id):
    acc = models.get_accommodation_by_id(acc_id)
    if not acc:
        return jsonify({"error": "Not found"}), 404
    d = dict(acc)
    d["photos"] = [dict(p) for p in (acc.get("photos") or [])]
    d["amenities"] = [dict(a) for a in (acc.get("amenities") or [])]
    return jsonify(d), 200


@app.route("/accommodations/landlord", methods=["GET"])
@role_required("landlord", "admin")
def landlord_accommodations():
    user_id = int(get_jwt_identity())
    accs = models.get_landlord_accommodations(user_id)
    return jsonify([dict(a) for a in accs]), 200


@app.route("/accommodations", methods=["POST"])
@role_required("landlord")
def create_accommodation():
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    # TODO: re-enable verification gate before onboarding real landlords
    # verification = models.get_user_verification_status(user_id)
    # if not verification["fully_verified"]:
    #     return jsonify({
    #         "error": "Account not fully verified. Submit ID, business permit and title deed first.",
    #         "missing": list({"national_id", "business_permit", "title_deed"} - set(verification["approved_types"]))
    #     }), 403
    acc = models.create_accommodation(user_id, data)
    return jsonify(dict(acc)), 201


@app.route("/accommodations/<int:acc_id>/status", methods=["PATCH"])
@role_required("admin")
def update_accommodation_status(acc_id):
    data = request.get_json() or {}
    result = models.update_accommodation_status(acc_id, data.get("status"))
    return jsonify({"updated": bool(result)}), 200


# ─────────────────────────────────────────────
#  FAVOURITES
# ─────────────────────────────────────────────

@app.route("/favourites", methods=["GET"])
@role_required("user")
def get_favourites():
    user_id = int(get_jwt_identity())
    return jsonify([dict(f) for f in models.get_user_favourites(user_id)]), 200


@app.route("/favourites/<int:acc_id>", methods=["POST"])
@role_required("user")
def add_favourite(acc_id):
    user_id = int(get_jwt_identity())
    result = models.add_favourite(user_id, acc_id)
    return jsonify({"added": bool(result)}), 200


@app.route("/favourites/<int:acc_id>", methods=["DELETE"])
@role_required("user")
def remove_favourite(acc_id):
    user_id = int(get_jwt_identity())
    result = models.remove_favourite(user_id, acc_id)
    return jsonify({"removed": bool(result)}), 200


# ─────────────────────────────────────────────
#  APPLICATIONS (tenant pipeline)
# ─────────────────────────────────────────────

@app.route("/applications", methods=["POST"])
@role_required("user")
def apply_for_accommodation():
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    if not data.get("accommodation_id"):
        return jsonify({"error": "accommodation_id required"}), 400
    result = models.create_application(
        user_id, data["accommodation_id"], data.get("message", "")
    )
    return jsonify(dict(result) if result else {"error": "Already applied"}), 200 if result else 409


@app.route("/applications", methods=["GET"])
@role_required("user")
def my_applications():
    user_id = int(get_jwt_identity())
    apps = models.get_user_applications(user_id)
    return jsonify([dict(a) for a in apps]), 200


@app.route("/applications/<int:app_id>/status", methods=["PATCH"])
@role_required("landlord")
def update_application(app_id):
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    status = data.get("status")
    if status not in ("approved", "rejected", "active"):
        return jsonify({"error": "Invalid status"}), 400
    result = models.update_application_status(app_id, status, user_id)
    if not result:
        return jsonify({"error": "Not found or not authorised"}), 404
    return jsonify(dict(result)), 200


@app.route("/tenancy", methods=["GET"])
@role_required("user")
def active_tenancy():
    user_id = int(get_jwt_identity())
    tenancy = models.get_active_tenancy(user_id)
    return jsonify(dict(tenancy) if tenancy else {}), 200


# ─────────────────────────────────────────────
#  PAYMENTS
# ─────────────────────────────────────────────

@app.route("/payments/rent", methods=["POST"])
@role_required("user")
def pay_rent():
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    acc_id = data.get("accommodation_id")
    amount = data.get("amount")
    is_first = data.get("is_first_payment", False)
    if not acc_id or not amount:
        return jsonify({"error": "accommodation_id and amount required"}), 400
    surcharge = round(float(amount) * 0.02, 2) if is_first else 0
    result = models.create_payment(user_id, acc_id, float(amount), "rent", surcharge)
    return jsonify(dict(result)), 201


@app.route("/payments/accommodation/<int:acc_id>", methods=["GET"])
@role_required("landlord")
def accommodation_payments(acc_id):
    user_id = int(get_jwt_identity())
    payments = models.get_payments_for_accommodation(acc_id, user_id)
    return jsonify([dict(p) for p in payments]), 200


# ─────────────────────────────────────────────
#  WALLET (landlord)
# ─────────────────────────────────────────────

@app.route("/wallet", methods=["GET"])
@role_required("landlord", "service_provider")
def get_wallet():
    user_id = int(get_jwt_identity())
    wallet = models.get_wallet(user_id)
    w = dict(wallet)
    w["transactions"] = [dict(t) for t in (wallet.get("transactions") or [])]
    return jsonify(w), 200


# ─────────────────────────────────────────────
#  REVIEWS
# ─────────────────────────────────────────────

@app.route("/reviews", methods=["POST"])
@jwt_required()
def submit_review():
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    required = ["target_id", "target_type", "rating"]
    if missing := [f for f in required if not data.get(f)]:
        return jsonify({"error": f"Missing: {', '.join(missing)}"}), 400
    if data["target_type"] not in ("user", "accommodation", "service_provider"):
        return jsonify({"error": "Invalid target_type"}), 400
    rating = float(data["rating"])
    if not 1 <= rating <= 5:
        return jsonify({"error": "Rating must be 1–5"}), 400
    result = models.create_review(
        user_id, data["target_id"], data["target_type"],
        rating, data.get("comment", "")
    )
    return jsonify(dict(result)), 201


@app.route("/reviews/<target_type>/<int:target_id>", methods=["GET"])
def get_reviews(target_type, target_id):
    if target_type not in ("user", "accommodation", "service_provider"):
        return jsonify({"error": "Invalid target_type"}), 400
    reviews = models.get_reviews(target_id, target_type)
    return jsonify([dict(r) for r in reviews]), 200


# ─────────────────────────────────────────────
#  CHAT
# ─────────────────────────────────────────────

@app.route("/conversations", methods=["GET"])
@jwt_required()
def list_conversations():
    user_id = int(get_jwt_identity())
    role = get_jwt().get("role")
    convos = models.get_user_conversations(user_id, role)
    return jsonify([dict(c) for c in convos]), 200


@app.route("/conversations", methods=["POST"])
@role_required("user")
def start_conversation():
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    if not all([data.get("landlord_id"), data.get("accommodation_id")]):
        return jsonify({"error": "landlord_id and accommodation_id required"}), 400
    convo = models.get_or_create_conversation(
        user_id, data["landlord_id"], data["accommodation_id"]
    )
    return jsonify(dict(convo)), 200


@app.route("/conversations/<int:convo_id>/messages", methods=["GET"])
@jwt_required()
def get_messages(convo_id):
    user_id = int(get_jwt_identity())
    convo = models.get_conversation_messages(convo_id, user_id)
    if not convo:
        return jsonify({"error": "Not found"}), 404
    d = dict(convo)
    d["messages"] = [dict(m) for m in (convo.get("messages") or [])]
    return jsonify(d), 200


@app.route("/conversations/<int:convo_id>/messages", methods=["POST"])
@jwt_required()
def send_message(convo_id):
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    if not data.get("content"):
        return jsonify({"error": "content required"}), 400
    msg = models.send_message(convo_id, user_id, data["content"])
    return jsonify(dict(msg)), 201


# ─────────────────────────────────────────────
#  TOURS
# ─────────────────────────────────────────────

@app.route("/tours", methods=["POST"])
@role_required("user")
def book_tour():
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    required = ["accommodation_id", "tour_type", "scheduled_at"]
    if missing := [f for f in required if not data.get(f)]:
        return jsonify({"error": f"Missing: {', '.join(missing)}"}), 400
    if data["tour_type"] not in ("physical", "virtual"):
        return jsonify({"error": "tour_type must be physical or virtual"}), 400
    result = models.book_tour(
        user_id, data["accommodation_id"],
        data["tour_type"], data["scheduled_at"]
    )
    return jsonify(dict(result)), 201


@app.route("/tours", methods=["GET"])
@jwt_required()
def list_tours():
    user_id = int(get_jwt_identity())
    role = get_jwt().get("role")
    if role == "landlord":
        tours = models.get_landlord_tours(user_id)
    else:
        tours = models.get_user_tours(user_id)
    return jsonify([dict(t) for t in tours]), 200


# ─────────────────────────────────────────────
#  VERIFICATION DOCUMENTS
# ─────────────────────────────────────────────

@app.route("/verification/submit", methods=["POST"])
@jwt_required()
def submit_verification():
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    valid_types = {"national_id", "business_permit", "title_deed", "kra_pin", "other"}
    if data.get("doc_type") not in valid_types:
        return jsonify({"error": f"doc_type must be one of: {', '.join(valid_types)}"}), 400
    if not data.get("file_url"):
        return jsonify({"error": "file_url required"}), 400
    result = models.submit_verification_document(
        user_id, data["doc_type"], data["file_url"],
        data.get("accommodation_id")
    )
    return jsonify(dict(result)), 201


@app.route("/verification/status", methods=["GET"])
@jwt_required()
def verification_status():
    user_id = int(get_jwt_identity())
    return jsonify(models.get_user_verification_status(user_id)), 200


@app.route("/verification/<int:doc_id>/review", methods=["PATCH"])
@role_required("admin")
def review_document(doc_id):
    data = request.get_json() or {}
    status = data.get("status")
    if status not in ("approved", "rejected"):
        return jsonify({"error": "status must be approved or rejected"}), 400
    result = models.admin_review_document(doc_id, status, data.get("rejection_reason"))
    return jsonify(dict(result)), 200


# ─────────────────────────────────────────────
#  SERVICE PROVIDERS
# ─────────────────────────────────────────────

@app.route("/providers", methods=["GET"])
def list_providers():
    category = request.args.get("category")
    providers = models.get_service_providers(category=category)
    return jsonify([dict(p) for p in providers]), 200


@app.route("/providers/profile", methods=["GET"])
@role_required("service_provider")
def my_provider_profile():
    user_id = int(get_jwt_identity())
    profile = models.get_provider_by_user_id(user_id)
    return jsonify(dict(profile) if profile else {}), 200


@app.route("/providers/profile", methods=["POST"])
@role_required("service_provider")
def upsert_provider_profile():
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    if not data.get("category"):
        return jsonify({"error": "category required"}), 400
    result = models.create_service_provider_profile(user_id, data)
    return jsonify(dict(result)), 200


@app.route("/providers/location", methods=["POST"])
@role_required("service_provider")
def update_location():
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    lat, lng = data.get("lat"), data.get("lng")
    if lat is None or lng is None:
        return jsonify({"error": "lat and lng required"}), 400
    models.update_provider_location(user_id, lat, lng)
    return jsonify({"updated": True}), 200


# ─────────────────────────────────────────────
#  HOMERRFIX JOBS
# ─────────────────────────────────────────────

@app.route("/jobs", methods=["POST"])
@role_required("user")
def create_job():
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    if not data.get("category") or not data.get("description"):
        return jsonify({"error": "category and description are required"}), 400
    result = models.create_job(
        user_id,
        data["category"],
        data["description"],
        address=data.get("address"),
        urgency=data.get("urgency", "normal"),
        accommodation_id=data.get("accommodation_id"),
        lat=data.get("lat"),
        lng=data.get("lng"),
    )
    return jsonify(dict(result)), 201


@app.route("/providers/online", methods=["PATCH"])
@role_required("service_provider")
def toggle_provider_online():
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    is_online = bool(data.get("is_online", False))
    result = models.set_provider_online(user_id, is_online)
    if not result:
        return jsonify({"error": "Provider profile not found"}), 404
    return jsonify(dict(result)), 200


@app.route("/providers/price-range/<category>", methods=["GET"])
def category_price_range(category):
    result = models.get_category_price_range(category)
    return jsonify(dict(result) if result else {}), 200


@app.route("/jobs/<int:job_id>/accept", methods=["POST"])
@role_required("service_provider")
def accept_job(job_id):
    user_id = int(get_jwt_identity())
    result = models.accept_job(job_id, user_id)
    if not result:
        return jsonify({"error": "Job not available or already taken"}), 404
    return jsonify(dict(result)), 200


@app.route("/jobs/open", methods=["GET"])
@role_required("service_provider")
def open_jobs():
    category = request.args.get("category")
    lat = request.args.get("lat", type=float)
    lng = request.args.get("lng", type=float)
    jobs = models.get_open_jobs(category, provider_lat=lat, provider_lng=lng)
    return jsonify(jobs), 200


@app.route("/jobs", methods=["GET"])
@jwt_required()
def list_jobs():
    user_id = int(get_jwt_identity())
    role = get_jwt().get("role")
    if role == "service_provider":
        jobs = models.get_provider_jobs(user_id)
    else:
        jobs = models.get_tenant_jobs(user_id)
    return jsonify([dict(j) for j in jobs]), 200


@app.route("/jobs/<int:job_id>/seen", methods=["PATCH"])
@role_required("service_provider")
def mark_job_seen(job_id):
    user_id = int(get_jwt_identity())
    result = models.mark_job_seen(job_id, user_id)
    if not result:
        return jsonify({"error": "Not found or not authorised"}), 404
    return jsonify({"marked_seen": True}), 200


@app.route("/jobs/<int:job_id>/status", methods=["PATCH"])
@role_required("service_provider")
def update_job_status(job_id):
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    valid = ("pending","accepted","en_route","arrived","in_progress","completed","cancelled")
    if data.get("status") not in valid:
        return jsonify({"error": f"Invalid status. Choose: {', '.join(valid)}"}), 400
    result = models.update_job_status(job_id, data["status"], user_id)
    if not result:
        return jsonify({"error": "Not found or not authorised"}), 404
    return jsonify(dict(result)), 200


# ─────────────────────────────────────────────
#  HOMERRINSURANCE
# ─────────────────────────────────────────────

@app.route("/insurance/tiers", methods=["GET"])
def insurance_tiers():
    return jsonify(models.INSURANCE_TIERS), 200


@app.route("/insurance/subscribe", methods=["POST"])
@role_required("user")
def subscribe_insurance():
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    tier = data.get("tier")
    if not tier:
        return jsonify({"error": "tier required"}), 400
    try:
        policy = models.subscribe_insurance(user_id, tier)
        return jsonify(dict(policy)), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.route("/insurance/policy", methods=["GET"])
@role_required("user")
def my_insurance():
    user_id = int(get_jwt_identity())
    policy = models.get_insurance_policy(user_id)
    return jsonify(dict(policy) if policy else {}), 200


@app.route("/insurance/coverage", methods=["POST"])
@role_required("user")
def check_coverage():
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    if not data.get("bill_amount"):
        return jsonify({"error": "bill_amount required"}), 400
    result = models.calculate_coverage(user_id, float(data["bill_amount"]))
    return jsonify(result), 200


# ─────────────────────────────────────────────
#  ADMIN
# ─────────────────────────────────────────────

@app.route("/admin/stats", methods=["GET"])
@role_required("admin")
def admin_stats():
    stats = models.get_platform_stats()
    return jsonify(dict(stats)), 200


@app.route("/admin/verifications", methods=["GET"])
@role_required("admin")
def pending_verifications():
    docs = models.get_pending_verifications()
    return jsonify([dict(d) for d in docs]), 200



@app.route('/landlord/analytics', methods=['GET'])
@role_required('landlord', 'admin')
def landlord_analytics():
    import json
    from datetime import datetime, date
    user_id = int(get_jwt_identity())
    data = models.get_landlord_analytics(user_id)
    def default(o):
        if isinstance(o, (datetime, date)): return o.isoformat()
        raise TypeError
    return app.response_class(json.dumps(data, default=default), mimetype='application/json'), 200


@app.route('/accommodations/<int:acc_id>/photos', methods=['GET'])
def get_photos(acc_id):
    photos = models.get_accommodation_photos(acc_id)
    return jsonify(photos), 200

@app.route('/accommodations/<int:acc_id>/photos', methods=['POST'])
@role_required('landlord', 'admin')
def add_photo(acc_id):
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    photo_url = data.get('photo_url', '').strip()
    if not photo_url:
        return jsonify({'error': 'photo_url is required'}), 400
    sort_order = data.get('sort_order', 0)
    photo_id = models.add_accommodation_photo(acc_id, photo_url, sort_order)
    return jsonify({'id': photo_id, 'photo_url': photo_url}), 201

@app.route('/photos/<int:photo_id>', methods=['DELETE'])
@role_required('landlord', 'admin')
def delete_photo(photo_id):
    user_id = int(get_jwt_identity())
    result = models.delete_accommodation_photo(photo_id, user_id)
    if not result:
        return jsonify({'error': 'Photo not found or unauthorized'}), 404
    return jsonify({'deleted': True}), 200

from flask import send_from_directory

# Serve HTML files from project root
@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    # Let Flask handle /static/ normally, serve HTML files from root
    if filename.startswith('static/'):
        return send_from_directory('.', filename)
    if filename.endswith('.html'):
        return send_from_directory('.', filename)
    return send_from_directory('.', filename)
if __name__ == "__main__":
    app.run(debug=True)

