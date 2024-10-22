from . import app_views
from flask import jsonify, request
from api import db
from models.user import User
from models.medical_records import MedicalRecords
from sqlalchemy import asc, desc
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from api.views.routes import (
    upload_file,
    allowed_file,
    ALLOWED_EXTENSIONS,
    DOCUMENT_EXTENSIONS,
    COMPRESSED_EXTENSIONS,
)
from werkzeug.utils import secure_filename


@app_views.route("/create_record/<user_id>", methods=["POST"], strict_slashes=False)
@jwt_required()
def create_record(user_id):
    # Check if the user exists
    user = User.query.get(user_id)
    if not user:
        return (
            jsonify(
                {
                    "error": "USER_NOT_FOUND",
                    "status": False,
                    "statusCode": 404,
                    "msg": "User not found.",
                }
            ),
            404,
        )

    try:
        data = request.form

        # Check if the input data exists
        if not data:
            return (
                jsonify(
                    {
                        "error": "NO_INPUT_DATA_FOUND",
                        "status": False,
                        "statusCode": 400,
                        "msg": "No input data found.",
                    }
                ),
                400,
            )

        # Extract fields
        record_name = data.get("record_name")
        health_care_provider = data.get("health_care_provider")
        type_of_record = data.get("type_of_record")

        # Validate required fields
        if not record_name:
            return (
                jsonify(
                    {
                        "error": "BAD_REQUEST",
                        "status": False,
                        "statusCode": 400,
                        "msg": "Record name is required.",
                    }
                ),
                400,
            )

        if not health_care_provider:
            return (
                jsonify(
                    {
                        "error": "BAD_REQUEST",
                        "status": False,
                        "statusCode": 400,
                        "msg": "Health care provider is required.",
                    }
                ),
                400,
            )

        if not type_of_record:
            return (
                jsonify(
                    {
                        "error": "BAD_REQUEST",
                        "status": False,
                        "statusCode": 400,
                        "msg": "Type of record is required.",
                    }
                ),
                400,
            )

        # Optional fields
        diagnosis = data.get("diagnosis")
        notes = data.get("notes")
        status = data.get("status", "draft")
        practitioner_name = data.get("practitioner_name")

        # Create medical record
        medical_record = MedicalRecords(
            user_id=user_id,
            record_name=record_name,
            health_care_provider=health_care_provider,
            type_of_record=type_of_record,
            diagnosis=diagnosis,
            notes=notes,
            status=status,
            practitioner_name=practitioner_name,
        )

        print(medical_record)

        # Handle file upload (if any)
        files = request.files
        if not files:
            return (
                jsonify(
                    {
                        "error": "NO_FILES_UPLOADED",
                        "status": False,
                        "statusCode": 400,
                        "msg": "No files were uploaded.",
                    }
                ),
                400,
            )
        list_files = []
        for file in files.values():
            if file:
                if not allowed_file(
                    file.filename, DOCUMENT_EXTENSIONS, COMPRESSED_EXTENSIONS
                ):
                    return (
                        jsonify(
                            {
                                "error": "INVALID_FILE_FORMAT",
                                "status": False,
                                "statusCode": 400,
                                "msg": f"File format not allowed. Allowed types: {', '.join(DOCUMENT_EXTENSIONS)}{', '.join(COMPRESSED_EXTENSIONS)}",
                            }
                        ),
                        400,
                    )

                # Upload the file securely
                print(medical_record.id)
                new_filename = f"medicalFiles/{user_id}/{medical_record.id}/{secure_filename(file.filename)}"
                try:
                    file_path = upload_file(
                        new_filename, file
                    )  # Assuming upload_file returns the file URL/path
                    list_files.append(file_path)
                    print(file_path)
                except Exception as e:
                    return (
                        jsonify(
                            {
                                "error": "FILE_UPLOAD_ERROR",
                                "status": False,
                                "statusCode": 500,
                                "msg": f"File upload failed: {str(e)}",
                            }
                        ),
                        500,
                    )
        medical_record.set_file_paths(list_files)
        # Save record to the database
        db.session.add(medical_record)
        db.session.commit()

        # Return success response
        return (
            jsonify(
                {
                    "msg": "Medical Records successfully created",
                    "status": True,
                    "statusCode": 201,
                    "data": medical_record.to_dict(),
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
                    "msg": f"An error occurred: {str(e)}",
                }
            ),
            500,
        )


@app_views.route("/user_records/<user_id>", methods=["GET"], strict_slashes=False)
@jwt_required()
def get_user_medical_records(user_id):
    user = User.query.get(user_id)

    if not user:
        return jsonify({"error": "USER_NOT_FOUND", "message": "User not found."}), 404

    try:
        # Check if the content type is JSON and get the JSON data
        if request.content_type == "application/json":
            data = request.get_json()
        else:
            data = None  # No JSON provided

        # If JSON data is not present, return all records
        if data is None:
            records = MedicalRecords.query.filter_by(user_id=user_id).all()
            return (
                jsonify(
                    {
                        "msg": "Medical Records successfully retrieved",
                        "status": True,
                        "statusCode": 200,
                        "data": [record.to_dict() for record in records],
                    }
                ),
                200,
            )

        # Process the incoming JSON data
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

            return (
                jsonify(
                    {
                        "msg": "Medical Record successfully retrieved",
                        "status": True,
                        "statusCode": 200,
                        "data": record.to_dict(),
                    }
                ),
                200,
            )

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

        return (
            jsonify(
                {
                    "msg": "Medical Records successfully retrieved",
                    "status": True,
                    "statusCode": 200,
                    "data": [record.to_dict() for record in records],
                }
            ),
            200,
        )
    except Exception as e:
        return jsonify({"error": "INTERNAL_SERVER_ERROR", "msg": str(e)}), 500


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
                        "msg": "Medical record updated successfully",
                        "status": True,
                        "statusCode": 200,
                        "data": medical_record.to_dict(),
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
                        "message": str(e),
                    }
                ),
                500,
            )
    except Exception as e:
        return (
            jsonify(
                {"error": "INTERNAL_SERVER_ERROR", "status": False, "message": str(e)}
            ),
            500,
        )


@app_views.route("/delete_record/<record_id>", methods=["DELETE"], strict_slashes=False)
@jwt_required()
def delete_medical_record(record_id):
    medical_record = MedicalRecords.query.get(record_id)

    if not medical_record:
        return (
            jsonify({"error": "RECORD_NOT_FOUND", "msg": "Medical record not found."}),
            404,
        )

    try:
        db.session.delete(medical_record)
        db.session.commit()
        return (
            jsonify({"msg": f"Medical record {record_id} successfully deleted!"}),
            200,
        )
    except Exception as e:
        return jsonify({"error": "INTERNAL_SERVER_ERROR", "msg": str(e)}), 500
