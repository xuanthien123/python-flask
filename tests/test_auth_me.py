from app.extensions import db

from .conftest import ADMIN_EMAIL


def test_me_returns_profile_of_token_owner(client, admin_user, admin_auth_headers):
    response = client.get('/api/auth/me', headers=admin_auth_headers)

    body = response.get_json()
    assert response.status_code == 200
    assert body['success'] is True
    assert body['data'] == {
        'id': admin_user.id,
        'name': 'Admin',
        'email': ADMIN_EMAIL,
        'roles': ['admin'],
        'address': None,
        'date_of_birth': None,
        'sex': None,
        'email_verified_at': None,
    }


def test_me_never_exposes_password(client, admin_user, admin_auth_headers):
    response = client.get('/api/auth/me', headers=admin_auth_headers)

    assert 'password' not in response.get_json()['data']


def test_me_rejects_request_without_token(client):
    response = client.get('/api/auth/me')

    assert response.status_code == 401
    assert response.get_json()['message'] == 'Authentication required'


def test_me_rejects_invalid_token(client):
    response = client.get('/api/auth/me', headers={'Authorization': 'Bearer not-a-real-token'})

    assert response.status_code == 401
    assert response.get_json()['message'] == 'Invalid token'


def test_me_rejects_token_of_deleted_user(client, admin_user, admin_auth_headers):
    db.session.delete(admin_user)
    db.session.commit()

    response = client.get('/api/auth/me', headers=admin_auth_headers)

    assert response.status_code == 401
    assert response.get_json()['message'] == 'User not found'
