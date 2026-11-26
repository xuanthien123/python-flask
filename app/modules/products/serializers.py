def serialize_product(product):
    return {
        'id': product.id,
        'name': product.name,
        'description': product.description,
        'price': product.price,
        'quantity': product.quantity,
        'categories': [
            {'id': category.id, 'name': category.name}
            for category in product.categories
        ],
    }
