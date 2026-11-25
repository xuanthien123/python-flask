"""Package that groups all SQLAlchemy models.
It re‑exports the individual model classes for convenient imports.
"""

from .category import Category
from .product import Product
from .role import Role
from .user import User
from .associations import product_category, role_user
