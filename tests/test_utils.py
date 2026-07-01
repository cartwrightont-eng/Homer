import pytest
from flask import Flask

from utils import parse_json_request, require_enum, require_fields, sanitize_string


@pytest.fixture
def app():
    app = Flask(__name__)
    return app


def test_require_fields_with_missing_value(app):
    with app.app_context():
        error = require_fields({"name": "Alice"}, ["name", "email"])
        assert error[1] == 400
        assert "Missing" in error[0].json["error"]


def test_require_fields_valid(app):
    with app.app_context():
        assert require_fields({"name": "Alice", "email": "alice@example.com"}, ["name", "email"]) is None


def test_require_enum_invalid(app):
    with app.app_context():
        error = require_enum("green", {"red", "blue"}, "color")
        assert error[1] == 400
        assert error[0].json["error"] == "color must be one of: blue, red"


def test_sanitize_string_trims_and_limits():
    assert sanitize_string("  hello world  ", max_length=5) == "hello"
    assert sanitize_string("  ", allow_empty=True) == ""
    assert sanitize_string("  ") is None
    assert sanitize_string(123, max_length=3) == "123"


def test_parse_json_request_with_malformed_body(app):
    with app.test_request_context(path="/", data="not-json", content_type="application/json"):
        data, error = parse_json_request()
        assert data is None
        assert error[1] == 400
        assert "required or malformed" in error[0].json["error"]
