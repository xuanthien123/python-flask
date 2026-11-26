from flask import request
from marshmallow import ValidationError

from .errors import ApiError


def load_json_body(schema):
    payload = request.get_json(silent=True)
    if payload is None:
        raise ApiError('Request body must be JSON', 400)
    return load_payload(schema, payload)


def load_optional_json_body(schema):
    return load_payload(schema, request.get_json(silent=True) or {})


def load_query_args(schema):
    return load_payload(schema, request.args.to_dict())


def load_payload(schema, payload):
    try:
        return schema.load(payload)
    except ValidationError as error:
        raise ApiError('Validation failed', 422, error.messages)
