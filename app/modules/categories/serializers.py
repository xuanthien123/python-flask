def serialize_category(category):
    return {
        'id': category.id,
        'name': category.name,
        'description': category.description,
    }
