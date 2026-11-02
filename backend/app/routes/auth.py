from flask import Blueprint, request, jsonify

from flask_jwt_extended import (
    create_access_token
)

from app.extensions import db

from app.models.user import User

from app.utils.security import (
    hash_password,
    verify_password
)

auth_bp = Blueprint(
    "auth",
    __name__,
    url_prefix="/api/auth"
)


@auth_bp.route("/register", methods=["POST"])
def register():

    data = request.get_json()

    if User.query.filter_by(
        email=data["email"]
    ).first():

        return jsonify({
            "message": "Email already exists"
        }), 400

    user = User(
        username=data["username"],
        email=data["email"],
        password=hash_password(
            data["password"]
        )
    )

    db.session.add(user)

    db.session.commit()

    return jsonify({
        "message": "User Registered"
    })


@auth_bp.route("/login", methods=["POST"])
def login():

    data = request.get_json()

    user = User.query.filter_by(
        email=data["email"]
    ).first()

    if not user:

        return jsonify({
            "message": "Invalid Credentials"
        }), 401

    if not verify_password(
        user.password,
        data["password"]
    ):

        return jsonify({
            "message": "Invalid Credentials"
        }), 401

    token = create_access_token(
        identity=user.id
    )

    return jsonify({
        "access_token": token
    })