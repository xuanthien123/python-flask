from app.models import RevokedToken
from app.security.tokens import build_access_token


def test_logout_succeeds_with_valid_token(client, admin_user, admin_auth_headers):
    response = client.post('/api/auth/logout', headers=admin_auth_headers)

    body = response.get_json()
    assert response.status_code == 200
    assert body['success'] is True
    assert body['message'] == 'Logged out'


def test_logout_stores_token_id_as_revoked(client, admin_user, admin_auth_headers):
    client.post('/api/auth/logout', headers=admin_auth_headers)

    assert RevokedToken.query.count() == 1


def test_token_is_rejected_after_logout(client, admin_user, admin_auth_headers):
    client.post('/api/auth/logout', headers=admin_auth_headers)

    response = client.get('/api/auth/me', headers=admin_auth_headers)

    assert response.status_code == 401
    assert response.get_json()['message'] == 'Token has been revoked'


def test_logout_twice_with_same_token_is_rejected(client, admin_user, admin_auth_headers):
    client.post('/api/auth/logout', headers=admin_auth_headers)

    response = client.post('/api/auth/logout', headers=admin_auth_headers)

    assert response.status_code == 401
    assert response.get_json()['message'] == 'Token has been revoked'


def test_logout_only_revokes_the_token_that_was_used(client, admin_user, admin_auth_headers):
    other_headers = {'Authorization': f'Bearer {build_access_token(admin_user)}'}

    client.post('/api/auth/logout', headers=admin_auth_headers)

    response = client.get('/api/auth/me', headers=other_headers)
    assert response.status_code == 200


def test_logout_rejects_request_without_token(client):
    response = client.post('/api/auth/logout')

    assert response.status_code == 401
    assert response.get_json()['message'] == 'Authentication required'
