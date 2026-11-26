from io import BytesIO

from openpyxl import Workbook, load_workbook

from app.extensions import db
from app.models import Category, Product
from app.modules.products.excel import MAX_IMPORT_ROWS, PRODUCT_HEADERS

TEMPLATE_URL = '/api/products/import-template'
IMPORT_URL = '/api/products/import'


def create_category_row(name):
    category = Category(name=name)
    db.session.add(category)
    db.session.commit()
    return category


def build_xlsx_bytes(rows, headers=PRODUCT_HEADERS, sheet_title='Products'):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = sheet_title
    sheet.append(headers)
    for row in rows:
        sheet.append(row)
    stream = BytesIO()
    workbook.save(stream)
    return stream.getvalue()


def post_import(client, headers, file_bytes):
    return client.post(
        IMPORT_URL,
        data={'file': (BytesIO(file_bytes), 'products.xlsx')},
        headers=headers,
        content_type='multipart/form-data',
    )


def fill_sheet_row(sheet, row_number, values):
    for column_index, value in enumerate(values, start=1):
        sheet.cell(row=row_number, column=column_index, value=value)


def read_category_names(product):
    return sorted(category.name for category in product.categories)


def test_import_template_requires_admin_token(client):
    assert client.get(TEMPLATE_URL).status_code == 401


def test_import_template_forbidden_for_non_admin(client, non_admin_auth_headers):
    assert client.get(TEMPLATE_URL, headers=non_admin_auth_headers).status_code == 403


def test_import_template_lists_current_categories(client, admin_auth_headers):
    create_category_row('Phone')
    create_category_row('Laptop')
    response = client.get(TEMPLATE_URL, headers=admin_auth_headers)
    assert response.status_code == 200
    assert response.mimetype.endswith('spreadsheetml.sheet')
    assert 'product_import_template.xlsx' in response.headers['Content-Disposition']

    workbook = load_workbook(BytesIO(response.get_data()))
    assert workbook.sheetnames == ['Products', 'Instructions', 'Categories']
    assert workbook['Categories'].sheet_state == 'hidden'
    category_cells = workbook['Categories']['A2:A3']
    assert [row[0].value for row in category_cells] == ['Laptop', 'Phone']
    products_sheet = workbook['Products']
    assert [cell.value for cell in products_sheet[1]] == PRODUCT_HEADERS
    list_formulas = [
        validation.formula1 for validation in products_sheet.data_validations.dataValidation
        if validation.type == 'list'
    ]
    assert list_formulas == ['=Categories!$A$2:$A$3']


def test_import_creates_products_from_filled_template(client, admin_auth_headers):
    create_category_row('Laptop')
    create_category_row('Phone')
    template = client.get(TEMPLATE_URL, headers=admin_auth_headers).get_data()
    workbook = load_workbook(BytesIO(template))
    sheet = workbook['Products']
    fill_sheet_row(sheet, 2, [
        '  USB-C Charger 65W ', 'Charges laptops and phones', 25, None, 'Laptop', 'phone', 'Laptop',
    ])
    fill_sheet_row(sheet, 4, ['Mouse Pad', None, 3.5, 12])
    fill_sheet_row(sheet, 5, [1984, None, 9, 1])
    stream = BytesIO()
    workbook.save(stream)

    response = post_import(client, admin_auth_headers, stream.getvalue())

    assert response.status_code == 201
    assert response.get_json()['data'] == {'created_count': 3}
    charger, mouse_pad, book = Product.query.order_by(Product.id).all()
    assert charger.name == 'USB-C Charger 65W'
    assert charger.quantity == 0
    assert read_category_names(charger) == ['Laptop', 'Phone']
    assert (mouse_pad.price, mouse_pad.quantity, mouse_pad.categories) == (3.5, 12, [])
    assert book.name == '1984'


def test_import_reports_errors_by_row_and_saves_nothing(client, admin_auth_headers):
    create_category_row('Laptop')
    file_bytes = build_xlsx_bytes([
        ['Charger', None, 25, 1, 'Laptop'],
        ['Pen', None, -1, None, 'Tablet'],
        [None, 'No name', 5, 2.5],
    ])

    response = post_import(client, admin_auth_headers, file_bytes)

    assert response.status_code == 422
    row_errors = response.get_json()['errors']['rows']
    assert [row_error['row'] for row_error in row_errors] == [3, 4]
    assert set(row_errors[0]['errors']) == {'price', 'category_1'}
    assert set(row_errors[1]['errors']) == {'name', 'quantity'}
    assert Product.query.count() == 0


def test_import_requires_file(client, admin_auth_headers):
    response = client.post(
        IMPORT_URL, data={}, headers=admin_auth_headers, content_type='multipart/form-data',
    )
    assert response.status_code == 422
    assert 'file' in response.get_json()['errors']


def test_import_rejects_file_that_is_not_xlsx(client, admin_auth_headers):
    response = post_import(client, admin_auth_headers, b'name,price\nPen,1\n')
    assert response.status_code == 422
    assert 'file' in response.get_json()['errors']


def test_import_rejects_wrong_header(client, admin_auth_headers):
    file_bytes = build_xlsx_bytes([['Pen', 1]], headers=['title', 'price'])
    response = post_import(client, admin_auth_headers, file_bytes)
    assert response.status_code == 422
    assert 'file' in response.get_json()['errors']


def test_import_rejects_missing_products_sheet(client, admin_auth_headers):
    file_bytes = build_xlsx_bytes([['Pen', None, 1]], sheet_title='Sheet1')
    response = post_import(client, admin_auth_headers, file_bytes)
    assert response.status_code == 422
    assert 'file' in response.get_json()['errors']


def test_import_rejects_file_without_products(client, admin_auth_headers):
    response = post_import(client, admin_auth_headers, build_xlsx_bytes([]))
    assert response.status_code == 422
    assert 'file' in response.get_json()['errors']


def test_import_rejects_more_rows_than_limit(client, admin_auth_headers):
    rows = [['Pen', None, 1, 1]] * (MAX_IMPORT_ROWS + 1)
    response = post_import(client, admin_auth_headers, build_xlsx_bytes(rows))
    assert response.status_code == 422
    assert 'file' in response.get_json()['errors']
    assert Product.query.count() == 0


def test_import_forbidden_for_non_admin(client, non_admin_auth_headers):
    response = post_import(client, non_admin_auth_headers, build_xlsx_bytes([['Pen', None, 1]]))
    assert response.status_code == 403
