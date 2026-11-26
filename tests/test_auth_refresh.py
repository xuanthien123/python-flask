from datetime import timedelta

from flask_jwt_extended import create_access_token, create_refresh_token, decode_token

from app.extensions import db
from app.models import RevokedToken, User
from app.security.passwords import hash_password
from app.security.tokens import build_access_token, build_refresh_token

from .conftest import ADMIN_EMAIL, ADMIN_PASSWORD


def post_login(client):
    return client.post('/api/auth/login', json={'email': ADMIN_EMAIL, 'password': ADMIN_PASSWORD})


def test_login_returns_refresh_token_and_lifetime(client, admin_user):
    data = post_login(client).get_json()['data']

    assert data['refresh_token']
    assert data['token_type'] == 'Bearer'
    assert data['expires_in'] == 30 * 60


def test_login_tokens_have_expected_types_and_lifetimes(client, admin_user):
    data = post_login(client).get_json()['data']

    access = decode_token(data['access_token'])
    refresh = decode_token(data['refresh_token'])
    assert access['type'] == 'access'
    assert refresh['type'] == 'refresh'
    assert access['exp'] - access['iat'] == 30 * 60
    assert refresh['exp'] - refresh['iat'] == 30 * 24 * 60 * 60


def test_refresh_returns_new_access_token_that_works(client, admin_user, admin_refresh_headers):
    response = client.post('/api/auth/refresh', headers=admin_refresh_headers)

    data = response.get_json()['data']
    assert response.status_code == 200
    assert data['expires_in'] == 30 * 60
    assert 'refresh_token' not in data
    new_headers = {'Authorization': f"Bearer {data['access_token']}"}
    assert client.get('/api/auth/me', headers=new_headers).status_code == 200


def test_refresh_rejects_access_token(client, admin_user, admin_auth_headers):
    response = client.post('/api/auth/refresh', headers=admin_auth_headers)

    assert response.status_code == 401
    assert response.get_json()['code'] == 'token_invalid'


def test_normal_route_rejects_refresh_token(client, admin_user, admin_refresh_headers):
    response = client.get('/api/auth/me', headers=admin_refresh_headers)

    assert response.status_code == 401
    assert response.get_json()['code'] == 'token_invalid'


def test_refresh_rejects_request_without_token(client):
    response = client.post('/api/auth/refresh')

    assert response.status_code == 401
    assert response.get_json()['code'] == 'token_missing'


def test_refresh_rejects_expired_refresh_token(client, admin_user):
    expired = create_refresh_token(identity=str(admin_user.id), expires_delta=timedelta(seconds=-10))

    response = client.post('/api/auth/refresh', headers={'Authorization': f'Bearer {expired}'})

    assert response.status_code == 401
    assert response.get_json()['code'] == 'token_expired'


def test_refresh_rejects_token_of_deleted_user(client, admin_user, admin_refresh_headers):
    db.session.delete(admin_user)
    db.session.commit()

    response = client.post('/api/auth/refresh', headers=admin_refresh_headers)

    assert response.status_code == 401
    assert response.get_json()['message'] == 'User not found'


def test_expired_access_token_returns_token_expired_code(client, admin_user):
    expired = create_access_token(identity=str(admin_user.id), expires_delta=timedelta(seconds=-10))

    response = client.get('/api/auth/me', headers={'Authorization': f'Bearer {expired}'})

    assert response.status_code == 401
    assert response.get_json()['code'] == 'token_expired'


def test_logout_with_refresh_token_revokes_both_tokens(
    client, admin_user, admin_auth_headers, admin_refresh_token, admin_refresh_headers
):
    response = client.post(
        '/api/auth/logout', headers=admin_auth_headers, json={'refresh_token': admin_refresh_token}
    )

    assert response.status_code == 200
    assert RevokedToken.query.count() == 2
    refresh_again = client.post('/api/auth/refresh', headers=admin_refresh_headers)
    assert refresh_again.status_code == 401
    assert refresh_again.get_json()['code'] == 'token_revoked'


def test_logout_without_refresh_token_keeps_refresh_token_usable(
    client, admin_user, admin_auth_headers, admin_refresh_headers
):
    client.post('/api/auth/logout', headers=admin_auth_headers)

    assert client.post('/api/auth/refresh', headers=admin_refresh_headers).status_code == 200


def test_logout_rejects_garbage_refresh_token_and_revokes_nothing(client, admin_user, admin_auth_headers):
    response = client.post(
        '/api/auth/logout', headers=admin_auth_headers, json={'refresh_token': 'garbage'}
    )

    assert response.status_code == 422
    assert 'refresh_token' in response.get_json()['errors']
    assert RevokedToken.query.count() == 0


def test_logout_rejects_refresh_token_of_another_user(client, admin_user, admin_auth_headers):
    other = User(name='Other', email='other@example.com', password=hash_password('whatever123'))
    db.session.add(other)
    db.session.commit()

    response = client.post(
        '/api/auth/logout',
        headers=admin_auth_headers,
        json={'refresh_token': build_refresh_token(other)},
    )

    assert response.status_code == 422
    assert RevokedToken.query.count() == 0


def test_logout_accepts_expired_refresh_token(client, admin_user, admin_auth_headers):
    expired = create_refresh_token(identity=str(admin_user.id), expires_delta=timedelta(seconds=-10))

    response = client.post('/api/auth/logout', headers=admin_auth_headers, json={'refresh_token': expired})

    assert response.status_code == 200


def test_logout_with_already_revoked_refresh_token_does_not_fail(
    client, admin_user, admin_auth_headers, admin_refresh_token
):
    client.post('/api/auth/logout', headers=admin_auth_headers, json={'refresh_token': admin_refresh_token})
    second_access = {'Authorization': f'Bearer {build_access_token(admin_user)}'}

    response = client.post('/api/auth/logout', headers=second_access, json={'refresh_token': admin_refresh_token})

    assert response.status_code == 200
