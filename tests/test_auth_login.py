from flask_jwt_extended import decode_token

from .conftest import ADMIN_EMAIL, ADMIN_PASSWORD


def post_login(client, payload):
    return client.post('/api/auth/login', json=payload)


def test_login_returns_token_and_user_for_valid_credentials(client, admin_user):
    response = post_login(client, {'email': ADMIN_EMAIL, 'password': ADMIN_PASSWORD})

    body = response.get_json()
    assert response.status_code == 200
    assert body['success'] is True
    assert body['data']['user'] == {
        'id': admin_user.id,
        'name': 'Admin',
        'email': ADMIN_EMAIL,
        'roles': ['admin']
    }
    assert body['data']['access_token']


def test_login_token_carries_roles_claim(client, admin_user):
    response = post_login(client, {'email': ADMIN_EMAIL, 'password': ADMIN_PASSWORD})

    token = response.get_json()['data']['access_token']
    claims = decode_token(token)
    assert claims['sub'] == str(admin_user.id)
    assert claims['roles'] == ['admin']


def test_login_response_never_exposes_password(client, admin_user):
    response = post_login(client, {'email': ADMIN_EMAIL, 'password': ADMIN_PASSWORD})

    assert 'password' not in response.get_json()['data']['user']


def test_login_rejects_wrong_password(client, admin_user):
    response = post_login(client, {'email': ADMIN_EMAIL, 'password': 'wrong-password'})

    assert response.status_code == 401
    assert response.get_json()['message'] == 'Invalid email or password'


def test_login_rejects_unknown_email_with_same_message_as_wrong_password(client, admin_user):
    wrong_password = post_login(client, {'email': ADMIN_EMAIL, 'password': 'wrong-password'})
    unknown_email = post_login(client, {'email': 'nobody@example.com', 'password': 'abc'})

    assert unknown_email.status_code == 401
    assert unknown_email.get_json() == wrong_password.get_json()


def test_login_rejects_empty_body_with_missing_fields(client):
    response = post_login(client, {})

    body = response.get_json()
    assert response.status_code == 422
    assert set(body['errors']) == {'email', 'password'}


def test_login_rejects_missing_password(client):
    response = post_login(client, {'email': ADMIN_EMAIL})

    assert response.status_code == 422
    assert set(response.get_json()['errors']) == {'password'}


def test_login_rejects_malformed_email(client):
    response = post_login(client, {'email': 'not-an-email', 'password': 'abc'})

    assert response.status_code == 422
    assert 'email' in response.get_json()['errors']


def test_login_rejects_request_without_json_body(client):
    response = client.post('/api/auth/login', data='email=a@b.com', content_type='text/plain')

    assert response.status_code == 400
    assert response.get_json()['message'] == 'Request body must be JSON'
