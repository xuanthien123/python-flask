"""Category model definitions.
Simple example with id, name, description.
"""

from ..extensions import db
from .associations import product_category

class Category(db.Model):
    __tablename__ = 'category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    products = db.relationship(
        'Product',
        secondary=product_category,
        back_populates='categories',
    )

    def __repr__(self):
        return f'<Category {self.name}>'
