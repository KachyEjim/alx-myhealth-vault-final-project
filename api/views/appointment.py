from flask import jsonify, request
from datetime import datetime, timedelta
from api import db, mail
from models.appointment import Appointment
from models.user import User
from . import app_views
from flask_jwt_extended import jwt_required


@app_views.route("/get_appointments/<user_id>", methods=["POST"])
@jwt_required()
def get_appointments(user_id):
    # Check if the user exists
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "USER_NOT_FOUND", "message": "User not found."}), 404

    # Get the request data
    data = request.get_json()

    # Check if appointment_id is provided in the request
    appointment_id = data.get("id")
    if appointment_id:
        # If appointment_id is provided, return that specific appointment
        appointment = Appointment.query.get(appointment_id)
        if not appointment or appointment.user_id != user_id:
            return (
                jsonify(
                    {
                        "error": "APPOINTMENT_NOT_FOUND",
                        "message": "Appointment not found.",
                    }
                ),
                404,
            )
        return jsonify(appointment.to_dict()), 200

    # If no appointment_id is provided, search for appointments based on other criteria
    query = Appointment.query.filter_by(user_id=user_id)

    # Search by optional criteria from the request data
    start_time = data.get("start_time")
    end_time = data.get("end_time")
    status = data.get("status")
    doctor_id = data.get("doctor_id")

    if start_time:
        query = query.filter(
            Appointment.start_time >= datetime.fromisoformat(start_time)
        )
    if end_time:
        query = query.filter(Appointment.end_time <= datetime.fromisoformat(end_time))
    if doctor_id:
        query = query.filter_by(doctor_id=doctor_id)

    # Filter by status (Upcoming, Completed, Missed, Canceled)
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
            return (
                jsonify(
                    {"error": "INVALID_STATUS", "message": "Invalid status provided."}
                ),
                400,
            )

    # Get all matching appointments
    appointments = query.all()

    if not appointments:
        return (
            jsonify(
                {"error": "NO_APPOINTMENTS_FOUND", "message": "No appointments found."}
            ),
            404,
        )

    # Return the list of appointments
    return jsonify([appointment.to_dict() for appointment in appointments]), 200


@app_views.route("/create_appointment/<user_id>", methods=["POST"])
@jwt_required()
def create_appointment(user_id):
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

    start_time = data.get("start_time")
    end_time = data.get("end_time")
    description = data.get("description")
    doctor_id = data.get("doctor_id")

    if not start_time or not end_time:
        return (
            jsonify(
                {"error": "BAD_REQUEST", "message": "Start and end times are required."}
            ),
            400,
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
        return jsonify(appointment.to_dict()), 201
    except Exception as e:
        return jsonify({"error": "INTERNAL_SERVER_ERROR", "message": str(e)}), 500


@app_views.route("/update_appointment/<appointment_id>", methods=["PUT", "PATCH"])
@jwt_required()
def update_appointment(appointment_id):
    appointment = Appointment.query.get(appointment_id)
    if not appointment:
        return (
            jsonify(
                {"error": "APPOINTMENT_NOT_FOUND", "message": "Appointment not found."}
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

    appointment.start_time = data.get("start_time", appointment.start_time)
    appointment.end_time = data.get("end_time", appointment.end_time)
    appointment.description = data.get("description", appointment.description)
    appointment.doctor_id = data.get("doctor_id", appointment.doctor_id)

    try:
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
    appointment = Appointment.query.get(appointment_id)
    if not appointment:
        return (
            jsonify(
                {"error": "APPOINTMENT_NOT_FOUND", "message": "Appointment not found."}
            ),
            404,
        )

    try:
        db.session.delete(appointment)
        db.session.commit()
        return (
            jsonify({"message": f"Appointment {appointment_id} successfully deleted!"}),
            200,
        )
    except Exception as e:
        return jsonify({"error": "INTERNAL_SERVER_ERROR", "message": str(e)}), 500
