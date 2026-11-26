import pytest

from app import create_app
from app.extensions import db
from app.models import Role, User
from app.security.passwords import hash_password
from app.security.tokens import build_access_token, build_refresh_token

ADMIN_EMAIL = 'admin@example.com'
ADMIN_PASSWORD = 'secret123'


@pytest.fixture()
def app():
    app = create_app('app.config.TestConfig')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def admin_user(app):
    admin_role = Role(name='admin')
    user = User(
        name='Admin',
        email=ADMIN_EMAIL,
        password=hash_password(ADMIN_PASSWORD),
    )
    user.roles.append(admin_role)
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture()
def admin_auth_headers(admin_user):
    return {'Authorization': f'Bearer {build_access_token(admin_user)}'}


@pytest.fixture()
def non_admin_auth_headers(app):
    user = User(
        name='Customer',
        email='customer@example.com',
        password=hash_password('secret123'),
    )
    db.session.add(user)
    db.session.commit()
    return {'Authorization': f'Bearer {build_access_token(user)}'}


@pytest.fixture()
def admin_refresh_token(admin_user):
    return build_refresh_token(admin_user)


@pytest.fixture()
def admin_refresh_headers(admin_refresh_token):
    return {'Authorization': f'Bearer {admin_refresh_token}'}


@pytest.fixture()
def sent_reset_tokens(monkeypatch):
    # Thay hàm gửi mail bằng hàm giả, chỉ giữ lại mã đã "gửi".
    # DB chỉ có bản băm nên test phải lấy mã gốc từ đây.
    sent_tokens = []

    def fake_send_password_reset_email(user, plain_token):
        sent_tokens.append(plain_token)

    monkeypatch.setattr(
        'app.modules.auth.routes.send_password_reset_email',
        fake_send_password_reset_email,
    )
    return sent_tokens
