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
    end_time = data.get("end_time")
    start_time = data.get("start_time")
    description = data.get("description")
    doctor_id = data.get("doctor_id")
    status = data.get("status")
    # Validate required fields

    if not start_time:
        return (
            jsonify({"error": "BAD_REQUEST", "message": "start date is required."}),
            400,
        )
    if not end_time:
        return (
            jsonify({"error": "BAD_REQUEST", "message": "end time is required."}),
            400,
        )

    try:
        # Create a new Appointment object
        appointment = Appointment(
            userId=user_id,
            description=description,
            start_time=start_time,
            end_time=end_time,
            status=status,
            doctor_id=doctor_id,
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
    appointment.start_time = data.get("start_time", appointment.start_time)
    appointment.end_time = data.get("end_time", appointment.end_time)
    appointment.description = data.get("description", appointment.description)
    appointment.doctor_id = data.get("doctor_id", appointment.doctor_id)
    appointment.status = data.get("status", appointment.status)
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
