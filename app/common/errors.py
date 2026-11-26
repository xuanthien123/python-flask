from werkzeug.exceptions import HTTPException

from .responses import build_error_response


class ApiError(Exception):
    def __init__(self, message, status_code=400, errors=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.errors = errors


def register_error_handlers(app):
    from app.extensions import jwt

    @app.errorhandler(ApiError)
    def handle_api_error(error):
        return build_error_response(error.message, error.status_code, error.errors)

    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        return build_error_response(error.description, error.code)

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        app.logger.exception('Unhandled error')
        return build_error_response('Internal server error', 500)

    @jwt.unauthorized_loader
    def handle_missing_token(reason):
        return build_error_response('Authentication required', 401, code='token_missing')

    @jwt.invalid_token_loader
    def handle_invalid_token(reason):
        return build_error_response('Invalid token', 401, code='token_invalid')

    @jwt.revoked_token_loader
    def handle_revoked_token(jwt_header, jwt_payload):
        return build_error_response('Token has been revoked', 401, code='token_revoked')

    @jwt.expired_token_loader
    def handle_expired_token(jwt_header, jwt_payload):
        return build_error_response('Token expired', 401, code='token_expired')
