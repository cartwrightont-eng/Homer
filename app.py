import os
from datetime import timedelta

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager

try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
except ImportError:  # pragma: no cover - optional dependency in some environments
    Limiter = None
    get_remote_address = None

from blueprints.accommodations import bp as accommodations_bp
from blueprints.admin import bp as admin_bp
from blueprints.applications import bp as applications_bp
from blueprints.auth import bp as auth_bp
from blueprints.content import bp as content_bp
from blueprints.favourites import bp as favourites_bp
from blueprints.insurance import bp as insurance_bp
from blueprints.jobs import bp as jobs_bp
from blueprints.messages import bp as messages_bp
from blueprints.payments import bp as payments_bp
from blueprints.photos import bp as photos_bp
from blueprints.providers import bp as providers_bp
from blueprints.tours import bp as tours_bp
from blueprints.verification import bp as verification_bp
from config import JWT_SECRET_KEY

app = Flask(__name__)
if Limiter is not None and get_remote_address is not None:
    limiter = Limiter(get_remote_address, app=app, default_limits=[])
    app.extensions["limiter"] = limiter
else:
    limiter = None

app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=7)
app.config["JSON_SORT_KEYS"] = False

cors_origins = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",") if origin.strip()]
CORS(app, resources={r"/*": {"origins": cors_origins}})

jwt = JWTManager(app)

app.register_blueprint(auth_bp)
app.register_blueprint(accommodations_bp)
app.register_blueprint(applications_bp)
app.register_blueprint(payments_bp)
app.register_blueprint(content_bp)
app.register_blueprint(messages_bp)
app.register_blueprint(tours_bp)
app.register_blueprint(verification_bp)
app.register_blueprint(providers_bp)
app.register_blueprint(jobs_bp)
app.register_blueprint(insurance_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(favourites_bp)
app.register_blueprint(photos_bp)


@app.route("/")
def serve_index():
    return send_from_directory(".", "index.html")


SAFE_STATIC_EXTENSIONS = {".html", ".css", ".js", ".json", ".png", ".jpg", ".jpeg", ".svg", ".ico", ".txt"}


@app.route("/<path:filename>")
def serve_static(filename):
    if filename.startswith("static/"):
        return send_from_directory(".", filename)
    if os.path.splitext(filename)[1].lower() in SAFE_STATIC_EXTENSIONS:
        return send_from_directory(".", filename)
    return jsonify({"error": "Forbidden"}), 403


if __name__ == "__main__":
    app.run(
        debug=os.getenv("FLASK_ENV", "development") == "development",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
    )

