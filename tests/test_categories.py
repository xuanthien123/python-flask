import app.modules.categories.routes as category_routes
from app.extensions import db
from app.models import Category, Product


def create_category_row(name='Books'):
    category = Category(name=name)
    db.session.add(category)
    db.session.commit()
    return category


def test_list_categories_is_public_and_paginated(client):
    create_category_row('Books')
    create_category_row('Toys')
    response = client.get('/api/categories?per_page=1')
    body = response.get_json()
    assert response.status_code == 200
    assert [row['name'] for row in body['data']] == ['Books']
    assert body['meta']['total'] == 2


def test_list_categories_filters_by_name(client):
    create_category_row('Books')
    create_category_row('Toys')
    body = client.get('/api/categories?q=toy').get_json()
    assert [row['name'] for row in body['data']] == ['Toys']


def test_get_category_returns_row(client):
    category = create_category_row('Books')
    response = client.get(f'/api/categories/{category.id}')
    assert response.status_code == 200
    assert response.get_json()['data']['name'] == 'Books'


def test_get_category_returns_404_when_missing(client):
    response = client.get('/api/categories/999')
    assert response.status_code == 404
    assert response.get_json()['success'] is False


def test_create_category_requires_admin_token(client):
    response = client.post('/api/categories', json={'name': 'Books'})
    assert response.status_code == 401


def test_create_category_forbidden_for_non_admin(client, non_admin_auth_headers):
    response = client.post(
        '/api/categories', json={'name': 'Books'}, headers=non_admin_auth_headers,
    )
    body = response.get_json()
    assert response.status_code == 403
    assert body['success'] is False
    assert body['message']


def test_create_category_saves_row(client, admin_auth_headers):
    response = client.post(
        '/api/categories', json={'name': 'Books', 'description': 'Paper'},
        headers=admin_auth_headers,
    )
    assert response.status_code == 201
    assert response.get_json()['data']['name'] == 'Books'
    assert Category.query.count() == 1


def test_create_category_rejects_duplicate_name(client, admin_auth_headers):
    create_category_row('Books')
    response = client.post(
        '/api/categories', json={'name': 'books'}, headers=admin_auth_headers,
    )
    assert response.status_code == 409


def test_create_category_rejects_missing_name(client, admin_auth_headers):
    response = client.post('/api/categories', json={}, headers=admin_auth_headers)
    assert response.status_code == 422


def test_create_category_trims_name(client, admin_auth_headers):
    response = client.post(
        '/api/categories', json={'name': '  Books  '}, headers=admin_auth_headers,
    )
    assert response.status_code == 201
    assert response.get_json()['data']['name'] == 'Books'


def test_create_category_rejects_blank_name(client, admin_auth_headers):
    response = client.post(
        '/api/categories', json={'name': '   '}, headers=admin_auth_headers,
    )
    assert response.status_code == 422


def test_create_category_rejects_name_differing_only_by_spaces(
    client, admin_auth_headers,
):
    create_category_row('Books')
    response = client.post(
        '/api/categories', json={'name': ' Books '}, headers=admin_auth_headers,
    )
    assert response.status_code == 409


def test_create_category_returns_409_when_db_rejects_duplicate(
    client, admin_auth_headers, monkeypatch,
):
    create_category_row('Books')
    monkeypatch.setattr(category_routes, 'ensure_name_is_free', lambda *args, **kwargs: None)
    response = client.post(
        '/api/categories', json={'name': 'Books'}, headers=admin_auth_headers,
    )
    assert response.status_code == 409
    assert Category.query.count() == 1


def test_update_category_changes_name(client, admin_auth_headers):
    category = create_category_row('Books')
    response = client.patch(
        f'/api/categories/{category.id}', json={'name': 'Novels'},
        headers=admin_auth_headers,
    )
    assert response.status_code == 200
    assert response.get_json()['data']['name'] == 'Novels'


def test_update_category_rejects_name_of_other_category(client, admin_auth_headers):
    create_category_row('Books')
    other = create_category_row('Toys')
    response = client.put(
        f'/api/categories/{other.id}', json={'name': 'Books'},
        headers=admin_auth_headers,
    )
    assert response.status_code == 409


def test_update_category_rejects_blank_name(client, admin_auth_headers):
    category = create_category_row('Books')
    response = client.patch(
        f'/api/categories/{category.id}', json={'name': '   '},
        headers=admin_auth_headers,
    )
    assert response.status_code == 422


def test_update_category_returns_409_when_db_rejects_duplicate(
    client, admin_auth_headers, monkeypatch,
):
    create_category_row('Books')
    other = create_category_row('Toys')
    monkeypatch.setattr(category_routes, 'ensure_name_is_free', lambda *args, **kwargs: None)
    response = client.patch(
        f'/api/categories/{other.id}', json={'name': 'Books'},
        headers=admin_auth_headers,
    )
    assert response.status_code == 409
    assert db.session.get(Category, other.id).name == 'Toys'


def test_update_category_returns_404_when_missing(client, admin_auth_headers):
    response = client.patch(
        '/api/categories/999', json={'name': 'X'}, headers=admin_auth_headers,
    )
    assert response.status_code == 404


def test_delete_category_removes_row(client, admin_auth_headers):
    category = create_category_row('Books')
    response = client.delete(f'/api/categories/{category.id}', headers=admin_auth_headers)
    assert response.status_code == 200
    assert Category.query.count() == 0


def test_delete_category_blocked_when_it_has_products(client, admin_auth_headers):
    category = create_category_row('Books')
    product = Product(name='Novel', price=10)
    product.categories.append(category)
    db.session.add(product)
    db.session.commit()
    response = client.delete(f'/api/categories/{category.id}', headers=admin_auth_headers)
    assert response.status_code == 409
