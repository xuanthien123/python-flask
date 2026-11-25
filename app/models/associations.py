# app/models/associations.py
"""Association tables for many‑to‑many relationships used by the model
package. They are imported by the individual model files.
"""

from ..extensions import db
from sqlalchemy import Table, Column, Integer, ForeignKey

# Product ↔ Category
product_category = Table(
    "product_category",
    db.metadata,
    Column("product_id", Integer, ForeignKey("product.id"), primary_key=True),
    Column("category_id", Integer, ForeignKey("category.id"), primary_key=True),
)

# Role ↔ User
role_user = Table(
    "role_user",
    db.metadata,
    Column("role_id", Integer, ForeignKey("role.id"), primary_key=True),
    Column("user_id", Integer, ForeignKey("user.id"), primary_key=True),
)
