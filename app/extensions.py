from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_mail import Mail

# Extension instances – initialise in the app factory

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
mail = Mail()