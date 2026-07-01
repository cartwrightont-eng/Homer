from functools import wraps

from flask import current_app, jsonify, request
from flask_jwt_extended import get_jwt, jwt_required


def json_error(message, status=400):
    return jsonify({"error": message}), status


def sanitize_string(value, max_length=None, allow_empty=False):
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)

    cleaned = value.strip()
    if not allow_empty and cleaned == "":
        return None
    if max_length is not None:
        cleaned = cleaned[:max_length]
    return cleaned


def sanitize_fields(data, field_specs):
    sanitized = {}
    for field, spec in field_specs.items():
        if isinstance(spec, tuple):
            max_length, allow_empty = spec
        else:
            max_length, allow_empty = spec, False
        sanitized[field] = sanitize_string(data.get(field), max_length=max_length, allow_empty=allow_empty)
    return sanitized


def parse_json_request():
    data = request.get_json(silent=True)
    if data is None:
        return None, json_error("JSON body required or malformed", 400)

    if not isinstance(data, dict):
        return None, json_error("JSON body must be an object", 400)

    return data, None


def require_fields(data, required):
    missing = [
        field for field in required
        if field not in data or data[field] is None or (isinstance(data[field], str) and not data[field].strip())
    ]
    if missing:
        return json_error(f"Missing: {', '.join(missing)}", 400)
    return None


def require_enum(value, valid_values, field_name="value"):
    if value not in valid_values:
        return json_error(f"{field_name} must be one of: {', '.join(sorted(valid_values))}", 400)
    return None


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


def rate_limit(*limits):
    limiter = current_app.extensions.get("limiter")
    if limiter is None:
        return lambda fn: fn
    return limiter.limit(*limits)
