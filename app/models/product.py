"""Product model with many‑to‑many relationship to Category.
"""

from sqlalchemy import Column, Integer, String, Text, Float
from sqlalchemy.orm import relationship

from ..extensions import db
from .associations import product_category

class Product(db.Model):
    __tablename__ = 'product'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False, default=0.0)
    # Many‑to‑many with Category
    categories = relationship(
        'Category',
        secondary=product_category,
        back_populates='products',
    )

    def __repr__(self):
        return f'<Product {self.name}>'
