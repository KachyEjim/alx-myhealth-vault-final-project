from . import app_views
from flask import request, jsonify, redirect
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
)
from api import db
from models.doctor import Doctor
import jwt
from datetime import datetime, timedelta
from jwt import ExpiredSignatureError, InvalidTokenError
from api.config import Config


@app_views.route("/doctor/signup", methods=["POST"], strict_slashes=False)
def doctor_signup():
    data = request.get_json()

    full_name = data.get("full_name")
    phone_number = data.get("phone_number")
    specialization = data.get("specialization")
    email = data.get("email")
    password = data.get("password")
    years_of_experience = data.get("years_of_experience")

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

    existing_doctor = Doctor.query.filter_by(email=email).first()
    if existing_doctor:
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
        new_doctor = Doctor(
            full_name=full_name,
            phone_number=phone_number,
            specialization=specialization,
            email=email,
            password=password,
            years_of_experience=years_of_experience,
        )
        new_doctor.hash_password()

        send_verification_email(
            new_doctor,
            subject="Email Verification",
            body="Welcome! Please verify your email to start using your account.",
            action_text="Verify Account",
        )

        db.session.add(new_doctor)
        db.session.commit()

        return (
            jsonify(
                {
                    "msg": "Doctor registered successfully! Verification email sent.",
                    "status": True,
                    "statusCode": 201,
                    "data": new_doctor.to_dict(),
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


@app_views.route("/doctor/login", methods=["POST"], strict_slashes=False)
def doctor_login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    doctor = Doctor.query.filter_by(email=email).first()

    if doctor and not doctor.is_verified:
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

    if doctor and doctor.check_password(password):
        access_token = create_access_token(
            identity=doctor.id, additional_claims={"role": "doctor"}
        )
        refresh_token = create_refresh_token(
            identity=doctor.id, additional_claims={"role": "doctor"}
        )

        return (
            jsonify(
                {
                    "msg": "Login successful.",
                    "status": True,
                    "statusCode": 200,
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "doctor": doctor.to_dict(),
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


def send_verification_email(doctor, subject, body, action_text):
    token = jwt.encode(
        {"user_id": doctor.id, "exp": datetime.utcnow() + timedelta(hours=24)},
        Config.SECRET_KEY,
        algorithm="HS256",
    )

    verification_link = (
        f"https://myhealthvault-backend.onrender.com/api/doctor/verify-email/{token}"
    )
    from api.app import send_email

    send_email(
        to=doctor.email,
        name=doctor.full_name,
        subject=subject,
        body=body,
        action_url=verification_link,
        action_text=action_text,
    )
    return


@app_views.route("/doctor/verify-email/<token>", methods=["GET"], strict_slashes=False)
def doctor_verify_email(token):
    try:
        payload = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
        doctor_id = payload["user_id"]

        doctor = Doctor.query.get(doctor_id)
        if not doctor:
            return (
                jsonify(
                    {
                        "status": False,
                        "statusCode": 404,
                        "error": "USER_NOT_FOUND",
                        "msg": "Doctor not found",
                    }
                ),
                404,
            )

        doctor.is_verified = True
        db.session.commit()

        return redirect("https://myhealthvault.netlify.app/auth/login", code=302)

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


@app_views.route("/doctor/join_appointment/<appointment_id>", methods=["GET"])
def doctor_join_appointment(appointment_id):
    from models.appointment import Appointment

    now = datetime.now()
    appointment = Appointment.query.get(appointment_id)

    if not appointment:
        return (
            jsonify(
                {"error": "APPOINTMENT_NOT_FOUND", "msg": "Appointment not found."}
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
            return jsonify({"error": "INTERNAL_SERVER_ERROR", "msg": str(e)}), 500

        redirect_url = "https://myhealthvault.netlify.app/appointments"
        return redirect(redirect_url)

    return (
        jsonify(
            {
                "error": "INVALID_APPOINTMENT_STATUS",
                "msg": "Appointment is either not ongoing or has a different status.",
            }
        ),
        400,
    )
