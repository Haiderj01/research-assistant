from flask import jsonify
from backend.controllers._helpers import require_json_body
from backend.services import auth_service


def handle_register():
    body = require_json_body()

    email = body.get("email")
    password = body.get("password")
    name = body.get("name")

    result = auth_service.register_user(email, password, name)

    return jsonify({
        "success": True,
        "data": {
            "token": result["token"],
            "user": result["user"],
        },
        "message": "Account created successfully.",
    }), 201


def handle_login():
    body = require_json_body()

    email = body.get("email")
    password = body.get("password")

    result = auth_service.login_user(email, password)

    return jsonify({
        "success": True,
        "data": {
            "token": result["token"],
            "user": result["user"],
        },
        "message": "Login successful.",
    }), 200
