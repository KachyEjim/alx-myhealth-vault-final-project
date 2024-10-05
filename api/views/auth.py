from . import app_views
from flask import request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token
from api import db
from api.app import mail
from models.user import User
import jwt
from datetime import datetime, timedelta
from flask_mail import Message
from jwt import ExpiredSignatureError, InvalidTokenError


@app_views.route("doc/signup", methods=["POST"], strict_slashes=False)
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

        return jsonify({"message": "User registered successfully!"}), 201

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


@app_views.route("/login", methods=["POST"])
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
        app_views.config["SECRET_KEY"],
        algorithm="HS256",
    )

    verification_link = f"http://yourdomain.com/verify-email/{token}"

    msg = Message(
        subject="Email Verification",
        recipients=[user.email],
        body=f"Hi {user.username},\n\nPlease verify your email address by clicking the link below:\n\n{verification_link}\n\nIf you did not sign up for this account, please ignore this email.",
    )
    mail.send(msg)

    return (
        jsonify({"message": "Verification email sent. Please check your inbox."}),
        200,
    )


@app_views.route("/verify-email/<token>", methods=["GET"])
def verify_email(token):
    try:
        # Decode the JWT token to get the user ID
        payload = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
        user_id = payload["user_id"]

        # Retrieve the user and mark them as verified
        user = User.query.get(user_id)
        if not user:
            return (
                jsonify({"error": "USER_NOT_FOUND", "message": "User not found"}),
                404,
            )

        user.is_verified = True  # Mark the user as verified
        db.session.commit()  # Save changes to the database

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


@app_views.route("/resend-verification", methods=["POST"])
def resend_verification_email():
    data = request.get_json()

    email = data.get("email")
    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({"error": "USER_NOT_FOUND", "message": "No user found with that email."}), 404

    if user.is_verified:
        return jsonify({"message": "This account is already verified."}), 400

    send_verification_email(user)
    return jsonify({"message": "Verification email resent. Please check your inbox."}), 200
