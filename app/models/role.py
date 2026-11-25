"""Role model – many‑to‑many relationship with User.
"""

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from ..extensions import db
from .associations import role_user

class Role(db.Model):
    __tablename__ = 'role'
    id = Column(Integer, primary_key=True)
    name = Column(String(64), unique=True, nullable=False)
    # Relationship back to users
    users = relationship(
        'User',
        secondary=role_user,
        back_populates='roles',
    )

    def __repr__(self):
        return f'<Role {self.name}>'
