from .conftest import ADMIN_EMAIL


def put_profile(client, headers, payload):
    return client.put('/api/auth/update-profile', json=payload, headers=headers)


def test_update_profile_changes_all_given_fields(client, admin_user, admin_auth_headers):
    response = put_profile(client, admin_auth_headers, {
        'name': 'New Name',
        'address': '12 Le Loi, Ha Noi',
        'date_of_birth': '1989-05-01',
        'sex': 'male',
    })

    body = response.get_json()
    assert response.status_code == 200
    assert body['success'] is True
    assert body['data']['name'] == 'New Name'
    assert body['data']['address'] == '12 Le Loi, Ha Noi'
    assert body['data']['date_of_birth'] == '1989-05-01'
    assert body['data']['sex'] == 'male'


def test_update_profile_keeps_fields_that_were_not_sent(client, admin_user, admin_auth_headers):
    put_profile(client, admin_auth_headers, {'address': 'Old address'})

    response = put_profile(client, admin_auth_headers, {'name': 'Only Name'})

    data = response.get_json()['data']
    assert data['name'] == 'Only Name'
    assert data['address'] == 'Old address'


def test_update_profile_saves_changes_to_database(client, admin_user, admin_auth_headers):
    put_profile(client, admin_auth_headers, {'name': 'Saved Name'})

    profile = client.get('/api/auth/me', headers=admin_auth_headers).get_json()['data']
    assert profile['name'] == 'Saved Name'


def test_update_profile_allows_clearing_optional_field(client, admin_user, admin_auth_headers):
    put_profile(client, admin_auth_headers, {'address': 'Some address'})

    response = put_profile(client, admin_auth_headers, {'address': None})

    assert response.status_code == 200
    assert response.get_json()['data']['address'] is None


def test_update_profile_rejects_email_roles_and_password_fields(client, admin_user, admin_auth_headers):
    response = put_profile(client, admin_auth_headers, {
        'email': 'hacker@example.com',
        'roles': ['admin'],
        'password': 'x',
    })

    assert response.status_code == 422
    assert set(response.get_json()['errors']) == {'email', 'roles', 'password'}
    profile = client.get('/api/auth/me', headers=admin_auth_headers).get_json()['data']
    assert profile['email'] == ADMIN_EMAIL


def test_update_profile_rejects_empty_body(client, admin_user, admin_auth_headers):
    response = put_profile(client, admin_auth_headers, {})

    assert response.status_code == 422
    assert response.get_json()['message'] == 'No fields to update'


def test_update_profile_rejects_empty_name(client, admin_user, admin_auth_headers):
    response = put_profile(client, admin_auth_headers, {'name': ''})

    assert response.status_code == 422
    assert 'name' in response.get_json()['errors']


def test_update_profile_rejects_malformed_date(client, admin_user, admin_auth_headers):
    response = put_profile(client, admin_auth_headers, {'date_of_birth': '01/05/1989'})

    assert response.status_code == 422
    assert 'date_of_birth' in response.get_json()['errors']


def test_update_profile_rejects_too_long_sex_value(client, admin_user, admin_auth_headers):
    response = put_profile(client, admin_auth_headers, {'sex': 'x' * 11})

    assert response.status_code == 422
    assert 'sex' in response.get_json()['errors']


def test_update_profile_rejects_request_without_token(client):
    response = client.put('/api/auth/update-profile', json={'name': 'No Token'})

    assert response.status_code == 401
    assert response.get_json()['message'] == 'Authentication required'
