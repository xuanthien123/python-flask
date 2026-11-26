from flask import Blueprint, request
from sqlalchemy.exc import IntegrityError

from app.common.errors import ApiError
from app.common.pagination import paginate_query
from app.common.responses import build_success_response
from app.common.validation import load_json_body
from app.decorators import role_required
from app.extensions import db
from app.models import Category

from .schemas import CreateCategorySchema, UpdateCategorySchema
from .serializers import serialize_category

categories_bp = Blueprint('categories', __name__, url_prefix='/api/categories')


def find_category_or_404(category_id):
    category = db.session.get(Category, category_id)
    if category is None:
        raise ApiError('Category not found', 404)
    return category


def ensure_name_is_free(name, ignore_category_id=None):
    query = Category.query.filter(db.func.lower(Category.name) == name.lower())
    if ignore_category_id is not None:
        query = query.filter(Category.id != ignore_category_id)
    if query.first() is not None:
        raise ApiError('Category name already exists', 409)


def commit_or_raise_name_conflict():
    # Another request can take the name between the check and the commit.
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ApiError('Category name already exists', 409)


@categories_bp.route('', methods=['GET'])
def list_categories():
    query = Category.query
    search_text = request.args.get('q', '').strip()
    if search_text:
        query = query.filter(Category.name.ilike(f'%{search_text}%'))
    rows, meta = paginate_query(query.order_by(Category.name), serialize_category)
    return build_success_response(rows, meta=meta)


@categories_bp.route('/<int:category_id>', methods=['GET'])
def get_category(category_id):
    category = find_category_or_404(category_id)
    return build_success_response(serialize_category(category))


@categories_bp.route('', methods=['POST'])
@role_required('admin')
def create_category():
    data = load_json_body(CreateCategorySchema())
    ensure_name_is_free(data['name'])
    category = Category(**data)
    db.session.add(category)
    commit_or_raise_name_conflict()
    return build_success_response(serialize_category(category), 'Category created', 201)


@categories_bp.route('/<int:category_id>', methods=['PUT', 'PATCH'])
@role_required('admin')
def update_category(category_id):
    category = find_category_or_404(category_id)
    data = load_json_body(UpdateCategorySchema())
    if 'name' in data:
        ensure_name_is_free(data['name'], ignore_category_id=category.id)
    for field_name, value in data.items():
        setattr(category, field_name, value)
    commit_or_raise_name_conflict()
    return build_success_response(serialize_category(category), 'Category updated')


@categories_bp.route('/<int:category_id>', methods=['DELETE'])
@role_required('admin')
def delete_category(category_id):
    category = find_category_or_404(category_id)
    if category.products:
        raise ApiError('Category still has products', 409)
    db.session.delete(category)
    db.session.commit()
    return build_success_response(message='Category deleted')
