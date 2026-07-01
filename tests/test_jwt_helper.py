from flask_jwt_extended import create_access_token


def create_test_token(identity="1", role="user"):
    return create_access_token(identity=identity, additional_claims={"role": role, "name": "Test User"})
