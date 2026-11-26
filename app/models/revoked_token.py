from sqlalchemy import Column, DateTime, Integer, String

from ..extensions import db


class RevokedToken(db.Model):
    __tablename__ = 'revoked_token'

    id = Column(Integer, primary_key=True)
    jti = Column(String(36), nullable=False, unique=True)
    expires_at = Column(DateTime, nullable=False)

    def __repr__(self):
        return f'<RevokedToken {self.jti}>'
