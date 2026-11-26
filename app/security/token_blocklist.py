from datetime import datetime, timezone

from app.extensions import db, jwt
from app.models import RevokedToken


def register_token_blocklist():
    @jwt.token_in_blocklist_loader
    def is_token_revoked(jwt_header, jwt_payload):
        revoked = RevokedToken.query.filter_by(jti=jwt_payload['jti']).first()
        return revoked is not None


def revoke_token(jwt_payload):
    if RevokedToken.query.filter_by(jti=jwt_payload['jti']).first():
        return
    expires_at = datetime.fromtimestamp(jwt_payload['exp'], tz=timezone.utc)
    db.session.add(RevokedToken(
        jti=jwt_payload['jti'],
        expires_at=expires_at.replace(tzinfo=None),
    ))
    db.session.commit()
