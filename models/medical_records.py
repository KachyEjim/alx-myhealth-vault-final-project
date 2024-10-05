from datetime import datetime
from models.base_model import BaseModel
from api import db


class MedicalRecords(BaseModel):
    """
    Medical_record inheriting the BaseModel with extra fields and methods
    """

    __tablename__ = "medical_records"

    userId = db.Column(db.String(50), db.ForeignKey("users.id"), nullable=False)
    record_name = db.Column(db.String(200), nullable=False)
    health_care_provider = db.Column(db.String(100), nullable=False)
    type_of_record = db.Column(db.String(70), nullable=False)
    diagnosis = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    file_path = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), nullable=True, default="draft")
    practitioner_name = db.Column(db.String(100), nullable=True)
    last_added = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_updated = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    user = db.relationship("Users", backref=db.backref("medical_records", lazy=True))

    def __repr__(self):
        """String Representation showing record name and diagnosis"""
        return f"<MedicalRecord {self.record_name} ({self.diagnosis})>"

    def to_dict(self):
        """Converts the medical record instance into a dictionary format"""
        return {
            "id": self.get("id"),
            "user_id": self.get("user_id"),
            "record_name": self.get("record_name"),
            "health_care_provider": self.get("health_care_provider"),
            "type_of_record": self.get("type_of_record"),
            "diagnosis": self.get("diagnosis"),
            "notes": self.get("notes"),
            "file_path": self.get("file_path"),
            "status": self.get("status"),
            "practitioner_name": self.get("practitioner_name"),
            "last_added": self.get("last_added").isoformat(),
            "last_updated": self.get("last_updated").isoformat(),
            "created_at": self.get("created_at").isoformat(),
            "updated_at": self.get("updated_at").isoformat(),
        }
