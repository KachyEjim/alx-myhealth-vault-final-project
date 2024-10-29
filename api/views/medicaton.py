import uuid
from flask import request, jsonify
from datetime import datetime
from flask_jwt_extended import jwt_required, get_jwt_identity
from api import db
from models.medication import Medication
from . import app_views


# Helper functions for error responses
def error_response(status, code, message, status_code=400):
    return (
        jsonify(
            {"status": status, "statusCode": status_code, "error": code, "msg": message}
        ),
        status_code,
    )


def success_response(message, data=None, status_code=200):
    response = {"status": True, "statusCode": status_code, "msg": message}
    if data:
        response["data"] = data
    return jsonify(response), status_code


@app_views.route("/save-medications", methods=["POST"], strict_slashes=False)
@jwt_required()
def save_medications():
    try:
        data = request.get_json()

        # Validate incoming data
        user_id = get_jwt_identity()
        name = data.get("name")
        duration = data.get("duration")
        count = data.get("count")

        if not all([name, duration, count]):
            return error_response(
                "ERROR",
                "MISSING_FIELDS",
                "Each medication must have 'name', 'duration', and 'count'.",
            )

        # Validate duration format
        if not isinstance(duration, list):
            return error_response(
                "ERROR",
                "INVALID_DURATION_FORMAT",
                "'duration' must be a list of objects with 'when' and 'time' fields.",
            )

        # Check each entry in the duration list for valid time format
        for index, entry in enumerate(duration):
            when = (
                (entry.get("when")).lower()
                if (entry.get("when") and isinstance(str, entry.get("when")))
                else ""
            )
            time = entry.get("time")

            if not when or not time:
                return error_response(
                    "ERROR",
                    "MISSING_DURATION_FIELDS",
                    f"Each entry in 'duration' must contain both 'when' and 'time' fields (error at index {index}).",
                )

            # Validate time format
            try:
                datetime.strptime(time, "%H:%M")
            except ValueError:
                return error_response(
                    "ERROR",
                    "INVALID_TIME_FORMAT",
                    f"Invalid time format for 'time' in duration entry at index {index}. Expected format is 'HH:MM'.",
                )

        # Create a new Medication object
        new_medication = Medication(
            name=name,
            duration=duration,
            count=count,
            user_id=user_id,
            count_left=count,
        )

        db.session.add(new_medication)
        db.session.commit()

        return success_response(
            "Medication successfully saved!", new_medication.to_dict(), 201
        )

    except Exception as e:
        return error_response("ERROR", "INTERNAL_SERVER_ERROR", str(e), 500)


@app_views.route("/update-medications/<med_id>", methods=["PUT"], strict_slashes=False)
@jwt_required()
def update_medication(med_id):
    try:
        data = request.get_json()
        user_id = get_jwt_identity()

        # Check if medication exists
        medication = Medication.query.filter_by(id=med_id, user_id=user_id).first()
        if not medication:
            return error_response(
                "ERROR", "MEDICATION_NOT_FOUND", "Medication not found.", 404
            )

        # Validate duration format if provided
        if "duration" in data:
            duration = data["duration"]
            if not isinstance(duration, list):
                return error_response(
                    "ERROR",
                    "INVALID_DURATION_FORMAT",
                    "'duration' must be a list of objects with 'when' and 'time' fields.",
                )

            # Check each entry in the duration list for valid time format
            for index, entry in enumerate(duration):
                when = entry.get("when")
                time = entry.get("time")

                if not when or not time:
                    return error_response(
                        "ERROR",
                        "MISSING_DURATION_FIELDS",
                        f"Each entry in 'duration' must contain both 'when' and 'time' fields (error at index {index}).",
                    )

                # Validate time format
                try:
                    datetime.strptime(time, "%H:%M")
                except ValueError:
                    return error_response(
                        "ERROR",
                        "INVALID_TIME_FORMAT",
                        f"Invalid time format for 'time' in duration entry at index {index}. Expected format is 'HH:MM'.",
                    )

            # Update the duration if it passes validation
            medication.duration = duration

        # Update other fields if present in the request
        medication.name = data.get("name", medication.name)
        medication.status = data.get("status", medication.status)
        medication.count = data.get("count", medication.count)

        db.session.commit()

        return success_response("Medication updated successfully", medication.to_dict())

    except Exception as e:
        return error_response("ERROR", "INTERNAL_SERVER_ERROR", str(e), 500)


@app_views.route("/medications/<user_id>", methods=["GET"], strict_slashes=False)
@jwt_required()
def get_medications_by_user(user_id):
    try:
        # Check if the user from the JWT matches the requested user_id
        logged_in_user_id = get_jwt_identity()
        if str(logged_in_user_id) != user_id:
            return error_response(
                "ERROR",
                "UNAUTHORIZED",
                "You are not authorized to view these medications.",
                403,
            )

        # Query all medications for the specified user_id
        medications = Medication.query.filter_by(user_id=user_id).all()

        if not medications:
            return error_response(
                "ERROR",
                "NO_MEDICATIONS_FOUND",
                "No medications found for this user.",
                404,
            )

        # Convert medications to dictionary format
        medications_data = [medication.to_dict() for medication in medications]

        return success_response("Medications retrieved successfully", medications_data)

    except Exception as e:
        return error_response("ERROR", "INTERNAL_SERVER_ERROR", str(e), 500)


@app_views.route("/get-medications", methods=["POST", "GET"], strict_slashes=False)
@jwt_required()
def get_medications():
    try:
        user_id = get_jwt_identity()
        data = request.get_json() if request.is_json else {}

        # Extract filter parameters
        filters = {
            "id": data.get("id"),
            "name": data.get("name"),
            "status": data.get("status"),
            "created_at": data.get("created_at"),
            "updated_at": data.get("updated_at"),
            "count": data.get("count"),
            "count_left": data.get("count_left"),
        }

        query = Medication.query.filter_by(user_id=user_id)

        if filters["id"]:
            medication = Medication.query.filter_by(
                user_id=user_id, id=filters["id"]
            ).first()
            if not medication:
                return error_response(
                    "ERROR",
                    "NO_MEDICATION_FOUND",
                    f"No medication found with id: {filters['id']}.",
                    404,
                )
            return success_response(
                "Medication successfully retrieved", medication.to_dict()
            )

        # Apply filters to the query
        if filters["count"]:
            query = query.filter_by(count=filters["count"])
        if filters["name"]:
            query = query.filter(Medication.name.ilike(f"%{filters['name']}%"))
        if filters["count_left"]:
            query = query.filter_by(count_left=filters["count_left"])
        if filters["status"]:
            query = query.filter_by(status=filters["status"])

        # Parse date filters
        if filters["created_at"]:
            try:
                created_at_datetime = datetime.strptime(
                    filters["created_at"], "%Y-%m-%d %H:%M:%S"
                )
                query = query.filter(Medication.created_at == created_at_datetime)
            except ValueError:
                return error_response(
                    "ERROR",
                    "INVALID_DATETIME_FORMAT",
                    "Invalid format for created_at. Use YYYY-MM-DD HH:MM:SS.",
                )
        if filters["updated_at"]:
            try:
                updated_at_datetime = datetime.strptime(
                    filters["updated_at"], "%Y-%m-%d %H:%M:%S"
                )
                query = query.filter(Medication.updated_at == updated_at_datetime)
            except ValueError:
                return error_response(
                    "ERROR",
                    "INVALID_DATETIME_FORMAT",
                    "Invalid format for updated_at. Use YYYY-MM-DD HH:MM:SS.",
                )

        medications = query.all()

        if not medications:
            return error_response(
                "ERROR", "NO_MEDICATIONS_FOUND", "No medications found.", 404
            )

        return success_response(
            "Medications successfully retrieved", [med.to_dict() for med in medications]
        )

    except Exception as e:
        return error_response("ERROR", "INTERNAL_SERVER_ERROR", str(e), 500)


@app_views.route(
    "/delete-medications/<med_id>", methods=["DELETE"], strict_slashes=False
)
@jwt_required()
def delete_medication(med_id):
    try:
        user_id = get_jwt_identity()

        # Check if medication exists
        medication = Medication.query.filter_by(id=med_id, user_id=user_id).first()
        if not medication:
            return error_response(
                "ERROR", "MEDICATION_NOT_FOUND", "Medication not found.", 404
            )

        db.session.delete(medication)
        db.session.commit()

        return success_response("Medication deleted successfully!")

    except Exception as e:
        return error_response("ERROR", "INTERNAL_SERVER_ERROR", str(e), 500)
