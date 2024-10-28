from flask import jsonify, request
from datetime import datetime
from api import db
from models.appointment import Appointment
from models.user import User
from . import app_views
from flask_jwt_extended import jwt_required, get_jwt_identity


# Helper functions for error responses
def error_response(status, code, message, status_code=400):
    return (
        jsonify(
            {"status": False, "statusCode": status_code, "error": code, "msg": message}
        ),
        status_code,
    )


def success_response(message, data=None, status_code=200):
    response = {"status": True, "statusCode": status_code, "msg": message}
    if data:
        response["data"] = data
    return jsonify(response), status_code


@app_views.route("/get_appointments/<user_id>", methods=["GET", "POST"])
@jwt_required()
def get_appointments(user_id):
    user = User.query.get(user_id)
    if not user:
        return error_response("ERROR", "USER_NOT_FOUND", "User not found.", 404)

    try:
        data = request.get_json()
    except Exception:
        data = {}
    appointment_id = data.get("id")
    if appointment_id:
        appointment = Appointment.query.get(appointment_id)
        if not appointment or appointment.user_id != user_id:
            return error_response(
                "ERROR", "APPOINTMENT_NOT_FOUND", "Appointment not found.", 404
            )

        return success_response(
            "Appointment retrieved successfully.", appointment.to_dict()
        )

    query = Appointment.query.filter_by(user_id=user_id)

    start_time = data.get("start_time", None)
    end_time = data.get("end_time", None)
    status = data.get("status", None)
    doctor_id = data.get("doctor_id", None)

    if start_time:
        query = query.filter(
            Appointment.start_time >= datetime.fromisoformat(start_time)
        )
    if end_time:
        query = query.filter(Appointment.end_time <= datetime.fromisoformat(end_time))
    if doctor_id:
        query = query.filter_by(doctor_id=doctor_id)

    if status:
        current_time = datetime.now()
        if status == "Upcoming":
            query = query.filter(
                Appointment.start_time > current_time, Appointment.status == "Upcoming"
            )
        elif status == "Completed":
            query = query.filter(
                Appointment.end_time < current_time, Appointment.status == "Completed"
            )
        elif status == "Missed":
            query = query.filter(
                Appointment.end_time < current_time, Appointment.status == "Missed"
            )
        elif status == "Canceled":
            query = query.filter(Appointment.status == "Canceled")
        else:
            return error_response(
                "ERROR", "INVALID_STATUS", "Invalid status provided.", 400
            )

    appointments = query.all()
    print(appointments)
    if not appointments:
        return error_response(
            "ERROR", "NO_APPOINTMENTS_FOUND", "No appointments found.", 404
        )

    return success_response(
        "Appointments retrieved successfully.",
        [appointment.to_dict() for appointment in appointments],
    )


@app_views.route("/create_appointment/<user_id>", methods=["POST"])
@jwt_required()
def create_appointment(user_id):
    user = User.query.get(user_id)
    if not user:
        return error_response("ERROR", "USER_NOT_FOUND", "User not found.", 404)

    data = request.get_json()
    if not data:
        return error_response(
            "ERROR", "NO_INPUT_DATA_FOUND", "No input data found.", 400
        )

    start_time = data.get("start_time")
    end_time = data.get("end_time")
    description = data.get("description")
    doctor_id = data.get("doctor_id")

    if not start_time or not end_time:
        return error_response(
            "ERROR", "BAD_REQUEST", "Start and end times are required.", 400
        )

    # Create a new Appointment object
    try:
        appointment = Appointment(
            user_id=user_id,
            description=description,
            start_time=datetime.fromisoformat(start_time),
            end_time=datetime.fromisoformat(end_time),
            doctor_id=doctor_id,
            status="Upcoming",
        )
        db.session.add(appointment)
        db.session.commit()
        return success_response(
            "Appointment created successfully.", appointment.to_dict(), 201
        )
    except Exception as e:
        return error_response("ERROR", "INTERNAL_SERVER_ERROR", str(e), 500)


@app_views.route("/update_appointment/<appointment_id>", methods=["PUT", "PATCH"])
@jwt_required()
def update_appointment(appointment_id):
    appointment = Appointment.query.get(appointment_id)
    if not appointment:
        return error_response(
            "ERROR", "APPOINTMENT_NOT_FOUND", "Appointment not found.", 404
        )

    data = request.get_json()
    if not data:
        return error_response(
            "ERROR", "NO_INPUT_DATA_FOUND", "No input data provided.", 400
        )

    appointment.start_time = data.get("start_time", appointment.start_time)
    appointment.end_time = data.get("end_time", appointment.end_time)
    appointment.description = data.get("description", appointment.description)
    appointment.doctor_id = data.get("doctor_id", appointment.doctor_id)
    appointment.status = data.get("status", appointment.status)

    try:
        db.session.commit()
        return success_response(
            "Appointment updated successfully.", appointment.to_dict()
        )
    except Exception as e:
        return error_response("ERROR", "INTERNAL_SERVER_ERROR", str(e), 500)


@app_views.route("/delete_appointment/<appointment_id>", methods=["DELETE"])
@jwt_required()
def delete_appointment(appointment_id):
    appointment = Appointment.query.get(appointment_id)
    if not appointment:
        return error_response(
            "ERROR", "APPOINTMENT_NOT_FOUND", "Appointment not found.", 404
        )

    try:
        db.session.delete(appointment)
        db.session.commit()
        return success_response(f"Appointment {appointment_id} successfully deleted!")
    except Exception as e:
        return error_response("ERROR", "INTERNAL_SERVER_ERROR", str(e), 500)
