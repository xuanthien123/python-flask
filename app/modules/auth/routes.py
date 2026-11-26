"""Authentication routes similar to the Laravel example.
Provides login, password reset, logout, profile, and token‑based protected endpoints.
"""

import smtplib

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity,
    get_jwt,
    unset_jwt_cookies,
)
from werkzeug.security import check_password_hash, generate_password_hash

from app.common.errors import ApiError
from app.common.mailer import send_password_reset_email
from app.common.responses import build_success_response
from app.common.validation import load_json_body, load_optional_json_body
from app.extensions import db
from app.models import User
from app.modules.users.serializers import serialize_user, serialize_user_profile
from app.security.password_reset import (
    create_password_reset_token,
    find_usable_reset_token,
    read_utc_now,
)
from app.security.passwords import hash_password, verify_password
from app.security.token_blocklist import revoke_token
from app.security.tokens import (
    build_access_token,
    build_login_tokens,
    load_current_user,
    read_access_token_lifetime_seconds,
    read_own_refresh_token_claims,
)

from .schemas import (
    ChangePasswordSchema,
    ForgotPasswordSchema,
    LoginSchema,
    LogoutSchema,
    ResetPasswordSchema,
    UpdateProfileSchema,
)

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

FORGOT_PASSWORD_MESSAGE = 'If the email is registered, a password reset link has been sent'
INVALID_RESET_TOKEN_MESSAGE = 'Invalid or expired reset token'

# ---------------------------------------------------------------------------
# Public endpoints
# ---------------------------------------------------------------------------
@auth_bp.route('/login', methods=['POST'])
def login():
    data = load_json_body(LoginSchema())
    user = User.query.filter_by(email=data['email']).first()
    if user is None or not verify_password(data['password'], user.password):
        raise ApiError('Invalid email or password', 401)
    return build_success_response({
        **build_login_tokens(user),
        'user': serialize_user(user),
    })

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    data = load_json_body(ForgotPasswordSchema())
    user = User.query.filter_by(email=data['email']).first()

    # Chỉ tạo mã và gửi link khi email có tài khoản
    if user is not None:
        plain_token = create_password_reset_token(user)
        try:
            send_password_reset_email(user, plain_token)
        except (smtplib.SMTPException, OSError):
            # Máy chủ mail lỗi hay không kết nối được (OSError) thì chỉ ghi log,
            # không trả lỗi 500. Nếu báo lỗi, người lạ sẽ biết email này có tài khoản.
            current_app.logger.exception('Could not send password reset email')

    # Có hay không có tài khoản cũng trả cùng một câu,
    # để người lạ không dò được email nào đã đăng ký
    return build_success_response(message=FORGOT_PASSWORD_MESSAGE)

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    data = load_json_body(ResetPasswordSchema())
    reset_token = find_usable_reset_token(data['token'])

    # Mã sai, đã dùng hay hết hạn đều báo cùng một lỗi
    if reset_token is None:
        raise ApiError(INVALID_RESET_TOKEN_MESSAGE, 422, {
            'token': [INVALID_RESET_TOKEN_MESSAGE],
        })

    user = db.session.get(User, reset_token.user_id)
    user.password = hash_password(data['new_password'])

    # Đánh dấu mã đã dùng, để không ai đổi mật khẩu lần nữa bằng mã này
    reset_token.used_at = read_utc_now()

    # Lưu mật khẩu mới và dấu "đã dùng" cùng một lần
    db.session.commit()
    return build_success_response(message='Password has been reset')

# ---------------------------------------------------------------------------
# Protected endpoints – require JWT
# ---------------------------------------------------------------------------
@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh_access_token():
    user = load_current_user()
    
    if user is None:
        raise ApiError('User not found', 401)
    return build_success_response({
        'access_token': build_access_token(user),
        'token_type': 'Bearer',
        'expires_in': read_access_token_lifetime_seconds(),
    })

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    user = load_current_user()
    if user is None:
        raise ApiError('User not found', 401)
    return build_success_response(serialize_user_profile(user))

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    data = load_optional_json_body(LogoutSchema())
    refresh_token = data.get('refresh_token')
    refresh_claims = read_own_refresh_token_claims(refresh_token) if refresh_token else None
    revoke_token(get_jwt())
    if refresh_claims:
        revoke_token(refresh_claims)
    return build_success_response(message='Logged out')

@auth_bp.route('/password', methods=['PUT'])
@jwt_required()
def change_password():
    data = load_json_body(ChangePasswordSchema())
    user = load_current_user()
    if user is None:
        raise ApiError('User not found', 401)
    if not verify_password(data['current_password'], user.password):
        raise ApiError('Current password is incorrect', 422, {
            'current_password': ['Current password is incorrect'],
        })
    user.password = hash_password(data['new_password'])
    db.session.commit()
    return build_success_response(message='Password changed')

@auth_bp.route('/update-profile', methods=['PUT'])
@jwt_required()
def update_profile():
    data = load_json_body(UpdateProfileSchema())
    if not data:
        raise ApiError('No fields to update', 422)
    user = load_current_user()
    if user is None:
        raise ApiError('User not found', 401)
    for field_name, value in data.items():
        setattr(user, field_name, value)
    db.session.commit()
    return build_success_response(serialize_user_profile(user))
