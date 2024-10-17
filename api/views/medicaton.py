import uuid
from flask import request, jsonify
from datetime import datetime
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from api import db
from models.medication import Medication
from . import app_views


@app_views.route("/save-medications", methods=["POST"], strict_slashes=False)
@jwt_required()
def save_medications():
    try:
        data = request.get_json()

        if not isinstance(data, list):
            return (
                jsonify(
                    {
                        "status": "ERROR",
                        "error": "INVALID_INPUT",
                        "message": "Medications should be provided as a list of dictionaries.",
                    }
                ),
                400,
            )

        user_id = get_jwt_identity()
        saved_medications = []
        med_id = str(uuid.uuid4())
        for med_data in data:
            # Extract the fields from each dictionary
            name = med_data.get("name")
            when = med_data.get("when")
            time = med_data.get("time")

            if not all([name, when, time]):
                return (
                    jsonify(
                        {
                            "status": "ERROR",
                            "error": "MISSING_FIELDS",
                            "message": "Each medication must have 'name', 'when', and 'time'.",
                        }
                    ),
                    400,
                )

            # Create a new Medication object
            new_medication = Medication(
                med_id=med_id,
                name=name,
                when=when,
                time=time,
                user_id=user_id,
            )

            db.session.add(new_medication)
            saved_medications.append(new_medication.to_dict())

        db.session.commit()

        return jsonify({"status": "SUCCESS", "medications": saved_medications}), 201

    except Exception as e:
        return (
            jsonify(
                {"status": "ERROR", "error": "INTERNAL_SERVER_ERROR", "message": str(e)}
            ),
            500,
        )


@app_views.route("/get-medications", methods=["POST"], strict_slashes=False)
@jwt_required()
def get_medications():
    try:
        user_id = get_jwt_identity()

        # Get the JSON data from the request
        data = request.get_json()

        # Extract parameters from the JSON data
        med_id = data.get("med_id")
        id = data.get("id")
        name = data.get("name")
        dosage = data.get("dosage")
        status = data.get("status")
        created_at = data.get("created_at")
        updated_at = data.get("updated_at")
        when = data.get("when")

        # If an ID is provided, fetch the specific medication
        if id:
            medication = Medication.query.filter_by(user_id=user_id, id=id).first()
            if medication:
                return (
                    jsonify({"status": "SUCCESS", "medication": medication.to_dict()}),
                    200,
                )
            else:
                return (
                    jsonify(
                        {
                            "status": "ERROR",
                            "error": "NO_MEDICATION_FOUND",
                            "message": f"No medication found with id: {id}.",
                        }
                    ),
                    404,
                )

        query = Medication.query.filter_by(user_id=user_id)

        if med_id:
            query = query.filter_by(med_id=med_id)
        if name:
            query = query.filter(Medication.name.ilike(f"%{name}%"))
        if dosage:
            query = query.filter_by(dosage=dosage)
        if status:
            query = query.filter_by(status=status)

        if created_at:
            try:
                created_at_datetime = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
                query = query.filter(Medication.created_at == created_at_datetime)
            except ValueError:
                return (
                    jsonify(
                        {
                            "status": "ERROR",
                            "error": "INVALID_DATETIME_FORMAT",
                            "message": "Invalid format for created_at. Use YYYY-MM-DD HH:MM:SS.",
                        }
                    ),
                    400,
                )

        if updated_at:
            try:
                updated_at_datetime = datetime.strptime(updated_at, "%Y-%m-%d %H:%M:%S")
                query = query.filter(Medication.updated_at == updated_at_datetime)
            except ValueError:
                return (
                    jsonify(
                        {
                            "status": "ERROR",
                            "error": "INVALID_DATETIME_FORMAT",
                            "message": "Invalid format for updated_at. Use YYYY-MM-DD HH:MM:SS.",
                        }
                    ),
                    400,
                )

        if when:
            try:
                when_time = datetime.strptime(
                    when, "%H:%M"
                ).time()  # Parse time as HH:MM
                query = query.filter(
                    Medication.when == when_time
                )  # Assuming Medication.when is a TIME field
            except ValueError:
                return (
                    jsonify(
                        {
                            "status": "ERROR",
                            "error": "INVALID_TIME_FORMAT",
                            "message": "Invalid format for when. Use HH:MM.",
                        }
                    ),
                    400,
                )

        medications = query.all()

        if not medications:
            return (
                jsonify(
                    {
                        "status": "ERROR",
                        "error": "NO_MEDICATIONS_FOUND",
                        "message": "No medications found.",
                    }
                ),
                404,
            )

        return (
            jsonify(
                {
                    "status": "SUCCESS",
                    "medications": [med.to_dict() for med in medications],
                }
            ),
            200,
        )

    except Exception as e:
        return (
            jsonify(
                {"status": "ERROR", "error": "INTERNAL_SERVER_ERROR", "message": str(e)}
            ),
            500,
        )


@app_views.route("/medications", methods=["GET"], strict_slashes=False)
@jwt_required()
def get_medications():
    try:
        user_id = get_jwt_identity()
        medications = Medication.query.filter_by(user_id=user_id).all()

        if not medications:
            return (
                jsonify(
                    {
                        "status": "ERROR",
                        "error": "NO_MEDICATIONS_FOUND",
                        "message": "No medications found.",
                    }
                ),
                404,
            )

        return (
            jsonify(
                {
                    "status": "SUCCESS",
                    "medications": [med.to_dict() for med in medications],
                }
            ),
            200,
        )

    except Exception as e:
        return (
            jsonify(
                {"status": "ERROR", "error": "INTERNAL_SERVER_ERROR", "message": str(e)}
            ),
            500,
        )


@app_views.route("/update-medications/<med_id>", methods=["PUT"], strict_slashes=False)
@jwt_required()
def update_medication(med_id):
    try:
        data = request.get_json()
        user_id = get_jwt_identity()

        medication = Medication.query.filter_by(med_id=med_id, user_id=user_id).first()

        if not medication:
            return (
                jsonify(
                    {
                        "status": "ERROR",
                        "error": "MEDICATION_NOT_FOUND",
                        "message": "Medication not found.",
                    }
                ),
                404,
            )

        # Update fields if they exist in the request
        medication.name = data.get("name", medication.name)
        medication.when = data.get("when", medication.when)
        medication.time = data.get("time", medication.time)
        medication.status = data.get("status", medication.status)

        db.session.commit()

        return (
            jsonify(
                {
                    "status": "SUCCESS",
                    "message": "Medication updated successfully!",
                    "medication": medication.to_dict(),
                }
            ),
            200,
        )

    except Exception as e:
        return (
            jsonify(
                {"status": "ERROR", "error": "INTERNAL_SERVER_ERROR", "message": str(e)}
            ),
            500,
        )


@app_views.route(
    "/delete-medications/<med_id>", methods=["DELETE"], strict_slashes=False
)
@jwt_required()
def delete_medication(med_id):
    try:
        user_id = get_jwt_identity()

        medication = Medication.query.filter_by(med_id=med_id, user_id=user_id).first()

        if not medication:
            return (
                jsonify(
                    {
                        "status": "ERROR",
                        "error": "MEDICATION_NOT_FOUND",
                        "message": "Medication not found.",
                    }
                ),
                404,
            )

        db.session.delete(medication)
        db.session.commit()

        return (
            jsonify(
                {"status": "SUCCESS", "message": "Medication deleted successfully!"}
            ),
            200,
        )

    except Exception as e:
        return (
            jsonify(
                {"status": "ERROR", "error": "INTERNAL_SERVER_ERROR", "message": str(e)}
            ),
            500,
        )
