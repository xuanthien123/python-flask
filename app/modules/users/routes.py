from flask import Blueprint, jsonify, request
from ...models import User
from app.extensions import db

users_bp = Blueprint('users', __name__, url_prefix='/users')

@users_bp.route('', methods=['GET'])
def list_users():
    """Return a JSON list of all usernames."""
    users = User.query.all()
    usernames = [u.email for u in users]
    return jsonify(usernames)

@users_bp.route('', methods=['POST'])
def create_user():
    return

