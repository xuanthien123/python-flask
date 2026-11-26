"""Tạo và kiểm mã đặt lại mật khẩu (dùng cho quên mật khẩu)."""

import hashlib
import secrets
from datetime import datetime, timezone

from flask import current_app

from app.extensions import db
from app.models import PasswordResetToken


def read_utc_now():
    # Lấy giờ UTC rồi bỏ phần múi giờ, vì cột DateTime trong DB
    # lưu giờ không kèm múi giờ (bảng revoked_token cũng làm vậy)
    now = datetime.now(timezone.utc)
    return now.replace(tzinfo=None)


def hash_reset_token(plain_token):
    # Dùng sha256 chứ không dùng hash_password: sha256 băm cùng một mã
    # luôn ra cùng một kết quả, nhờ vậy mới tìm lại được mã trong DB.
    # hash_password thêm phần ngẫu nhiên nên mỗi lần băm ra một kiểu.
    token_bytes = plain_token.encode('utf-8')
    digest = hashlib.sha256(token_bytes)
    return digest.hexdigest()


def create_password_reset_token(user):
    # Xoá mã cũ của user này, để chỉ mã mới nhất còn dùng được
    old_tokens = PasswordResetToken.query.filter_by(user_id=user.id)
    old_tokens.delete()

    # Mã ngẫu nhiên 32 byte, rất khó đoán. Dạng "urlsafe" chỉ gồm chữ, số,
    # dấu - và _, nên gắn thẳng vào link được.
    plain_token = secrets.token_urlsafe(32)
    token_hash = hash_reset_token(plain_token)

    now = read_utc_now()
    lifetime = current_app.config['PASSWORD_RESET_TOKEN_EXPIRES']
    expires_at = now + lifetime

    reset_token = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
        created_at=now,
    )
    db.session.add(reset_token)
    db.session.commit()

    # Trả mã gốc để gửi cho user. Mã gốc không được lưu ở đâu cả.
    return plain_token


def find_usable_reset_token(plain_token):
    # Băm mã user gửi lên rồi tìm bản băm đó trong DB
    token_hash = hash_reset_token(plain_token)
    reset_token = PasswordResetToken.query.filter_by(token_hash=token_hash).first()

    # Không có mã này
    if reset_token is None:
        return None

    # Mã đã dùng để đổi mật khẩu rồi
    if reset_token.used_at is not None:
        return None

    # Mã đã quá hạn
    now = read_utc_now()
    if reset_token.expires_at <= now:
        return None

    return reset_token
