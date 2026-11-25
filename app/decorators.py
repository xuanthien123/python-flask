"""Utility decorators for role‑based access control.
Only a thin wrapper around Flask‑JWT‑Extended claims – adjust to your needs.
"""

from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt


def role_required(role: str):
    """Require a specific role claim in the JWT.
    Usage::
        @role_required('admin')
        def my_view():
            ...
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get('role') != role:
                return jsonify({'error': 'Forbidden – insufficient role'}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator
