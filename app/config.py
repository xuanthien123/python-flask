import os

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
