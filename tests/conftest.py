import pytest
from flask_jwt_extended import create_access_token

from app import app as flask_app


@pytest.fixture
def app():
    return flask_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def jwt_token(app):
    def create_token(identity="1", role="user"):
        with app.app_context():
            return create_access_token(identity=identity, additional_claims={"role": role, "name": "Test User"})

    return create_token
