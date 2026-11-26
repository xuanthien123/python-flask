import os
from flask import Flask, jsonify

def create_app(config_object='app.config.Config'):
    app = Flask(__name__)
    app.config.from_object(config_object)

    # Initialise extensions
    from .extensions import db, migrate, jwt, mail
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    mail.init_app(app)

    from .common.errors import register_error_handlers
    register_error_handlers(app)

    from .security.token_blocklist import register_token_blocklist
    register_token_blocklist()

    # Register blueprints
    from .modules.users.routes import users_bp
    from .modules.auth.routes import auth_bp
    from .modules.categories.routes import categories_bp
    from .modules.products.routes import products_bp
    app.register_blueprint(users_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(categories_bp)
    app.register_blueprint(products_bp)

    # Health check endpoint that also verifies DB connectivity
    @app.route('/health', methods=['GET'])
    def health():
        try:
            # simple query to ensure DB reachable
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))
            return jsonify({'status': 'ok', 'db': 'connected'})
        except Exception as exc:
            return jsonify({'status': 'error', 'db': str(exc)}), 500

    return app
