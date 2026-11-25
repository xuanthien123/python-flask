import os
from flask import Flask, jsonify

def create_app():
    app = Flask(__name__)
    # Load configuration from Config class
    app.config.from_object('app.config.Config')

    # Initialise extensions
    from .extensions import db, migrate, jwt
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # Register blueprints
    from .modules.users.routes import users_bp
    app.register_blueprint(users_bp)

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

    # Create tables if they don't exist
    # Initialise database tables – ignore if they already exist
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            app.logger.warning(f'DB init warning: {e}')
    return app
