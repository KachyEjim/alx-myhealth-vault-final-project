from . import app_views
from flask import request, jsonify, redirect
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
                    "status": False,
                    "statusCode": 400,
                    "msg": "Full name, email, and password are required.",
                }
            ),
            400,
        )

    password = str(password)
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return (
            jsonify(
                {
                    "error": "USER_EXISTS",
                    "status": False,
                    "statusCode": 400,
                    "msg": "Email is already in use.",
                }
            ),
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

        send_verification_email(
            new_user,
            subject="Email Verification",
            body="Welcome to Our Platform!\nPlease verify your email by clicking the link below.",
            footer="If you did not sign up for this account, please ignore this email.",
            action_text="Verify Your Account",
        )

        db.session.add(new_user)
        db.session.commit()

        return (
            jsonify(
                {
                    "msg": "User registered successfully! Verification email sent.",
                    "status": True,
                    "statusCode": 201,
                    "data": new_user.to_dict(),  # Include user data if needed
                }
            ),
            201,
        )

    except Exception as e:
        return (
            jsonify(
                {
                    "error": "INTERNAL_SERVER_ERROR",
                    "status": False,
                    "statusCode": 500,
                    "msg": f"An unexpected error occurred: {str(e)}",
                }
            ),
            500,
        )


@app_views.route("/login", methods=["POST"], strict_slashes=False)
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    user = User.query.filter_by(email=email).first()

    if user and not user.is_verified:
        return (
            jsonify(
                {
                    "error": "USER_NOT_VERIFIED",
                    "status": False,
                    "statusCode": 403,
                    "msg": "Please verify your email before logging in.",
                }
            ),
            403,
        )

    if user and user.check_password(password):
        access_token = create_access_token(
            identity=user.id, additional_claims={"role": user.role}
        )
        refresh_token = create_refresh_token(
            identity=user.id, additional_claims={"role": user.role}
        )

        return (
            jsonify(
                {
                    "msg": "Login successful.",
                    "status": True,
                    "statusCode": 200,
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "user": user.to_dict(),
                }
            ),
            200,
        )
    else:
        return (
            jsonify(
                {
                    "error": "INVALID_CREDENTIALS",
                    "status": False,
                    "statusCode": 401,
                    "msg": "Invalid email or password.",
                }
            ),
            401,
        )


def send_verification_email(user, subject, body, footer, action_text):
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
    from api.app import send_email

    send_email(
        to=user.email,
        name=user.full_name,
        subject=subject,
        body=body,
        action_url=verification_link,
        action_text=action_text,
        footer=footer,
        current_year=2024,
    )
    return


@app_views.route("/verify-email/<token>", methods=["GET"], strict_slashes=False)
def verify_email(token):
    try:
        payload = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
        user_id = payload["user_id"]

        user = User.query.get(user_id)
        if not user:
            return (
                jsonify(
                    {
                        "status": False,
                        "statusCode": 404,
                        "error": "USER_NOT_FOUND",
                        "msg": "User not found",
                    }
                ),
                404,
            )

        user.is_verified = True
        db.session.commit()

        return redirect(
            "https://incomparable-parfait-456242.netlify.app/auth/login", code=302
        )

    except ExpiredSignatureError:
        return (
            jsonify(
                {
                    "status": False,
                    "statusCode": 400,
                    "error": "TOKEN_EXPIRED",
                    "msg": "The verification token has expired",
                }
            ),
            400,
        )

    except InvalidTokenError:
        return (
            jsonify(
                {
                    "status": False,
                    "statusCode": 400,
                    "error": "INVALID_TOKEN",
                    "msg": "Invalid verification token",
                }
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
                {
                    "status": False,
                    "statusCode": 404,
                    "error": "USER_NOT_FOUND",
                    "msg": "No user found with that email.",
                }
            ),
            404,
        )

    if user.is_verified:
        return (
            jsonify(
                {
                    "status": False,
                    "statusCode": 400,
                    "msg": "This account is already verified.",
                }
            ),
            400,
        )

    send_verification_email(
        user,
        subject="Email Verification",
        body="Please verify your email address by clicking the link below:\n\n",
        footer="If you did not sign up for this account, please ignore this email.\n\n",
        action_text="Verify Your Account",
    )
    return (
        jsonify(
            {
                "status": True,
                "statusCode": 200,
                "msg": "Verification email resent. Please check your inbox.",
            }
        ),
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
                        "status": False,
                        "statusCode": 400,
                        "error": "MISSING_PASSWORD",
                        "msg": "New password is required.",
                    }
                ),
                400,
            )

        user.password = new_password
        user.hash_password()
        db.session.commit()

        return redirect(
            "https://incomparable-parfait-456242.netlify.app/auth/login", code=302
        )

    except jwt.ExpiredSignatureError:
        return (
            jsonify(
                {
                    "status": False,
                    "statusCode": 400,
                    "error": "TOKEN_EXPIRED",
                    "msg": "The password reset link has expired.",
                }
            ),
            400,
        )

    except jwt.InvalidTokenError:
        return (
            jsonify(
                {
                    "status": False,
                    "statusCode": 400,
                    "error": "INVALID_TOKEN",
                    "msg": "Invalid password reset token.",
                }
            ),
            400,
        )


@app_views.route("/forgot-password", methods=["POST"], strict_slashes=False)
def forgot_password():
    data = request.get_json()
    email = data.get("email")

    if not email:
        return (
            jsonify(
                {
                    "status": False,
                    "statusCode": 400,
                    "error": "MISSING_EMAIL",
                    "msg": "Email is required.",
                }
            ),
            400,
        )

    user = User.query.filter_by(email=email).first()

    if not user:
        return (
            jsonify(
                {
                    "status": False,
                    "statusCode": 404,
                    "error": "USER_NOT_FOUND",
                    "msg": "No user found with this email.",
                }
            ),
            404,
        )

    token = jwt.encode(
        {"user_id": user.id, "exp": datetime.utcnow() + timedelta(hours=1)},
        Config.SECRET_KEY,
        algorithm="HS256",
    )
    reset_link = (
        f"https://myhealthvault-backend.onrender.com/api/reset-password/{token}"
    )
    from api.notifications import send_email

    send_email(
        to=user.email,
        name=user.full_name,
        subject="Rest Your password",
        body="Click the link below to reset your password",
        action_url=reset_link,
        action_text="Reset Your Password",
        footer="If you did not request this action, please ignore this email.\n\n",
        current_year=2024,
    )

    return (
        jsonify(
            {"status": True, "statusCode": 200, "msg": "Password reset email sent."}
        ),
        200,
    )


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
                    "status": False,
                    "statusCode": 400,
                    "error": "MISSING_FIELDS",
                    "msg": "Old and new passwords are required.",
                }
            ),
            400,
        )

    user = User.query.get(user_id)

    if user and user.check_password(old_password):
        user.password = new_password
        user.hash_password()
        db.session.commit()
        return (
            jsonify(
                {
                    "status": True,
                    "statusCode": 200,
                    "msg": "Password changed successfully.",
                }
            ),
            200,
        )
    else:
        return (
            jsonify(
                {
                    "status": False,
                    "statusCode": 401,
                    "error": "INVALID_CREDENTIALS",
                    "msg": "Old password is incorrect.",
                }
            ),
            401,
        )


@app_views.route("/refresh", methods=["POST"], strict_slashes=False)
@jwt_required(refresh=True)
def refresh():
    current_user = get_jwt_identity()
    new_access_token = create_access_token(identity=current_user)
    return (
        jsonify(
            {
                "status": True,
                "statusCode": 200,
                "access_token": new_access_token,
                "msg": "Access token refreshed",
            }
        ),
        200,
    )


@app_views.route("/join_appointment/<appointment_id>", methods=["GET"])
def join_appointment(appointment_id):
    from flask import redirect
    from models.appointment import Appointment

    now = datetime.utcnow() + timedelta(hours=1)
    appointment = Appointment.query.get(appointment_id)
    print(f"{now}")

    if not appointment:
        return (
            jsonify(
                {"error": "APPOINTMENT_NOT_FOUND", "message": "Appointment not found."}
            ),
            404,
        )

    if (
        appointment.start_time <= now <= appointment.end_time
        and appointment.status == "Notified"
    ):
        appointment.status = "Ongoing"

        try:
            db.session.commit()
        except Exception as e:
            return jsonify({"error": "INTERNAL_SERVER_ERROR", "message": str(e)}), 500

        redirect_url = "https://incomparable-parfait-456242.netlify.app/auth/login/?redirect_to=/appointments/reschedule"
        return redirect(redirect_url)

    return (
        jsonify(
            {
                "error": "INVALID_APPOINTMENT_STATUS",
                "message": "The appointment is either not ongoing or has a different status.",
            }
        ),
        400,
    )
