from flask import jsonify


def build_success_response(data=None, message=None, status_code=200, meta=None):
    body = {'success': True, 'data': data}
    if message:
        body['message'] = message
    if meta is not None:
        body['meta'] = meta
    return jsonify(body), status_code


def build_error_response(message, status_code=400, errors=None, code=None):
    body = {'success': False, 'message': message}
    if code:
        body['code'] = code
    if errors:
        body['errors'] = errors
    return jsonify(body), status_code
