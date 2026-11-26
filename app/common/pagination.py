from flask import request


def read_pagination_args(default_per_page=20, max_per_page=100):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', default_per_page, type=int)
    return max(page, 1), min(max(per_page, 1), max_per_page)


def paginate_query(query, serialize_row):
    page, per_page = read_pagination_args()
    result = query.paginate(page=page, per_page=per_page, error_out=False)
    rows = [serialize_row(row) for row in result.items]
    meta = {
        'page': result.page,
        'per_page': result.per_page,
        'total': result.total,
        'pages': result.pages,
    }
    return rows, meta
