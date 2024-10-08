from . import app_views
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from api import db
from models.user import User


@app_views.route("/user", methods=["GET"])
@jwt_required()
def get_user():
    data = request.get_json()
    email = data.get("email")
    user_id = data.get("id")
    if user_id:
        user = User.query.get(user_id)
    elif email:
        user = User.query.filter_by(email=email).first()
    else:
        return (
            jsonify(
                {
                    "error": "MISSING_CRITERIA",
                    "message": "Please provide a valid ID or email.",
                }
            ),
            400,
        )

    if user:
        return jsonify({"user": user.to_dict()}), 200
    else:
        return jsonify({"error": "USER_NOT_FOUND", "message": "User not found."}), 404


@app_views.route("/update_user/<user_id>", methods=["PUT"])
@jwt_required()
def update_user(user_id):
    current_user_id = get_jwt_identity()

    if current_user_id != user_id:
        return (
            jsonify(
                {
                    "error": "UNAUTHORIZED",
                    "message": "You can only update your own information.",
                }
            ),
            403,
        )

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "USER_NOT_FOUND", "message": "User not found."}), 404
    try:
        data = request.get_json()

        user.full_name = data.get("full_name", user.full_name)
        user.phone_number = data.get("phone_number", user.phone_number)
        user.gender = data.get("gender", user.gender)
        user.address = data.get("address", user.address)
        user.age = data.get("age", user.age)

        db.session.commit()
        return (
            jsonify({"message": "User updated successfully!", "user": user.to_dict()}),
            200,
        )
    except Exception as e:
        return jsonify({"error": "INTERNAL_SERVER_ERROR", "message": str(e)}), 500


@app_views.route("/delete_user/<user_id>", methods=["DELETE"])
@jwt_required()
def delete_user(user_id):
    current_user_id = get_jwt_identity()

    if current_user_id != user_id:
        return (
            jsonify(
                {
                    "error": "UNAUTHORIZED",
                    "message": "You can only delete your own account.",
                }
            ),
            403,
        )

    user = User.query.get(user_id)

    if not user:
        return jsonify({"error": "USER_NOT_FOUND", "message": "User not found."}), 404

    try:
        db.session.delete(user)
        db.session.commit()
        jti = get_jwt()["jti"]
        expires_in = get_jwt()["exp"] - get_jwt()["iat"]
        from api.app import add_token_to_blocklist

        add_token_to_blocklist(jti, expires_in)
        return jsonify({"message": f"User {user_id} successfully deleted!"}), 200
    except Exception as e:
        return jsonify({"error": "INTERNAL_SERVER_ERROR", "message": str(e)}), 500
