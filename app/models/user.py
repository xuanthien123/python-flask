"""User model and its many‑to‑many relationship with Role."""

from sqlalchemy import Column, Integer, String, Date, DateTime
from sqlalchemy.orm import relationship

from ..extensions import db
from .associations import role_user

class User(db.Model):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    address = Column(String(512), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    sex = Column(String(10), nullable=True)
    email_verified_at = Column(DateTime, nullable=True)
    remember_token = Column(String(100), nullable=True)

    # Laravel: belongsToMany(Role::class)
    roles = relationship(
        "Role",
        secondary=role_user,
        back_populates="users",
    )

    def __repr__(self):
        return f"<User {self.email}>"
