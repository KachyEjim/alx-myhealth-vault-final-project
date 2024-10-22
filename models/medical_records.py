from datetime import datetime
from models.base_model import BaseModel
from api import db
import json


class MedicalRecords(BaseModel):
    """
    Medical_record inheriting the BaseModel with extra fields and methods
    """

    __tablename__ = "medical_records"

    user_id = db.Column(db.String(50), db.ForeignKey("users.id"), nullable=False)
    record_name = db.Column(db.String(200), nullable=False)
    health_care_provider = db.Column(db.String(100), nullable=False)
    type_of_record = db.Column(db.String(70), nullable=False)
    diagnosis = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    file_paths = db.Column(db.Text, nullable=True)  # Storing as JSON
    status = db.Column(db.String(20), nullable=True, default="draft")
    practitioner_name = db.Column(db.String(100), nullable=True)
    last_added = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_updated = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    user = db.relationship("User", backref=db.backref("medical_records", lazy=True))

    def __repr__(self):
        """String Representation showing record name and diagnosis"""
        return f"<MedicalRecord {self.record_name} ({self.diagnosis})>"

    def set_file_paths(self, paths):
        self.file_paths = json.dumps(paths)  # Store as JSON string

    def get_file_paths(self):
        return json.loads(self.file_paths) if self.file_paths else []

    def to_dict(self):
        """Converts the medical record instance into a dictionary format"""
        return {
            "id": getattr(self, "id", None),
            "user_id": getattr(self, "user_id", None),
            "record_name": getattr(self, "record_name", None),
            "health_care_provider": getattr(self, "health_care_provider", None),
            "type_of_record": getattr(self, "type_of_record", None),
            "diagnosis": getattr(self, "diagnosis", None),
            "notes": getattr(self, "notes", None),
            "file_path": getattr(self, "file_paths", None),
            "status": getattr(self, "status", None),
            "practitioner_name": getattr(self, "practitioner_name", None),
            "last_added": (
                getattr(self, "last_added", None).isoformat()
                if self.last_added
                else None
            ),
            "last_updated": (
                getattr(self, "last_updated", None).isoformat()
                if self.last_updated
                else None
            ),
            "created_at": (
                getattr(self, "created_at", None).isoformat()
                if self.created_at
                else None
            ),
            "updated_at": (
                getattr(self, "updated_at", None).isoformat()
                if self.updated_at
                else None
            ),
        }
