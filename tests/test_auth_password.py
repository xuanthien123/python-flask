from .conftest import ADMIN_EMAIL, ADMIN_PASSWORD

NEW_PASSWORD = 'brand-new-pass-1'


def put_password(client, headers, payload):
    return client.put('/api/auth/password', json=payload, headers=headers)


def post_login(client, password):
    return client.post('/api/auth/login', json={'email': ADMIN_EMAIL, 'password': password})


def test_change_password_succeeds_with_correct_current_password(client, admin_user, admin_auth_headers):
    response = put_password(client, admin_auth_headers, {
        'current_password': ADMIN_PASSWORD,
        'new_password': NEW_PASSWORD,
    })

    body = response.get_json()
    assert response.status_code == 200
    assert body['success'] is True
    assert body['message'] == 'Password changed'


def test_login_works_with_new_password_and_fails_with_old_one(client, admin_user, admin_auth_headers):
    put_password(client, admin_auth_headers, {
        'current_password': ADMIN_PASSWORD,
        'new_password': NEW_PASSWORD,
    })

    assert post_login(client, NEW_PASSWORD).status_code == 200
    assert post_login(client, ADMIN_PASSWORD).status_code == 401


def test_change_password_stores_hash_not_plain_text(client, admin_user, admin_auth_headers):
    put_password(client, admin_auth_headers, {
        'current_password': ADMIN_PASSWORD,
        'new_password': NEW_PASSWORD,
    })

    assert admin_user.password != NEW_PASSWORD


def test_change_password_rejects_wrong_current_password(client, admin_user, admin_auth_headers):
    response = put_password(client, admin_auth_headers, {
        'current_password': 'not-the-password',
        'new_password': NEW_PASSWORD,
    })

    assert response.status_code == 422
    assert 'current_password' in response.get_json()['errors']
    assert post_login(client, ADMIN_PASSWORD).status_code == 200


def test_change_password_rejects_too_short_new_password(client, admin_user, admin_auth_headers):
    response = put_password(client, admin_auth_headers, {
        'current_password': ADMIN_PASSWORD,
        'new_password': 'short',
    })

    assert response.status_code == 422
    assert 'new_password' in response.get_json()['errors']


def test_change_password_rejects_same_password(client, admin_user, admin_auth_headers):
    response = put_password(client, admin_auth_headers, {
        'current_password': ADMIN_PASSWORD,
        'new_password': ADMIN_PASSWORD,
    })

    assert response.status_code == 422
    assert 'new_password' in response.get_json()['errors']


def test_change_password_rejects_missing_fields(client, admin_user, admin_auth_headers):
    response = put_password(client, admin_auth_headers, {})

    assert response.status_code == 422
    assert set(response.get_json()['errors']) == {'current_password', 'new_password'}


def test_change_password_rejects_request_without_token(client):
    response = client.put('/api/auth/password', json={
        'current_password': ADMIN_PASSWORD,
        'new_password': NEW_PASSWORD,
    })

    assert response.status_code == 401
    assert response.get_json()['message'] == 'Authentication required'
