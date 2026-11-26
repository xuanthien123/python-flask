from app.extensions import db
from app.models import Category, Product, product_category


def create_product_row(name, price=10, categories=(), quantity=0):
    product = Product(name=name, price=price, quantity=quantity)
    product.categories.extend(categories)
    db.session.add(product)
    db.session.commit()
    return product


def create_category_row(name):
    category = Category(name=name)
    db.session.add(category)
    db.session.commit()
    return category


def read_product_names(response):
    return [row['name'] for row in response.get_json()['data']]


def test_list_products_is_public_and_paginated(client):
    create_product_row('Novel')
    create_product_row('Puzzle')
    response = client.get('/api/products?per_page=1')
    body = response.get_json()
    assert response.status_code == 200
    assert read_product_names(response) == ['Novel']
    assert body['meta']['total'] == 2


def test_list_products_includes_categories(client):
    books = create_category_row('Books')
    create_product_row('Novel', categories=[books])
    row = client.get('/api/products').get_json()['data'][0]
    assert row['categories'] == [{'id': books.id, 'name': 'Books'}]


def test_list_products_searches_name_ignoring_case(client):
    create_product_row('Novel')
    create_product_row('Puzzle')
    assert read_product_names(client.get('/api/products?q=NOV')) == ['Novel']


def test_list_products_treats_percent_in_search_as_text(client):
    create_product_row('Novel')
    create_product_row('100% Cotton Shirt')
    response = client.get('/api/products?q=%25')
    assert read_product_names(response) == ['100% Cotton Shirt']


def test_list_products_filters_by_category(client):
    books = create_category_row('Books')
    create_product_row('Novel', categories=[books])
    create_product_row('Puzzle')
    response = client.get(f'/api/products?category_id={books.id}')
    assert read_product_names(response) == ['Novel']


def test_list_products_filters_by_price_range(client):
    create_product_row('Pen', price=5)
    create_product_row('Novel', price=10)
    create_product_row('Puzzle', price=20)
    response = client.get('/api/products?min_price=6&max_price=15')
    assert read_product_names(response) == ['Novel']


def test_list_products_sorts_by_price_descending(client):
    create_product_row('Pen', price=5)
    create_product_row('Puzzle', price=20)
    create_product_row('Novel', price=10)
    response = client.get('/api/products?sort=-price')
    assert read_product_names(response) == ['Puzzle', 'Novel', 'Pen']


def test_list_products_rejects_price_that_is_not_a_number(client):
    response = client.get('/api/products?min_price=abc')
    assert response.status_code == 422
    assert 'min_price' in response.get_json()['errors']


def test_list_products_rejects_min_price_above_max_price(client):
    response = client.get('/api/products?min_price=20&max_price=10')
    assert response.status_code == 422
    assert 'min_price' in response.get_json()['errors']


def test_list_products_rejects_unknown_sort(client):
    response = client.get('/api/products?sort=stock')
    assert response.status_code == 422
    assert 'sort' in response.get_json()['errors']


def test_create_product_requires_admin_token(client):
    response = client.post('/api/products', json={'name': 'Novel', 'price': 10})
    assert response.status_code == 401


def test_create_product_forbidden_for_non_admin(client, non_admin_auth_headers):
    response = client.post(
        '/api/products', json={'name': 'Novel', 'price': 10}, headers=non_admin_auth_headers,
    )
    assert response.status_code == 403
    assert response.get_json()['success'] is False


def test_create_product_saves_row_with_categories(client, admin_auth_headers):
    books = create_category_row('Books')
    books_id = books.id
    response = client.post(
        '/api/products',
        json={
            'name': '  Novel ',
            'description': 'Paper',
            'price': 12.5,
            'quantity': 7,
            'category_ids': [books_id],
        },
        headers=admin_auth_headers,
    )
    body = response.get_json()
    assert response.status_code == 201
    assert body['data']['name'] == 'Novel'
    assert body['data']['price'] == 12.5
    assert body['data']['quantity'] == 7
    assert body['data']['categories'] == [{'id': books_id, 'name': 'Books'}]
    assert db.session.get(Product, body['data']['id']).description == 'Paper'


def test_create_product_defaults_quantity_to_zero(client, admin_auth_headers):
    response = client.post(
        '/api/products', json={'name': 'Novel', 'price': 10}, headers=admin_auth_headers,
    )
    assert response.status_code == 201
    assert response.get_json()['data']['quantity'] == 0


def test_create_product_rejects_negative_quantity(client, admin_auth_headers):
    response = client.post(
        '/api/products',
        json={'name': 'Novel', 'price': 10, 'quantity': -1},
        headers=admin_auth_headers,
    )
    assert response.status_code == 422
    assert 'quantity' in response.get_json()['errors']


def test_create_product_rejects_fractional_quantity(client, admin_auth_headers):
    response = client.post(
        '/api/products',
        json={'name': 'Novel', 'price': 10, 'quantity': 2.5},
        headers=admin_auth_headers,
    )
    assert response.status_code == 422
    assert 'quantity' in response.get_json()['errors']


def test_create_product_rejects_missing_name_and_price(client, admin_auth_headers):
    response = client.post('/api/products', json={}, headers=admin_auth_headers)
    errors = response.get_json()['errors']
    assert response.status_code == 422
    assert 'name' in errors
    assert 'price' in errors


def test_create_product_rejects_negative_price(client, admin_auth_headers):
    response = client.post(
        '/api/products', json={'name': 'Novel', 'price': -1}, headers=admin_auth_headers,
    )
    assert response.status_code == 422
    assert 'price' in response.get_json()['errors']


def test_create_product_rejects_unknown_category_ids(client, admin_auth_headers):
    response = client.post(
        '/api/products',
        json={'name': 'Novel', 'price': 10, 'category_ids': [999]},
        headers=admin_auth_headers,
    )
    assert response.status_code == 422
    assert 'category_ids' in response.get_json()['errors']
    assert Product.query.count() == 0


def test_update_product_requires_admin_token(client):
    product_id = create_product_row('Novel').id
    response = client.patch(f'/api/products/{product_id}', json={'price': 15})
    assert response.status_code == 401


def test_update_product_forbidden_for_non_admin(client, non_admin_auth_headers):
    product_id = create_product_row('Novel').id
    response = client.patch(
        f'/api/products/{product_id}', json={'price': 15}, headers=non_admin_auth_headers,
    )
    assert response.status_code == 403


def test_update_product_returns_404_when_missing(client, admin_auth_headers):
    response = client.patch('/api/products/999', json={'price': 15}, headers=admin_auth_headers)
    assert response.status_code == 404
    assert response.get_json()['success'] is False


def test_update_product_changes_only_sent_fields(client, admin_auth_headers):
    product_id = create_product_row('Novel', price=10, quantity=3).id
    response = client.patch(
        f'/api/products/{product_id}',
        json={'price': 15, 'quantity': 20},
        headers=admin_auth_headers,
    )
    data = response.get_json()['data']
    assert response.status_code == 200
    assert data['name'] == 'Novel'
    assert data['price'] == 15
    assert data['quantity'] == 20


def test_update_product_replaces_categories(client, admin_auth_headers):
    books = create_category_row('Books')
    toys = create_category_row('Toys')
    toys_id = toys.id
    product_id = create_product_row('Puzzle', categories=[books]).id
    response = client.put(
        f'/api/products/{product_id}', json={'category_ids': [toys_id]}, headers=admin_auth_headers,
    )
    assert response.status_code == 200
    assert response.get_json()['data']['categories'] == [{'id': toys_id, 'name': 'Toys'}]


def test_update_product_removes_categories_with_empty_list(client, admin_auth_headers):
    books = create_category_row('Books')
    product_id = create_product_row('Novel', categories=[books]).id
    response = client.patch(
        f'/api/products/{product_id}', json={'category_ids': []}, headers=admin_auth_headers,
    )
    assert response.status_code == 200
    assert response.get_json()['data']['categories'] == []


def test_update_product_rejects_empty_body(client, admin_auth_headers):
    product_id = create_product_row('Novel').id
    response = client.patch(f'/api/products/{product_id}', json={}, headers=admin_auth_headers)
    assert response.status_code == 422


def test_update_product_with_unknown_category_keeps_product(client, admin_auth_headers):
    product_id = create_product_row('Novel', price=10).id
    response = client.patch(
        f'/api/products/{product_id}',
        json={'price': 99, 'category_ids': [999]},
        headers=admin_auth_headers,
    )
    assert response.status_code == 422
    assert 'category_ids' in response.get_json()['errors']
    assert db.session.get(Product, product_id).price == 10


def test_summary_is_public_and_totals_quantity_and_value(client):
    create_product_row('Pen', price=5, quantity=10)
    create_product_row('Novel', price=10, quantity=3)
    response = client.get('/api/products/summary')
    assert response.status_code == 200
    assert response.get_json()['data'] == {
        'total_products': 2,
        'total_quantity': 13,
        'total_inventory_value': 80.0,
    }


def test_summary_returns_zero_when_no_products(client):
    response = client.get('/api/products/summary')
    assert response.get_json()['data'] == {
        'total_products': 0,
        'total_quantity': 0,
        'total_inventory_value': 0.0,
    }


def test_delete_product_requires_admin_token(client):
    product_id = create_product_row('Novel').id
    response = client.delete(f'/api/products/{product_id}')
    assert response.status_code == 401


def test_delete_product_forbidden_for_non_admin(client, non_admin_auth_headers):
    product_id = create_product_row('Novel').id
    response = client.delete(f'/api/products/{product_id}', headers=non_admin_auth_headers)
    assert response.status_code == 403
    assert Product.query.count() == 1


def test_delete_product_returns_404_when_missing(client, admin_auth_headers):
    response = client.delete('/api/products/999', headers=admin_auth_headers)
    assert response.status_code == 404
    assert response.get_json()['success'] is False


def test_delete_product_removes_row_and_category_links(client, admin_auth_headers):
    books = create_category_row('Books')
    product_id = create_product_row('Novel', categories=[books]).id
    response = client.delete(f'/api/products/{product_id}', headers=admin_auth_headers)
    assert response.status_code == 200
    assert response.get_json()['message'] == 'Product deleted'
    assert Product.query.count() == 0
    assert Category.query.count() == 1
    assert db.session.execute(db.select(product_category)).all() == []
