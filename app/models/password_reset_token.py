"""Bảng lưu mã đặt lại mật khẩu, tạo ra khi user bấm quên mật khẩu."""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String

from ..extensions import db


class PasswordResetToken(db.Model):
    __tablename__ = 'password_reset_token'

    id = Column(Integer, primary_key=True)
    # Mã này của user nào. Có index vì hay tìm mã theo user để huỷ mã cũ.
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False, index=True)
    # Chỉ lưu bản băm sha256 của mã (luôn dài 64 ký tự), không lưu mã gốc.
    # Lỡ lộ DB thì người khác cũng không lấy được mã để đổi mật khẩu.
    token_hash = Column(String(64), nullable=False, unique=True)
    # Qua thời điểm này thì mã hết hạn
    expires_at = Column(DateTime, nullable=False)
    # Còn trống là mã chưa dùng. Có giá trị là mã đã dùng, không dùng lại được.
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False)

    def __repr__(self):
        return f'<PasswordResetToken user_id={self.user_id}>'
