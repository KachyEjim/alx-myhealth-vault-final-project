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
        when = data.get("when")
        time = data.get("time")
        count = data.get("count")

        if not all([name, when, time, count]):
            return error_response(
                "ERROR",
                "MISSING_FIELDS",
                "Each medication must have 'name', 'when', 'time', and 'count'.",
            )

        # Create a new Medication object
        new_medication = Medication(
            name=name,
            when=when,
            time=time,
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


@app_views.route("/get-medications", methods=["POST", "GET"], strict_slashes=False)
@jwt_required()
def get_medications():
    try:
        user_id = get_jwt_identity()
        try:
            data = request.get_json()
        except Exception:
            data = {}
        # Extract filter parameters
        filters = {
            "id": data.get("id"),
            "time": data.get("time"),
            "name": data.get("name"),
            "status": data.get("status"),
            "created_at": data.get("created_at"),
            "updated_at": data.get("updated_at"),
            "when": data.get("when"),
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

        # Parse date and time filters
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

        if filters["time"]:
            try:
                when_time = datetime.strptime(filters["time"], "%H:%M").time()
                query = query.filter(Medication.time == when_time)
            except ValueError:
                return error_response(
                    "ERROR",
                    "INVALID_TIME_FORMAT",
                    "Invalid format for time. Use HH:MM.",
                )

        if filters["when"]:
            query = query.filter_by(when=filters["when"])

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

        # Update fields if present in the request
        medication.name = data.get("name", medication.name)
        medication.when = data.get("when", medication.when)
        medication.time = data.get("time", medication.time)
        medication.status = data.get("status", medication.status)
        medication.count = data.get("count", medication.count)

        db.session.commit()

        return success_response("Medication updated successfully", medication.to_dict())

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
