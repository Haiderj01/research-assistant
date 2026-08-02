from flask import request, jsonify
from backend.middlewares.error_handler import AppError
from backend.services import auth_service


def handle_register():
    body = request.get_json(silent=True)
    if body is None:
        raise AppError(
            message="Request body must be valid JSON.",
            status_code=400,
            code="INVALID_JSON",
        )

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
    body = request.get_json(silent=True)
    if body is None:
        raise AppError(
            message="Request body must be valid JSON.",
            status_code=400,
            code="INVALID_JSON",
        )

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
