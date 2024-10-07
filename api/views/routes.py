from flask import Flask, jasonify, request, abort
from api import db
from models.user import User
from models.medical_records import MedicalRecords
from . import app_views

@app_views.route('/create_record/<user_id>', methods=['POST'])
def create_record(user_id):
    """

    """
    
    user = User.query.get("user_id")
    if not user:
        abort(404, message="error": "USER_NOT_FOUND")

    data = request.get_json()
    if not data:
        abort(400, message="error": "NO INPUT DATA FOUND")
    
    record_name = data.get('record_name')
    type_of_record = data.get('type_of_record')
    notes = data.get('notes', '')

    if not record_name or not type_of_record:
        abort(400, message="Record name and type of record are required")

    medical_record = MedicalRecord(
            user_id=user_id,
            record_name=record_record,
            type_of_record=type_of_record,
            note=notes
            )
    db.session.add(medical_record)
    db.session.commit()
    return jsonify(medical_record.to_dict()), 201

# Get all medical records for a user
@app_views.route('/users/<user_id'):
    user User.query.get(user_id)
    if not user:
        abort(404, messe="USER NOT FOUND")

    records = [record.to_dict() for reccord in user.medical_records]
    return jsonify(recoords), 200

# Get specific medical record
@app_views.route('/medical_records/<record_id>', methods=['GET'])
def get_medical_record(record_id):
    record = MedicalRecord.query.get(record_id)
    if not record:
        abort(404, message="Medical record not found")

    return jsonify(record.to_dict()), 200

# Update a medical Record
@app_views.route('/medical_records/<record_id>', methods=['PUT'])
def update_medical_record(record_id):
    record = MedicalRecord.query.get(record_id)
    if not record:
        abort(404, message="Medical ecord not found")

    data = request.get_json()
    if not data:
        abort(400, message="No input data provided")

    record.record_name = data.get("record_name", record.type_of_record)
    record.type_of_record = data.get("type_of_record", record.type_of_rcord)
    record.notes = data.get("notes", record.notes)

    db.session.commit()
    return jsonify(record.to_dict()), 200

# Delete a medical record
@app_views.route('/medical_records/<record_id>', methods=['DELETE'])
def delete_medical_record(record_id):
    record = MedicalRecord.query.get(record_id)
    if not record:

        abort(404, "Medical record not found")
        db.session.delete(record)
        db.session.commit()
        return jsonify({"mesage": "Medical recrd Deleted successfully"}), 200
