import os
from datetime import timedelta


def read_int_from_env(name, default):
    # Biến môi trường luôn là chữ, mà cổng mail phải là số nên đổi sang int
    text_value = os.getenv(name, default)
    return int(text_value)


class Config:
    """Base configuration with sensible defaults."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev_secret_key_change_later')
    DEBUG = os.getenv('FLASK_DEBUG', '1') == '1'
    # Database URL for SQLAlchemy – compose provides MySQL service name `mysql`
    DB_USER = os.getenv('MYSQL_USER', 'flask_user')
    DB_PASSWORD = os.getenv('MYSQL_PASSWORD', 'flask_password_123')
    DB_HOST = os.getenv('DB_HOST', 'mysql')
    DB_PORT = os.getenv('DB_PORT', '3306')
    DB_NAME = os.getenv('MYSQL_DATABASE', 'product_management')
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev_jwt_secret')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=30)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    # Mã đặt lại mật khẩu chỉ dùng được trong 60 phút sau khi tạo
    PASSWORD_RESET_TOKEN_EXPIRES = timedelta(minutes=60)
    # Địa chỉ trang web (Vue) để ghép link đặt lại mật khẩu gửi cho user.
    # Mặc định là nginx ở cổng 8080, nơi đang trả bản build của Vue.
    FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:8080')

    # Máy chủ gửi mail (SMTP), Flask-Mail đọc các key MAIL_* này.
    # Mặc định trỏ tới Mailpit trong docker-compose: hộp thư giả, hứng hết mail
    # để xem ở http://localhost:8025, không gửi tới ai thật.
    # Chạy thật thì đặt các biến này trong .env theo SMTP thật (Gmail, SES...).
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'mailpit')
    MAIL_PORT = read_int_from_env('MAIL_PORT', '1025')
    # Mailpit không cần đăng nhập nên để trống
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    # Mã hoá đường truyền. Mailpit không dùng; SMTP thật thường cần TLS.
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', '0') == '1'
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', '0') == '1'
    # Địa chỉ hiện ở ô "Người gửi" của mail
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'no-reply@product-management.local')
    # Flask-Mail mặc định in hết nội dung gửi qua SMTP ra log khi DEBUG bật.
    # Nội dung đó có link đặt lại mật khẩu, ai đọc log là dùng được, nên tắt.
    MAIL_DEBUG = os.getenv('MAIL_DEBUG', '0') == '1'


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    JWT_SECRET_KEY = 'test_jwt_secret_with_enough_length_for_hs256'
