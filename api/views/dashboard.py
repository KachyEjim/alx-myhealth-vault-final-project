from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.medical_records import MedicalRecords
from models.appointment import Appointment
from models.user import User
from models.medication import Medication
from datetime import datetime
from . import app_views


@app_views.route("/dashboard", methods=["GET"], strict_slashes=False)
@jwt_required()
def dashboard():
    try:
        current_user_id = get_jwt_identity()

        total_medical_records = MedicalRecords.query.filter_by(
            user_id=current_user_id
        ).count()
        total_appointments = Appointment.query.filter_by(
            user_id=current_user_id
        ).count()
        total_medication_tracking = Medication.query.filter_by(
            user_id=current_user_id
        ).count()
        total_users = User.query.count()

        current_time = datetime.now()
        list_of_upcoming_appointments = Appointment.query.filter(
            Appointment.user_id == current_user_id,
            Appointment.start_time >= current_time,
        ).all()

        upcoming_appointments = [
            appointment.to_dict() for appointment in list_of_upcoming_appointments
        ]

        return (
            jsonify(
                {
                    "status": True,
                    "statusCode": 200,
                    "msg": f"Dashboard succesfully retreived",
                    "data": {
                        "totalMedicalRecords": total_medical_records,
                        "totalAppointments": total_appointments,
                        "totalMedicationTracking": total_medication_tracking,
                        "list_of_upcoming_appointments": upcoming_appointments,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        return (
            jsonify(
                {
                    "status": False,
                    "statusCode": 500,
                    "error": "INTERNAL_SERVER_ERROR",
                    "msg": f"An unexpected error occurred: {str(e)}",
                }
            ),
            500,
        )
