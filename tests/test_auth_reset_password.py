from datetime import timedelta

from app.extensions import db
from app.models import PasswordResetToken

from .conftest import ADMIN_EMAIL, ADMIN_PASSWORD

NEW_PASSWORD = 'brand-new-pass-1'
INVALID_RESET_TOKEN_MESSAGE = 'Invalid or expired reset token'


def request_reset_token(client, sent_reset_tokens):
    client.post('/api/auth/forgot-password', json={'email': ADMIN_EMAIL})
    return sent_reset_tokens[-1]


def post_reset_password(client, payload):
    return client.post('/api/auth/reset-password', json=payload)


def post_login(client, password):
    return client.post('/api/auth/login', json={'email': ADMIN_EMAIL, 'password': password})


def assert_invalid_token_response(response):
    body = response.get_json()
    assert response.status_code == 422
    assert body['success'] is False
    assert body['message'] == INVALID_RESET_TOKEN_MESSAGE
    assert 'token' in body['errors']


def test_reset_password_succeeds_with_valid_token(client, admin_user, sent_reset_tokens):
    token = request_reset_token(client, sent_reset_tokens)

    response = post_reset_password(client, {'token': token, 'new_password': NEW_PASSWORD})

    body = response.get_json()
    assert response.status_code == 200
    assert body['success'] is True
    assert body['message'] == 'Password has been reset'


def test_login_works_with_new_password_after_reset(client, admin_user, sent_reset_tokens):
    token = request_reset_token(client, sent_reset_tokens)

    post_reset_password(client, {'token': token, 'new_password': NEW_PASSWORD})

    assert post_login(client, NEW_PASSWORD).status_code == 200
    assert post_login(client, ADMIN_PASSWORD).status_code == 401


def test_reset_password_rejects_unknown_token(client, admin_user):
    response = post_reset_password(client, {'token': 'made-up-token', 'new_password': NEW_PASSWORD})

    assert_invalid_token_response(response)
    assert post_login(client, ADMIN_PASSWORD).status_code == 200


def test_reset_password_rejects_token_used_twice(client, admin_user, sent_reset_tokens):
    token = request_reset_token(client, sent_reset_tokens)
    post_reset_password(client, {'token': token, 'new_password': NEW_PASSWORD})

    second = post_reset_password(client, {'token': token, 'new_password': 'another-pass-2'})

    assert_invalid_token_response(second)
    assert post_login(client, NEW_PASSWORD).status_code == 200


def test_reset_password_rejects_expired_token(client, admin_user, sent_reset_tokens):
    token = request_reset_token(client, sent_reset_tokens)
    stored = PasswordResetToken.query.filter_by(user_id=admin_user.id).one()
    stored.expires_at = stored.created_at - timedelta(minutes=1)
    db.session.commit()

    response = post_reset_password(client, {'token': token, 'new_password': NEW_PASSWORD})

    assert_invalid_token_response(response)
    assert post_login(client, ADMIN_PASSWORD).status_code == 200


def test_reset_password_rejects_old_token_after_new_request(client, admin_user, sent_reset_tokens):
    old_token = request_reset_token(client, sent_reset_tokens)
    new_token = request_reset_token(client, sent_reset_tokens)

    old_response = post_reset_password(client, {'token': old_token, 'new_password': NEW_PASSWORD})
    new_response = post_reset_password(client, {'token': new_token, 'new_password': NEW_PASSWORD})

    assert_invalid_token_response(old_response)
    assert new_response.status_code == 200


def test_reset_password_rejects_too_short_password(client, admin_user, sent_reset_tokens):
    token = request_reset_token(client, sent_reset_tokens)

    response = post_reset_password(client, {'token': token, 'new_password': 'short'})

    assert response.status_code == 422
    assert 'new_password' in response.get_json()['errors']
    assert post_login(client, ADMIN_PASSWORD).status_code == 200


def test_reset_password_rejects_missing_fields(client):
    response = post_reset_password(client, {})

    assert response.status_code == 422
    assert set(response.get_json()['errors']) == {'token', 'new_password'}
