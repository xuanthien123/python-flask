"""Authentication routes similar to the Laravel example.
Provides login, password reset, logout, profile, and token‑based protected endpoints.
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity,
    get_jwt,
    unset_jwt_cookies,
)
from werkzeug.security import check_password_hash, generate_password_hash

# Assuming a User model with fields: id, email, password, name
from app.models import User

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# ---------------------------------------------------------------------------
# Public endpoints
# ---------------------------------------------------------------------------
@auth_bp.route('/login', methods=['POST'])
def login():
    # TODO: Implement login logic, validate credentials, and return JWT token.
    return

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    # TODO: Implement forgot password logic, send reset email with token.
    return

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    # TODO: Implement reset password logic, validate token, and update password.
    return

# ---------------------------------------------------------------------------
# Protected endpoints – require JWT
# ---------------------------------------------------------------------------
@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    # TODO: Return the current user's profile information.
    return

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    # TODO: Implement logout logic, invalidate JWT token, and clear cookies.
    return

@auth_bp.route('/password', methods=['PUT'])
@jwt_required()
def change_password():
    # TODO: Implement change password logic, validate current password, and update to new password.
    return

@auth_bp.route('/update-profile', methods=['PUT'])
@jwt_required()
def update_profile():
    # TODO: Implement update profile logic, validate input, and update user information.
    return
