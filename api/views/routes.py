from . import app_views
from flask import jsonify, request
from api import db
from models.user import User
from sqlalchemy import asc, desc
from models.appointment import Appointment
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt


@app_views.route("/create_appointment/<user_id>", methods=["POST"])
@jwt_required()
def create_appointment(user_id):
    # Check if the user exists
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "USER_NOT_FOUND", "message": "User not found."}), 404

    data = request.get_json()  # Get JSON data from the request body
    if not data:
        return (
            jsonify(
                {"error": "NO_INPUT_DATA_FOUND", "message": "No input data found."}
            ),
            400,
        )

    # Extract required fields from the JSON data
    appointment_date = data.get("appointment_date")
    appointment_time = data.get("appointment_time")
    description = data.get("description")

    # Validate required fields
    if not appointment_date:
        return (
            jsonify(
                {"error": "BAD_REQUEST", "message": "Appointment date is required."}
            ),
            400,
        )
    if not appointment_time:
        return (
            jsonify(
                {"error": "BAD_REQUEST", "message": "Appointment time is required."}
            ),
            400,
        )

    try:
        # Create a new Appointment object
        appointment = Appointment(
            userId=user_id,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            description=description,
        )

        db.session.add(appointment)  # Add appointment to the session
        db.session.commit()  # Commit the transaction

        return jsonify(appointment.to_dict()), 201  # Return the created appointment
    except Exception as e:
        return jsonify({"error": "INTERNAL_SERVER_ERROR", "message": str(e)}), 500


@app_views.route("/user_appointments/<user_id>", methods=["GET"])
@jwt_required()
def get_user_appointments(user_id):
    """
    Retrieve appointments for a specific user based on various filters and sorting parameters.
    Parameters:
    - user_id (str): The unique identifier of the user.
    - limit (int, optional): Limit the number of appointments to retrieve.
    - sort_by (str, optional): Field to sort the appointments by (default is "appointment_date").
    - sort_order (str, optional): Sorting order, either "asc" or "desc" (default is "desc").
    Returns:
    - json: A list of dictionaries representing the retrieved appointments.
    """
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "USER_NOT_FOUND", "message": "User not found."}), 404

    limit = request.args.get("limit", type=int)  # Get limit from query parameters
    sort_by = request.args.get(
        "sort_by", "appointment_date"
    )  # Get sort_by from query parameters
    sort_order = request.args.get(
        "sort_order", "desc"
    )  # Get sort_order from query parameters

    query = Appointment.query.filter_by(userId=user_id)

    # Sort the appointments by specified field and order
    if sort_order == "asc":
        query = query.order_by(asc(getattr(Appointment, sort_by, "appointment_date")))
    else:
        query = query.order_by(desc(getattr(Appointment, sort_by, "appointment_date")))

    # Limit the number of results if specified
    if limit:
        query = query.limit(limit)

    # Execute the query and fetch appointments
    appointments = query.all()

    # If no appointments are found, return a 404
    if not appointments:
        return (
            jsonify(
                {
                    "error": "NO_APPOINTMENTS_FOUND",
                    "message": "No appointments found for this user.",
                }
            ),
            404,
        )

    # Return the appointments as a list of dictionaries
    return jsonify([appointment.to_dict() for appointment in appointments]), 200


@app_views.route("/update_appointment/<appointment_id>", methods=["PUT", "PATCH"])
@jwt_required()
def update_appointment(appointment_id):
    """
    Update an appointment based on the provided appointment ID.
    Parameters:
    - appointment_id (int): The ID of the appointment to be updated.
    Returns:
    - tuple: A tuple containing JSON response and status code.
    """
    appointment = Appointment.query.get(appointment_id)

    if not appointment:
        return (
            jsonify(
                {"error": "APPOINTMENT_NOT_FOUND", "message": "Appointment not found."}
            ),
            404,
        )

    data = request.get_json()  # Get JSON data from the request body

    if not data:
        return (
            jsonify(
                {"error": "NO_INPUT_DATA_FOUND", "message": "No input data provided."}
            ),
            400,
        )

    # Update fields that are present in the request
    appointment.appointment_date = data.get(
        "appointment_date", appointment.appointment_date
    )
    appointment.appointment_time = data.get(
        "appointment_time", appointment.appointment_time
    )
    appointment.description = data.get("description", appointment.description)

    try:
        # Commit changes to the database
        db.session.commit()
        return (
            jsonify(
                {
                    "message": "Appointment updated successfully",
                    "appointment": appointment.to_dict(),
                }
            ),
            200,
        )
    except Exception as e:
        return jsonify({"error": "INTERNAL_SERVER_ERROR", "message": str(e)}), 500


@app_views.route("/delete_appointment/<appointment_id>", methods=["DELETE"])
@jwt_required()
def delete_appointment(appointment_id):
    """
    Delete an appointment by ID.
    Args:
        appointment_id (str): The ID of the appointment to be deleted.
    Returns:
        dict: A JSON response indicating the result of the deletion process.
              If successful, returns a message confirming the deletion.
              If the appointment is not found, returns an error message.
              If an internal server error occurs, returns an error message with details.
    """
    appointment = Appointment.query.get(appointment_id)

    if not appointment:
        return (
            jsonify(
                {"error": "APPOINTMENT_NOT_FOUND", "message": "Appointment not found."}
            ),
            404,
        )

    try:
        # Delete the appointment
        db.session.delete(appointment)
        db.session.commit()
        return (
            jsonify({"message": f"Appointment {appointment_id} successfully deleted!"}),
            200,
        )
    except Exception as e:
        return jsonify({"error": "INTERNAL_SERVER_ERROR", "message": str(e)}), 500
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




@app_views.route("/resend-verification", methods=["POST"])
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


@app_views.route("/reset-password/<token>", methods=["POST"])
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


@app_views.route("/forgot-password", methods=["POST"])
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


@app_views.route("/change-password", methods=["POST"])
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
from . import app_views
from flask import jsonify, request
from api import db
from models.user import User
from models.medical_records import MedicalRecords
from sqlalchemy import asc, desc
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt


@app_views.route("/create_record/<user_id>", methods=["POST"])
@jwt_required()
def create_record(user_id):
    # Check if the user exists
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "USER_NOT_FOUND", "message": "User not found."}), 404

    data = request.get_json()
    if not data:
        return (
            jsonify(
                {"error": "NO_INPUT_DATA_FOUND", "message": "No input data found."}
            ),
            400,
        )

    record_name = data.get("record_name")
    health_care_provider = data.get("health_care_provider")
    type_of_record = data.get("type_of_record")

    # Validate required fields
    if not record_name:
        return (
            jsonify({"error": "BAD_REQUEST", "message": "Record name is required."}),
            400,
        )
    if not health_care_provider:
        return (
            jsonify(
                {"error": "BAD_REQUEST", "message": "Health care provider is required."}
            ),
            400,
        )
    if not type_of_record:
        return (
            jsonify({"error": "BAD_REQUEST", "message": "Type of record is required."}),
            400,
        )

    # Optional fields
    diagnosis = data.get("diagnosis")
    notes = data.get("notes")
    file_path = data.get("file_path")
    status = data.get("status", "draft")
    practitioner_name = data.get("practitioner_name")

    try:
        medical_record = MedicalRecords(
            userId=user_id,
            record_name=record_name,
            health_care_provider=health_care_provider,
            type_of_record=type_of_record,
            diagnosis=diagnosis,
            notes=notes,
            file_path=file_path,
            status=status,
            practitioner_name=practitioner_name,
        )

        db.session.add(medical_record)
        db.session.commit()

        return jsonify(medical_record.to_dict()), 201
    except Exception as e:
        return jsonify({"error": "INTERNAL_SERVER_ERROR", "message": str(e)}), 500


@app_views.route("/user_records/<user_id>", methods=["GET"])
@jwt_required()
def get_user_medical_records(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "USER_NOT_FOUND", "message": "User not found."}), 404

    limit = request.args.get("limit", type=int)
    sort_by = request.args.get("sort_by", "last_added")
    sort_order = request.args.get("sort_order", "desc")
    record_name = request.args.get("record_name")
    type_of_record = request.args.get("type_of_record")
    diagnosis = request.args.get("diagnosis")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    created_start = request.args.get("created_start")
    created_end = request.args.get("created_end")
    updated_start = request.args.get("updated_start")
    updated_end = request.args.get("updated_end")

    query = MedicalRecords.query.filter_by(userId=user_id)

    if record_name:
        query = query.filter(MedicalRecords.record_name.ilike(f"%{record_name}%"))
    if type_of_record:
        query = query.filter_by(type_of_record=type_of_record)
    if diagnosis:
        query = query.filter(MedicalRecords.diagnosis.ilike(f"%{diagnosis}%"))

    # Filter by last_added date range
    if start_date:
        query = query.filter(MedicalRecords.last_added >= start_date)
    if end_date:
        query = query.filter(MedicalRecords.last_added <= end_date)

    # Filter by created_at date range
    if created_start:
        query = query.filter(MedicalRecords.created_at >= created_start)
    if created_end:
        query = query.filter(MedicalRecords.created_at <= created_end)

    # Filter by updated_at date range
    if updated_start:
        query = query.filter(MedicalRecords.updated_at >= updated_start)
    if updated_end:
        query = query.filter(MedicalRecords.updated_at <= updated_end)

    # Sort the records by specified field and order
    if sort_order == "asc":
        query = query.order_by(asc(getattr(MedicalRecords, sort_by, "last_added")))
    else:
        query = query.order_by(desc(getattr(MedicalRecords, sort_by, "last_added")))

    # Limit the number of results if specified
    if limit:
        query = query.limit(limit)

    # Execute the query and fetch records
    records = query.all()

    if not records:
        return (
            jsonify(
                {
                    "error": "NO_RECORDS_FOUND",
                    "message": "No medical records found for this user.",
                }
            ),
            404,
        )

    return jsonify([record.to_dict() for record in records]), 200


@app_views.route("/update_record/<record_id>", methods=["PUT", "PATCH"])
@jwt_required()
def update_medical_record(record_id):
    medical_record = MedicalRecords.query.get(record_id)

    if not medical_record:
        return (
            jsonify(
                {"error": "RECORD_NOT_FOUND", "message": "Medical record not found."}
            ),
            404,
        )

    data = request.get_json()

    if not data:
        return (
            jsonify(
                {"error": "NO_INPUT_DATA_FOUND", "message": "No input data provided."}
            ),
            400,
        )

    # Update fields that are present in the request
    medical_record.record_name = data.get("record_name", medical_record.record_name)
    medical_record.health_care_provider = data.get(
        "health_care_provider", medical_record.health_care_provider
    )
    medical_record.type_of_record = data.get(
        "type_of_record", medical_record.type_of_record
    )
    medical_record.diagnosis = data.get("diagnosis", medical_record.diagnosis)
    medical_record.notes = data.get("notes", medical_record.notes)
    medical_record.file_path = data.get("file_path", medical_record.file_path)
    medical_record.status = data.get("status", medical_record.status)
    medical_record.practitioner_name = data.get(
        "practitioner_name", medical_record.practitioner_name
    )

    try:
        db.session.commit()
        return (
            jsonify(
                {
                    "message": "Medical record updated successfully",
                    "record": medical_record.to_dict(),
                }
            ),
            200,
        )
    except Exception as e:
        return jsonify({"error": "INTERNAL_SERVER_ERROR", "message": str(e)}), 500


@app_views.route("/delete_record/<record_id>", methods=["DELETE"])
@jwt_required()
def delete_medical_record(record_id):
    medical_record = MedicalRecords.query.get(record_id)

    if not medical_record:
        return (
            jsonify(
                {"error": "RECORD_NOT_FOUND", "message": "Medical record not found."}
            ),
            404,
        )

    try:
        db.session.delete(medical_record)
        db.session.commit()
        return (
            jsonify({"message": f"Medical record {record_id} successfully deleted!"}),
            200,
        )
    except Exception as e:
        return jsonify({"error": "INTERNAL_SERVER_ERROR", "message": str(e)}), 500
from . import app_views
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from api import db
from models.user import User
from werkzeug.utils import secure_filename
from PIL import Image
import os
import tempfile


# Allowed image extensions
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}


@app_views.route("/user", methods=["GET"], strict_slashes=False)
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


@app_views.route("/update_user/<user_id>", methods=["PUT"], strict_slashes=False)
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


@app_views.route("/delete_user/<user_id>", methods=["DELETE"], strict_slashes=False)
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


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app_views.route(
    "/upload-profile-picture/<user_id>", methods=["POST"], strict_slashes=False
)
def profile_picture_upload(user_id):
    current_user_id = get_jwt_identity()

    if current_user_id != user_id:
        return (
            jsonify(
                {
                    "error": "UNAUTHORIZED",
                    "message": "You can only upload profile picture on your own account.",
                }
            ),
            403,
        )
    if request.method == "POST":
        try:
            # Get the uploaded image
            if "image" not in request.files:
                return (
                    jsonify(
                        {
                            "status": "ERROR",
                            "error": "NO_FILE_UPLOADED",
                            "message": "No file was uploaded.",
                        }
                    ),
                    400,
                )

            img = request.files["image"]

            if img.filename == "":
                return (
                    jsonify(
                        {
                            "status": "ERROR",
                            "error": "NO_FILE_UPLOADED",
                            "message": "No file was selected.",
                        }
                    ),
                    400,
                )

            if not allowed_file(img.filename):
                return (
                    jsonify(
                        {
                            "status": "ERROR",
                            "error": "INVALID_FILE_TYPE",
                            "message": "Invalid file type.",
                        }
                    ),
                    400,
                )

            # Verify the image using PIL
            try:
                image = Image.open(img)
                image.verify()
                img_format = image.format
            except Exception:
                return (
                    jsonify(
                        {
                            "status": "ERROR",
                            "error": "INVALID_IMAGE_FILE",
                            "message": "The uploaded file is not a valid image.",
                        }
                    ),
                    400,
                )

            if img.mimetype and img.content_length > 10 * 1024 * 1024:
                return (
                    jsonify(
                        {
                            "status": "ERROR",
                            "error": "FILE_TOO_LARGE",
                            "message": "File size exceeds 10MB limit.",
                        }
                    ),
                    400,
                )

            try:
                # Save the uploaded file temporarily
                with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                    for chunk in img.stream:
                        temp_file.write(chunk)
                    temp_file.flush()

                print(temp_file.name)
                print(os.path.isfile(temp_file.name))

                user = User.query.get(user_id)
                if not user:
                    raise Exception
                image_url = user.upload_file([(temp_file.name, img_format)], user_id)

                # For the sake of this example, we'll simulate a success response

                # Update the Firestore database or any other DB with the image URL
                # db.collection("users").document(user_id).set({"profile_images": image_url}, merge=True)

            except Exception as e:
                return (
                    jsonify(
                        {
                            "status": "ERROR",
                            "error": "UPLOAD_ERROR",
                            "message": f"Error uploading image or updating user: {str(e)}",
                        }
                    ),
                    500,
                )
            finally:
                # Clean up the temporary file
                if os.path.exists(temp_file.name):
                    os.remove(temp_file.name)

            return (
                jsonify(
                    {
                        "status": "SUCCESS",
                        "success": "IMAGE_UPLOADED",
                        "message": f"Image '{img.filename}' uploaded successfully.",
                        "image_url": image_url,
                    }
                ),
                200,
            )

        except Exception as e:
            return (
                jsonify(
                    {
                        "status": "ERROR",
                        "error": "INTERNAL_SERVER_ERROR",
                        "message": f"An unexpected error occurred: {str(e)}",
                    }
                ),
                500,
            )

    return (
        jsonify(
            {
                "status": "ERROR",
                "error": "INVALID_REQUEST_METHOD",
                "message": "Invalid request method.",
            }
        ),
        405,
    )
