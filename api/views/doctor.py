from . import app_views
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from api import db
from models.doctor import Doctor


@app_views.route("/doctor/<id>", methods=["GET", "POST"], strict_slashes=False)
@app_views.route(
    "/doctor", methods=["GET", "POST"], strict_slashes=False
)  # Optional route for POST with email or doctor_id
@jwt_required()
def get_doctor(id=None):
    try:
        data = request.get_json(silent=True) or {}
        email = data.get("email")
        doctor_id = data.get("id")

        # Determine doctor retrieval criteria
        if id:
            doctor = Doctor.query.get(id)
        elif doctor_id:
            doctor = Doctor.query.get(doctor_id)
        elif email:
            doctor = Doctor.query.filter_by(email=email).first()
        else:
            return (
                jsonify(
                    {
                        "error": "MISSING_CRITERIA",
                        "status": False,
                        "statusCode": 400,
                        "msg": "Please provide a valid ID or email.",
                    }
                ),
                400,
            )

        # Return doctor data if found
        if doctor:
            return (
                jsonify({"status": True, "statusCode": 200, "data": doctor.to_dict()}),
                200,
            )
        else:
            return (
                jsonify(
                    {
                        "error": "DOCTOR_NOT_FOUND",
                        "status": False,
                        "statusCode": 404,
                        "msg": "Doctor not found.",
                    }
                ),
                404,
            )
    except Exception as e:
        return (
            jsonify(
                {
                    "error": "INTERNAL_SERVER_ERROR",
                    "status": False,
                    "statusCode": 500,
                    "msg": str(e),
                }
            ),
            500,
        )


@app_views.route("/update_doctor/<doctor_id>", methods=["PUT"], strict_slashes=False)
@jwt_required()
def update_doctor(doctor_id):
    data = get_jwt()

    if data["role"] != "doctor":
        return (
            jsonify(
                {
                    "error": "UNAUTHORIZED",
                    "status": False,
                    "statusCode": 403,
                    "msg": "You are not authorized to access route.",
                }
            ),
            403,
        )

    if data["sub"] != doctor_id:
        return (
            jsonify(
                {
                    "error": "UNAUTHORIZED",
                    "status": False,
                    "statusCode": 403,
                    "msg": "You can only update your own information.",
                }
            ),
            403,
        )

    doctor = Doctor.query.get(doctor_id)
    if not doctor:
        return (
            jsonify(
                {
                    "error": "DOCTOR_NOT_FOUND",
                    "status": False,
                    "statusCode": 404,
                    "msg": "Doctor not found.",
                }
            ),
            404,
        )

    try:
        data = request.get_json()
        doctor.full_name = data.get("full_name", doctor.full_name)
        doctor.phone_number = data.get("phone_number", doctor.phone_number)
        doctor.specialization = data.get("specialization", doctor.specialization)
        doctor.address = data.get("address", doctor.address)
        doctor.years_of_experience = data.get(
            "years_of_experience", doctor.years_of_experience
        )
        doctor.license_number = data.get("license_number", doctor.license_number)
        doctor.bio = data.get("bio", doctor.bio)

        db.session.commit()
        return (
            jsonify(
                {
                    "status": True,
                    "statusCode": 200,
                    "msg": "Doctor updated successfully!",
                    "data": doctor.to_dict(),
                }
            ),
            200,
        )
    except Exception as e:
        return (
            jsonify(
                {
                    "error": "INTERNAL_SERVER_ERROR",
                    "status": False,
                    "statusCode": 500,
                    "msg": str(e),
                }
            ),
            500,
        )


@app_views.route("/delete_doctor/<doctor_id>", methods=["DELETE"], strict_slashes=False)
@jwt_required()
def delete_doctor(doctor_id):
    data = get_jwt()

    if data["role"] != "SuperAdmin":
        return (
            jsonify(
                {
                    "error": "UNAUTHORIZED",
                    "status": False,
                    "statusCode": 403,
                    "msg": "You are not authorized to delete this account.",
                }
            ),
            403,
        )

    doctor = Doctor.query.get(doctor_id)

    if not doctor:
        return (
            jsonify(
                {
                    "error": "DOCTOR_NOT_FOUND",
                    "status": False,
                    "statusCode": 404,
                    "msg": "Doctor not found.",
                }
            ),
            404,
        )

    try:
        db.session.delete(doctor)
        db.session.commit()
        return (
            jsonify(
                {
                    "status": True,
                    "statusCode": 200,
                    "msg": f"Doctor {doctor_id} successfully deleted!",
                    "data": doctor_id,
                }
            ),
            200,
        )
    except Exception as e:
        return (
            jsonify(
                {
                    "error": "INTERNAL_SERVER_ERROR",
                    "status": False,
                    "statusCode": 500,
                    "msg": str(e),
                }
            ),
            500,
        )


@app_views.route("/doctors", methods=["GET"], strict_slashes=False)
@jwt_required()
def get_all_doctors():
    try:
        # Query all doctors in the database
        doctors = Doctor.query.all()

        # Convert each doctor to a dictionary
        doctors_data = [doctor.to_dict() for doctor in doctors]

        return (
            jsonify(
                {
                    "status": True,
                    "statusCode": 200,
                    "data": doctors_data,
                    "msg": "Doctors retrieved successfully.",
                }
            ),
            200,
        )

    except Exception as e:
        # Handle unexpected server errors
        return (
            jsonify(
                {
                    "error": "INTERNAL_SERVER_ERROR",
                    "status": False,
                    "statusCode": 500,
                    "msg": str(e),
                }
            ),
            500,
        )


@app_views.route("/doctors/search", methods=["POST"], strict_slashes=False)
@jwt_required()
def search_doctors():
    try:
        data = request.get_json(silent=True) or {}

        limit = data.get("limit")

        query = Doctor.query

        if "full_name" in data:
            query = query.filter(Doctor.full_name.ilike(f"%{data['full_name']}%"))

        if "specialization" in data:
            query = query.filter(
                Doctor.specialization.ilike(f"%{data['specialization']}%")
            )

        if "years_of_experience" in data:
            query = query.filter(
                Doctor.years_of_experience >= data["years_of_experience"]
            )

        if "address" in data:
            query = query.filter(Doctor.address.ilike(f"%{data['address']}%"))

        if "phone_number" in data:
            query = query.filter(Doctor.phone_number == data["phone_number"])

        if "email" in data:
            query = query.filter(Doctor.email.ilike(f"%{data['email']}%"))

        if limit and isinstance(limit, int) and limit > 0:
            doctors = query.limit(limit).all()
        else:
            doctors = query.all()
        if not doctors:
            return (
                jsonify(
                    {
                        "error": "NO_DOCTOR_FOUND",
                        "status": False,
                        "statusCode": 404,
                        "msg": "No doctors found.",
                    }
                ),
                404,
            )
        doctors_data = [doctor.to_dict() for doctor in doctors]

        return (
            jsonify(
                {
                    "status": True,
                    "statusCode": 200,
                    "data": doctors_data,
                    "msg": "Doctors retrieved successfully.",
                }
            ),
            200,
        )

    except Exception as e:
        # Handle unexpected server errors
        return (
            jsonify(
                {
                    "error": "INTERNAL_SERVER_ERROR",
                    "status": False,
                    "statusCode": 500,
                    "msg": str(e),
                }
            ),
            500,
        )
