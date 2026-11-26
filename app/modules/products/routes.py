"""Product routes – CRUD and extra actions.
Matches the Laravel route definitions you provided.
"""

from datetime import date

from flask import Blueprint, request, jsonify, current_app, send_file
from marshmallow import ValidationError
from sqlalchemy.orm import selectinload

from app.common.errors import ApiError
from app.common.pagination import paginate_query
from app.common.responses import build_success_response
from app.common.validation import load_json_body, load_query_args
from app.models import Product, Category
from app.extensions import db
from app.decorators import role_required
import csv
import io

from .excel import (
    TEMPLATE_FILENAME,
    XLSX_MIMETYPE,
    build_export_filename,
    build_import_template,
    build_products_export,
    convert_import_row,
    read_import_rows,
)
from .schemas import CreateProductSchema, ListProductsQuerySchema, UpdateProductSchema
from .serializers import serialize_product

products_bp = Blueprint('products', __name__, url_prefix='/api/products')

# Tên người dùng gửi trong ?sort= và cột thật tương ứng trong bảng product
PRODUCT_SORT_COLUMNS = {
    'id': Product.id,
    'name': Product.name,
    'price': Product.price,
}


def filter_products(query, filters):
    # Mỗi bộ lọc người dùng gửi lên thêm một điều kiện WHERE vào câu SQL.
    # Hàm này chỉ soạn câu SQL, chưa chạy xuống DB.

    # q luôn có trong filters (mặc định là ''), chuỗi rỗng thì không lọc
    if filters['q']:
        # autoescape=True: coi % và _ là chữ thường, không phải ký tự đặc biệt của LIKE
        name_matches = Product.name.icontains(filters['q'], autoescape=True)
        query = query.filter(name_matches)

    # Các bộ lọc dưới đây chỉ có trong filters khi người dùng gửi lên
    if 'category_id' in filters:
        # any(): giữ product có ít nhất một category trùng id này
        has_category = Product.categories.any(Category.id == filters['category_id'])
        query = query.filter(has_category)

    if 'min_price' in filters:
        query = query.filter(Product.price >= filters['min_price'])

    if 'max_price' in filters:
        query = query.filter(Product.price <= filters['max_price'])

    return query


def sort_products(query, sort_key):
    # sort_key là 'price' (tăng dần) hoặc '-price' (giảm dần)
    column_name = sort_key.lstrip('-')
    column = PRODUCT_SORT_COLUMNS[column_name]

    # Xếp thêm theo id để các dòng trùng giá hay trùng tên luôn giữ một thứ tự,
    # không thì sang trang sau có thể gặp lại dòng đã thấy ở trang trước
    if sort_key.startswith('-'):
        return query.order_by(column.desc(), Product.id.desc())
    return query.order_by(column.asc(), Product.id.asc())


def find_categories_or_422(category_ids):
    # Không gửi category nào thì product không thuộc category nào
    if not category_ids:
        return []

    categories = Category.query.filter(Category.id.in_(category_ids)).all()

    # So id gửi lên với id tìm thấy trong DB để biết id nào không tồn tại
    found_ids = [category.id for category in categories]
    missing_ids = []
    for category_id in category_ids:
        if category_id not in found_ids:
            missing_ids.append(category_id)

    if missing_ids:
        # Cùng dạng lỗi với schema để frontend chỉ phải xử lý một kiểu lỗi 422
        errors = {'category_ids': [f'Unknown category ids: {missing_ids}']}
        raise ApiError('Validation failed', 422, errors)

    return categories


def find_product_or_404(product_id):
    # db.session.get tìm theo khoá chính (id), không thấy thì trả về None
    product = db.session.get(Product, product_id)
    if product is None:
        raise ApiError('Product not found', 404)
    return product


def build_products_from_import_rows(raw_rows):
    categories_by_name = {category.name.lower(): category for category in Category.query.all()}
    valid_rows = []
    row_errors = []
    for row_number, raw_row in raw_rows:
        payload, categories, errors = convert_import_row(raw_row, categories_by_name)
        try:
            data = CreateProductSchema().load(payload)
        except ValidationError as error:
            errors.update(error.messages)
        if errors:
            row_errors.append({'row': row_number, 'errors': errors})
        else:
            valid_rows.append((data, categories))
    if row_errors:
        raise ApiError('Validation failed', 422, {'rows': row_errors})
    return [
        Product(
            name=data['name'],
            description=data.get('description'),
            price=data['price'],
            quantity=data['quantity'],
            categories=categories,
        )
        for data, categories in valid_rows
    ]

# Public: summary
@products_bp.route('/summary', methods=['GET'])
def summary():
    # Một câu SQL tính cả 3 số:
    # SELECT COUNT(id), SUM(quantity), SUM(price * quantity) FROM product
    summary_query = db.session.query(
        db.func.count(Product.id),
        db.func.sum(Product.quantity),
        db.func.sum(Product.price * Product.quantity),
    )
    # one(): chạy SQL và lấy đúng một dòng kết quả, gồm 3 giá trị theo thứ tự trên
    total_products, total_quantity, total_inventory_value = summary_query.one()

    # Bảng chưa có product nào thì SUM trả về NULL (None trong Python)
    if total_quantity is None:
        total_quantity = 0
    if total_inventory_value is None:
        total_inventory_value = 0

    # MySQL trả SUM của cột số nguyên dạng Decimal, JSON sẽ in ra chuỗi "13".
    # Đổi về int và float để API luôn trả về số.
    total_quantity = int(total_quantity)
    # Cột price là kiểu Float nên tổng có thể lệch ở số lẻ xa, làm tròn 2 chữ số
    total_inventory_value = round(float(total_inventory_value), 2)

    summary_data = {
        'total_products': total_products,
        'total_quantity': total_quantity,
        'total_inventory_value': total_inventory_value,
    }
    return build_success_response(summary_data)

# Public: list all products
@products_bp.route('', methods=['GET'])
def list_products():
    # Đọc và kiểm tra query string (?q=...&min_price=...&sort=...), sai thì trả 422
    filters = load_query_args(ListProductsQuerySchema())

    # selectinload: lấy luôn categories của các product bằng một câu SQL phụ,
    # tránh mỗi product phải gọi DB thêm một lần khi đọc product.categories
    query = Product.query.options(selectinload(Product.categories))
    query = filter_products(query, filters)
    query = sort_products(query, filters['sort'])

    # Tới đây mới chạy SQL: lấy một trang product và đếm tổng số dòng
    rows, meta = paginate_query(query, serialize_product)
    return build_success_response(rows, meta=meta)

# Public: show single product
@products_bp.route('/<int:product_id>', methods=['GET'])
def show_product(product_id):
    product = db.session.get(Product, product_id)
    serialized_product = serialize_product(product)
    return build_success_response(serialized_product)

# Admin: export products as an Excel file
@products_bp.route('/export', methods=['GET'])
@role_required('admin')
def export_products():
    # Dùng chung bộ lọc với API list (?q=...&category_id=...&sort=...)
    # để file tải về khớp với danh sách admin đang xem. Gửi sai thì trả 422.
    filters = load_query_args(ListProductsQuerySchema())

    query = Product.query.options(selectinload(Product.categories))
    query = filter_products(query, filters)
    query = sort_products(query, filters['sort'])
    # all(): lấy hết mọi dòng khớp bộ lọc, không chia trang như API list
    products = query.all()

    excel_file = build_products_export(products)
    filename = build_export_filename(date.today())

    # as_attachment=True: trình duyệt tải file về máy thay vì mở ra xem
    return send_file(
        excel_file,
        mimetype=XLSX_MIMETYPE,
        as_attachment=True,
        download_name=filename,
    )

# Admin: create new product
@products_bp.route('', methods=['POST'])
@role_required('admin')
def create_product():
    # Đọc body JSON rồi kiểm bằng schema, sai thì tự trả lỗi 400 hoặc 422
    data = load_json_body(CreateProductSchema())

    # category_ids không phải cột của bảng product nên xử lý riêng
    categories = find_categories_or_422(data['category_ids'])

    product = Product(
        name=data['name'],
        # description không bắt buộc nên dùng get(), không gửi thì là None
        description=data.get('description'),
        price=data['price'],
        quantity=data['quantity'],
    )
    # Gán list category, khi commit SQLAlchemy tự thêm dòng vào bảng nối product_category
    product.categories = categories

    # add: đưa product vào phiên làm việc của DB; commit: ghi thật xuống DB
    db.session.add(product)
    db.session.commit()

    # 201: mã HTTP cho "đã tạo mới thành công"
    serialized_product = serialize_product(product)
    return build_success_response(serialized_product, 'Product created', 201)

# Admin: download the Excel template used by import
@products_bp.route('/import-template', methods=['GET'])
@role_required('admin')
def download_import_template():
    category_names = [category.name for category in Category.query.order_by(Category.name)]
    template = build_import_template(category_names, date.today())
    return send_file(
        template, mimetype=XLSX_MIMETYPE, as_attachment=True, download_name=TEMPLATE_FILENAME,
    )

# Admin: import products from the Excel template
@products_bp.route('/import', methods=['POST'])
@role_required('admin')
def import_products():
    upload = request.files.get('file')
    if upload is None:
        raise ApiError('Validation failed', 422, {'file': ['Send the .xlsx file in the "file" field']})
    products = build_products_from_import_rows(read_import_rows(upload.read()))
    db.session.add_all(products)
    db.session.commit()
    return build_success_response({'created_count': len(products)}, 'Products imported', 201)

# Admin: update product (PUT/PATCH)
@products_bp.route('/<int:product_id>', methods=['PUT', 'PATCH'])
@role_required('admin')
def update_product(product_id):
    product = find_product_or_404(product_id)
    data = load_json_body(UpdateProductSchema())

    # Xử lý category trước các field khác: id sai thì báo lỗi khi product chưa bị đổi gì.
    # Gán list mới thay list cũ, SQLAlchemy tự sửa các dòng ở bảng nối product_category.
    if 'category_ids' in data:
        product.categories = find_categories_or_422(data['category_ids'])

    # Chỉ sửa những field có trong body, field không gửi giữ nguyên
    if 'name' in data:
        product.name = data['name']
    if 'description' in data:
        product.description = data['description']
    if 'price' in data:
        product.price = data['price']
    if 'quantity' in data:
        product.quantity = data['quantity']

    # product được lấy từ DB nên session đã biết nó, không cần db.session.add
    db.session.commit()

    serialized_product = serialize_product(product)
    return build_success_response(serialized_product, 'Product updated')

# Admin: delete product
@products_bp.route('/<int:product_id>', methods=['DELETE'])
@role_required('admin')
def delete_product(product_id):
    product = find_product_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    return build_success_response(message='Product deleted')
