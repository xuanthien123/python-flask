"""Category routes – CRUD with admin protection where needed.
"""

from flask import Blueprint, request, jsonify
from app.models import Category
from app.extensions import db
from app.decorators import role_required

categories_bp = Blueprint('categories', __name__, url_prefix='/categories')

# Public: list categories
@categories_bp.route('', methods=['GET'])
def list_categories():
    # TODO: Implement pagination and filtering if needed.
    return

# Admin: create category
@categories_bp.route('', methods=['POST'])
@role_required('admin')
def create_category():
    # TODO: Implement category creation logic, validate input, and save to database.
    return

# Admin: update category
@categories_bp.route('/<int:category_id>', methods=['PUT', 'PATCH'])
@role_required('admin')
def update_category(category_id):
    # TODO: Implement category update logic, validate input, and save changes to database.
    return

# Admin: delete category
@categories_bp.route('/<int:category_id>', methods=['DELETE'])
@role_required('admin')
def delete_category(category_id):
    # TODO: Implement category deletion logic, check for dependencies, and remove from database.
    return
