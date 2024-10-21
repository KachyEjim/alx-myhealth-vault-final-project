from . import app_views
from flask import request, jsonify
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    get_jwt,
)
from api import db
from models.user import User
import jwt
from datetime import datetime, timedelta
from flask_mail import Message
from jwt import ExpiredSignatureError, InvalidTokenError
from api.config import Config


@app_views.route("/signup", methods=["POST"], strict_slashes=False)
def signup():
    data = request.get_json()

    full_name = data.get("full_name")
    phone_number = data.get("phone_number")
    gender = data.get("gender", "Other")
    address = data.get("address")
    email = data.get("email")
    password = data.get("password")
    age = data.get("age")

    if not all([full_name, email, password]):
        return (
            jsonify(
                {
                    "error": "MISSING_FIELDS",
                    "message": "Full name, email, and password are required.",
                }
            ),
            400,
        )

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return (
            jsonify({"error": "USER_EXISTS", "message": "Email is already in use."}),
            400,
        )

    try:
        new_user = User(
            full_name=full_name,
            phone_number=phone_number,
            gender=gender,
            address=address,
            email=email,
            password=password,
            age=age,
        )
        new_user.hash_password()
        db.session.add(new_user)
        db.session.commit()
        # Send verification email after successful registration
        send_verification_email(new_user)

        return (
            jsonify(
                {"message": "User registered successfully! Verification email sent."}
            ),
            201,
        )

    except Exception as e:
        return (
            jsonify(
                {
                    "error": "INTERNAL_SERVER_ERROR",
                    "message": f"An unexpected error occurred. {str(e)}",
                }
            ),
            500,
        )


@app_views.route("/login", methods=["POST"], strict_slashes=False)
def login():
    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    # Retrieve the user from the database by email
    user = User.query.filter_by(email=email).first()

    # Check if the user is verified
    if user and not user.is_verified:
        return (
            jsonify(
                {
                    "error": "USER_NOT_VERIFIED",
                    "message": "Please verify your email address before logging in.",
                }
            ),
            403,
        )  # Forbidden, as user needs verification

    # Check if the user's password is correct
    if user and user.check_password(password):
        # Generate access and refresh tokens with custom claims
        access_token = create_access_token(
            identity=user.id, additional_claims={"role": user.role}
        )
        refresh_token = create_refresh_token(
            identity=user.id, additional_claims={"role": user.role}
        )

        # Return successful login response
        return (
            jsonify(
                {
                    "message": "Login successful",
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "user": user.to_dict(),
                }
            ),
            200,
        )
    else:
        # Return invalid credentials error
        return (
            jsonify(
                {"error": "INVALID_CREDENTIALS", "message": "Invalid email or password"}
            ),
            401,
        )  # Unauthorized, as credentials are incorrect


# Secret key for JWT encoding


def send_verification_email(user):
    token = jwt.encode(
        {
            "user_id": user.id,
            "exp": datetime.utcnow() + timedelta(hours=24),  # Token expires in 24 hours
        },
        Config.SECRET_KEY,
        algorithm="HS256",
    )

    verification_link = (
        f"https://myhealthvault-backend.onrender.com/api/verify-email/{token}"
    )

    msg = Message(
        subject="Email Verification",
        recipients=[user.email],
        body=f"Hi {user.full_name},\n\nPlease verify your email address by clicking the link below:\n\n{verification_link}\n\nIf you did not sign up for this account, please ignore this email.",
    )
    from api.app import mail

    mail.send(msg)

    return (
        jsonify({"message": "Verification email sent. Please check your inbox."}),
        200,
    )


@app_views.route("/verify-email/<token>", methods=["GET"], strict_slashes=False)
def verify_email(token):
    try:
        # Decode the JWT token to get the user ID
        payload = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
        user_id = payload["user_id"]

        # Retrieve the user and mark them as verified
        user = User.query.get(user_id)
        if not user:
            return (
                jsonify({"error": "USER_NOT_FOUND", "message": "User not found"}),
                404,
            )

        user.is_verified = True
        db.session.commit()

        return (
            jsonify({"message": "Email verified successfully. You can now log in."}),
            200,
        )

    except ExpiredSignatureError:
        return (
            jsonify(
                {
                    "error": "TOKEN_EXPIRED",
                    "message": "The verification token has expired",
                }
            ),
            400,
        )

    except InvalidTokenError:
        return (
            jsonify(
                {"error": "INVALID_TOKEN", "message": "Invalid verification token"}
            ),
            400,
        )


@app_views.route("/resend-verification", methods=["POST"], strict_slashes=False)
def resend_verification_email():
    data = request.get_json()

    email = data.get("email")
    user = User.query.filter_by(email=email).first()

    if not user:
        return (
            jsonify(
                {"error": "USER_NOT_FOUND", "message": "No user found with that email."}
            ),
            404,
        )

    if user.is_verified:
        return jsonify({"message": "This account is already verified."}), 400

    send_verification_email(user)
    return (
        jsonify({"message": "Verification email resent. Please check your inbox."}),
        200,
    )


@app_views.route("/reset-password/<token>", methods=["POST"], strict_slashes=False)
def reset_password(token):
    try:
        payload = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
        user_id = payload["user_id"]
        user = User.query.get(user_id)

        data = request.get_json()
        new_password = data.get("new_password")

        if not new_password:
            return (
                jsonify(
                    {
                        "error": "MISSING_PASSWORD",
                        "message": "New password is required.",
                    }
                ),
                400,
            )

        user.password = new_password
        user.hash_password()
        db.session.commit()

        return jsonify({"message": "Password reset successfully."}), 200

    except jwt.ExpiredSignatureError:
        return (
            jsonify(
                {
                    "error": "TOKEN_EXPIRED",
                    "message": "The password reset link has expired.",
                }
            ),
            400,
        )

    except jwt.InvalidTokenError:
        return (
            jsonify(
                {"error": "INVALID_TOKEN", "message": "Invalid password reset token."}
            ),
            400,
        )


@app_views.route("/forgot-password", methods=["POST"], strict_slashes=False)
def forgot_password():
    data = request.get_json()
    email = data.get("email")

    if not email:
        return jsonify({"error": "MISSING_EMAIL", "message": "Email is required."}), 400

    user = User.query.filter_by(email=email).first()

    if not user:
        return (
            jsonify(
                {"error": "USER_NOT_FOUND", "message": "No user found with this email."}
            ),
            404,
        )

    token = jwt.encode(
        {"user_id": user.id, "exp": datetime.utcnow() + timedelta(hours=1)},
        Config.SECRET_KEY,
        algorithm="HS256",
    )
    reset_link = f"http://yourdomain.com/reset-password/{token}"

    msg = Message(
        subject="Password Reset",
        recipients=[email],
        body=f"Click the link to reset your password: {reset_link}",
    )
    from api.app import mail

    mail.send(msg)

    return jsonify({"message": "Password reset email sent."}), 200


@app_views.route("/change-password", methods=["POST"], strict_slashes=False)
@jwt_required()
def change_password():
    user_id = get_jwt_identity()
    data = request.get_json()

    old_password = data.get("old_password")
    new_password = data.get("new_password")

    if not all([old_password, new_password]):
        return (
            jsonify(
                {
                    "error": "MISSING_FIELDS",
                    "message": "Old and new passwords are required.",
                }
            ),
            400,
        )

    user = User.query.get(user_id)

    if user and user.check_password(old_password):
        user.password = new_password
        user.hash_password()
        db.session.commit()
        return jsonify({"message": "Password changed successfully."}), 200
    else:
        return (
            jsonify(
                {
                    "error": "INVALID_CREDENTIALS",
                    "message": "Old password is incorrect.",
                }
            ),
            401,
        )


@app_views.route("/refresh", methods=["POST"], strict_slashes=False)
@jwt_required(refresh=True)
def refresh():
    current_user = get_jwt_identity()

    new_access_token = create_access_token(identity=current_user)

    return jsonify(access_token=new_access_token)


