from app.common.mailer import send_password_reset_email
from app.extensions import mail
from app.models import PasswordResetToken

from .conftest import ADMIN_EMAIL

FORGOT_PASSWORD_MESSAGE = 'If the email is registered, a password reset link has been sent'


def post_forgot_password(client, payload):
    return client.post('/api/auth/forgot-password', json=payload)


def test_forgot_password_sends_token_for_registered_email(client, admin_user, sent_reset_tokens):
    response = post_forgot_password(client, {'email': ADMIN_EMAIL})

    body = response.get_json()
    assert response.status_code == 200
    assert body['success'] is True
    assert body['message'] == FORGOT_PASSWORD_MESSAGE
    assert len(sent_reset_tokens) == 1


def test_forgot_password_gives_same_answer_for_unknown_email(client, admin_user, sent_reset_tokens):
    registered = post_forgot_password(client, {'email': ADMIN_EMAIL})
    unknown = post_forgot_password(client, {'email': 'nobody@example.com'})

    assert unknown.status_code == registered.status_code
    assert unknown.get_json() == registered.get_json()
    assert len(sent_reset_tokens) == 1


def test_forgot_password_stores_hash_not_plain_token(client, admin_user, sent_reset_tokens):
    post_forgot_password(client, {'email': ADMIN_EMAIL})

    stored = PasswordResetToken.query.filter_by(user_id=admin_user.id).one()
    assert stored.token_hash != sent_reset_tokens[0]
    assert len(stored.token_hash) == 64


def test_forgot_password_keeps_only_newest_token(client, admin_user, sent_reset_tokens):
    post_forgot_password(client, {'email': ADMIN_EMAIL})
    post_forgot_password(client, {'email': ADMIN_EMAIL})

    assert PasswordResetToken.query.filter_by(user_id=admin_user.id).count() == 1


def test_forgot_password_sets_expiry_sixty_minutes_ahead(client, admin_user, sent_reset_tokens):
    post_forgot_password(client, {'email': ADMIN_EMAIL})

    stored = PasswordResetToken.query.filter_by(user_id=admin_user.id).one()
    lifetime = stored.expires_at - stored.created_at
    assert lifetime.total_seconds() == 60 * 60


def test_forgot_password_rejects_invalid_email(client):
    response = post_forgot_password(client, {'email': 'not-an-email'})

    assert response.status_code == 422
    assert 'email' in response.get_json()['errors']


def test_forgot_password_rejects_missing_email(client):
    response = post_forgot_password(client, {})

    assert response.status_code == 422
    assert 'email' in response.get_json()['errors']


def test_forgot_password_emails_reset_link_to_user(client, admin_user):
    with mail.record_messages() as outbox:
        post_forgot_password(client, {'email': ADMIN_EMAIL})

    assert len(outbox) == 1
    assert outbox[0].recipients == [ADMIN_EMAIL]
    assert '/reset-password?token=' in outbox[0].body


def test_forgot_password_gives_same_answer_when_mail_server_is_down(client, admin_user, monkeypatch):
    def fail_to_send_email(user, plain_token):
        raise ConnectionRefusedError('mail server is down')

    monkeypatch.setattr(
        'app.modules.auth.routes.send_password_reset_email',
        fail_to_send_email,
    )

    response = post_forgot_password(client, {'email': ADMIN_EMAIL})

    assert response.status_code == 200
    assert response.get_json()['message'] == FORGOT_PASSWORD_MESSAGE


def test_password_reset_email_has_link_and_expiry(app, admin_user):
    app.config['FRONTEND_URL'] = 'http://frontend.test/'

    with mail.record_messages() as outbox:
        send_password_reset_email(admin_user, 'abc123')

    message = outbox[0]
    assert message.subject == 'Reset your password'
    assert message.recipients == [ADMIN_EMAIL]
    assert message.sender == app.config['MAIL_DEFAULT_SENDER']
    assert 'http://frontend.test/reset-password?token=abc123' in message.body
    assert 'expires in 60 minutes' in message.body
