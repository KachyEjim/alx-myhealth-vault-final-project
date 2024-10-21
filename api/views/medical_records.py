from . import app_views
from flask import jsonify, request
from api import db
from models.user import User
from models.medical_records import MedicalRecords
from sqlalchemy import asc, desc
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt


@app_views.route("/create_record/<user_id>", methods=["POST"], strict_slashes=False)
@jwt_required()
def create_record(user_id):
    # Check if the user exists
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "USER_NOT_FOUND", "message": "User not found."}), 404
    try:
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
                jsonify(
                    {"error": "BAD_REQUEST", "message": "Record name is required."}
                ),
                400,
            )
        if not health_care_provider:
            return (
                jsonify(
                    {
                        "error": "BAD_REQUEST",
                        "message": "Health care provider is required.",
                    }
                ),
                400,
            )
        if not type_of_record:
            return (
                jsonify(
                    {"error": "BAD_REQUEST", "message": "Type of record is required."}
                ),
                400,
            )

        # Optional fields
        diagnosis = data.get("diagnosis")
        notes = data.get("notes")
        file_path = data.get("file_path")
        status = data.get("status", "draft")
        practitioner_name = data.get("practitioner_name")

        medical_record = MedicalRecords(
            user_id=user_id,
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


@app_views.route("/user_records/<user_id>", methods=["GET"], strict_slashes=False)
@jwt_required()
def get_user_medical_records(user_id):
    user = User.query.get(user_id)

    if not user:
        return jsonify({"error": "USER_NOT_FOUND", "message": "User not found."}), 404
    try:
        if request.content_type != "application/json":
            records = MedicalRecords.query.filter_by(user_id=user_id).all()
            return jsonify([record.to_dict() for record in records]), 200

        data = request.get_json()
        id = data.get("id")
        if id:
            record = MedicalRecords.query.filter_by(id=id).first()
            if not record:
                return (
                    jsonify(
                        {
                            "error": "NO_RECORDS_FOUND",
                            "message": "No medical records found for this user.",
                        }
                    ),
                    404,
                )

            return jsonify(record.to_dict()), 200

        limit = int(data.get("limit")) if data.get("limit") else None
        sort_by = data.get("sort_by", "last_added")
        sort_order = data.get("sort_order", "desc")
        record_name = data.get("record_name")
        type_of_record = data.get("type_of_record")
        diagnosis = data.get("diagnosis")
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        created_start = data.get("created_start")
        created_end = data.get("created_end")
        updated_start = data.get("updated_start")
        updated_end = data.get("updated_end")

        query = MedicalRecords.query.filter_by(user_id=user_id)

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
    except Exception as e:
        return jsonify({"error": "INTERNAL_SERVER_ERROR", "message": str(e)}), 500


@app_views.route(
    "/update_record/<record_id>", methods=["PUT", "PATCH"], strict_slashes=False
)
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
    try:
        data = request.get_json()

        if not data:
            return (
                jsonify(
                    {
                        "error": "NO_INPUT_DATA_FOUND",
                        "message": "No input data provided.",
                    }
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
    except Exception as e:
        return jsonify({"error": "INTERNAL_SERVER_ERROR", "message": str(e)}), 500


@app_views.route("/delete_record/<record_id>", methods=["DELETE"], strict_slashes=False)
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
