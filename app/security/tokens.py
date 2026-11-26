from flask import current_app
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_jwt_identity,
)
from flask_jwt_extended.exceptions import JWTExtendedException
from jwt.exceptions import PyJWTError

from app.common.errors import ApiError
from app.extensions import db
from app.models import User


def build_access_token(user):
    role_names = [role.name for role in user.roles]
    return create_access_token(
        identity=str(user.id),
        additional_claims={'roles': role_names},
    )


def build_refresh_token(user):
    return create_refresh_token(identity=str(user.id))


def read_access_token_lifetime_seconds():
    return int(current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].total_seconds())


def build_login_tokens(user):
    return {
        'access_token': build_access_token(user),
        'refresh_token': build_refresh_token(user),
        'token_type': 'Bearer',
        'expires_in': read_access_token_lifetime_seconds(),
    }


def read_own_refresh_token_claims(refresh_token):
    try:
        claims = decode_token(refresh_token, allow_expired=True)
    except (PyJWTError, JWTExtendedException):
        claims = None
    if (
        claims is None
        or claims.get('type') != 'refresh'
        or claims['sub'] != get_jwt_identity()
    ):
        raise ApiError('Invalid refresh token', 422, {
            'refresh_token': ['Invalid refresh token'],
        })
    return claims


def load_current_user():
    return db.session.get(User, int(get_jwt_identity()))
