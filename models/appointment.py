from flask_sqlalchemy import SQLAlchemy
from .base_model import BaseModel
from api import db


class Appointment(BaseModel):
    __tablename__ = "appointments"

    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    doctor_id = db.Column(db.String(36), db.ForeignKey("doctors.id"), nullable=True)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=True)
    status = db.Column(db.String(50), nullable=False, default="Upcoming")
    description = db.Column(db.String(255), nullable=True)

    doctor = db.relationship("Doctor", back_populates="appointments")
    user = db.relationship("User", back_populates="appointments")

    def __repr__(self):
        return f"<Appointment {self.start_time} - {self.end_time} with Doctor {self.doctor_id} for User {self.user_id}>"

    def to_dict(self):
        """
        Convert the Appointment object into a dictionary, using `.getattr()` to avoid attribute errors.
        """
        return {
            "id": getattr(self, "id", None),
            "start_time": (self.start_time.isoformat() if self.start_time else None),
            "end_time": (self.end_time.isoformat() if self.end_time else None),
            "doctor_id": getattr(self, "doctor_id", None),
            "user_id": getattr(self, "user_id", None),
            "status": getattr(self, "status", None),
            "description": getattr(self, "description", None),
            "created_at": (
                self.created_at.isoformat()
                if getattr(self, "created_at", None)
                else None
            ),
            "updated_at": (
                self.updated_at.isoformat()
                if getattr(self, "updated_at", None)
                else None
            ),
        }
