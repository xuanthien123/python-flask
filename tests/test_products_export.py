from datetime import date
from io import BytesIO

from openpyxl import load_workbook

from app.extensions import db
from app.models import Category, Product
from app.modules.products.excel import XLSX_MIMETYPE

EXPORT_URL = '/api/products/export'
EXPORT_HEADERS = ['id', 'name', 'description', 'price', 'quantity', 'categories']


def create_category_row(name):
    category = Category(name=name)
    db.session.add(category)
    db.session.commit()
    return category


def create_product_row(name, price, quantity=0, categories=None, description=None):
    product = Product(name=name, price=price, quantity=quantity, description=description)
    if categories:
        product.categories = categories
    db.session.add(product)
    db.session.commit()
    return product


def read_export_sheet(response):
    workbook = load_workbook(BytesIO(response.data))
    return workbook['Products']


def read_sheet_rows(sheet):
    rows = []
    for row in sheet.iter_rows(values_only=True):
        rows.append(list(row))
    return rows


def test_export_requires_admin_token(client):
    assert client.get(EXPORT_URL).status_code == 401


def test_export_forbidden_for_non_admin(client, non_admin_auth_headers):
    assert client.get(EXPORT_URL, headers=non_admin_auth_headers).status_code == 403


def test_export_downloads_xlsx_with_dated_filename(client, admin_auth_headers):
    response = client.get(EXPORT_URL, headers=admin_auth_headers)

    assert response.status_code == 200
    assert response.mimetype == XLSX_MIMETYPE
    content_disposition = response.headers['Content-Disposition']
    assert 'attachment' in content_disposition
    expected_filename = f'products_{date.today().strftime("%Y%m%d")}.xlsx'
    assert expected_filename in content_disposition


def test_export_empty_table_has_only_header(client, admin_auth_headers):
    response = client.get(EXPORT_URL, headers=admin_auth_headers)

    sheet = read_export_sheet(response)
    rows = read_sheet_rows(sheet)
    assert rows == [EXPORT_HEADERS]


def test_export_lists_products_with_categories(client, admin_auth_headers):
    phone = create_category_row('Phone')
    laptop = create_category_row('Laptop')
    charger = create_product_row(
        'USB-C Charger', 25.5, 100, [phone, laptop], 'Charges laptops and phones',
    )
    mouse = create_product_row('Mouse', 12, 40)

    response = client.get(EXPORT_URL, headers=admin_auth_headers)

    sheet = read_export_sheet(response)
    rows = read_sheet_rows(sheet)
    # Product không có description hay category thì ô để trống, đọc lại là None
    assert rows == [
        EXPORT_HEADERS,
        [charger.id, 'USB-C Charger', 'Charges laptops and phones', 25.5, 100, 'Laptop, Phone'],
        [mouse.id, 'Mouse', None, 12, 40, None],
    ]


def test_export_applies_list_filters_and_sort(client, admin_auth_headers):
    phone = create_category_row('Phone')
    create_product_row('Cheap phone', 50, categories=[phone])
    create_product_row('Phone case', 5, categories=[phone])
    create_product_row('Phone sticker', 0.5, categories=[phone])
    create_product_row('Laptop', 900)

    response = client.get(
        f'{EXPORT_URL}?category_id={phone.id}&min_price=1&sort=-price',
        headers=admin_auth_headers,
    )

    sheet = read_export_sheet(response)
    rows = read_sheet_rows(sheet)
    exported_names = []
    for row in rows[1:]:
        exported_names.append(row[1])
    assert exported_names == ['Cheap phone', 'Phone case']


def test_export_rejects_invalid_filter(client, admin_auth_headers):
    response = client.get(f'{EXPORT_URL}?sort=unknown', headers=admin_auth_headers)

    assert response.status_code == 422
    assert response.get_json()['success'] is False


def test_export_writes_formula_like_name_as_plain_text(client, admin_auth_headers):
    create_product_row('=HYPERLINK("http://evil.test","click")', 1)

    response = client.get(EXPORT_URL, headers=admin_auth_headers)

    sheet = read_export_sheet(response)
    name_cell = sheet['B2']
    assert name_cell.value == '=HYPERLINK("http://evil.test","click")'
    assert name_cell.data_type == 's'
