"""Gửi mail cho user."""

from flask import current_app
from flask_mail import Message

from app.extensions import mail


def build_password_reset_link(plain_token):
    frontend_url = current_app.config['FRONTEND_URL']
    # Bỏ dấu / ở cuối (nếu có) để link không bị thành //reset-password
    frontend_url = frontend_url.rstrip('/')
    return f'{frontend_url}/reset-password?token={plain_token}'


def build_password_reset_body(user, reset_link):
    # Đọc thời hạn mã từ config để câu trong mail luôn khớp với thời hạn thật
    lifetime = current_app.config['PASSWORD_RESET_TOKEN_EXPIRES']
    lifetime_seconds = lifetime.total_seconds()
    lifetime_minutes = int(lifetime_seconds // 60)

    return (
        f'Hi {user.name},\n'
        '\n'
        'We received a request to reset the password for your account.\n'
        f'Open this link to choose a new password: {reset_link}\n'
        '\n'
        f'The link can be used once and expires in {lifetime_minutes} minutes.\n'
        'If you did not ask for this, you can ignore this email.\n'
    )


def send_password_reset_email(user, plain_token):
    reset_link = build_password_reset_link(plain_token)
    body = build_password_reset_body(user, reset_link)

    # Người gửi lấy từ MAIL_DEFAULT_SENDER trong config
    message = Message(
        subject='Reset your password',
        recipients=[user.email],
        body=body,
    )

    # Lúc chạy test (TESTING=True) Flask-Mail không gửi thật,
    # chỉ báo ra là đã gửi để test bắt lại được mail
    mail.send(message)
