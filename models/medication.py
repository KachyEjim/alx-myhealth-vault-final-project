import bcrypt
from flask_sqlalchemy import SQLAlchemy
from .base_model import BaseModel
from api import db


class Medication(BaseModel):
    __tablename__ = "medications"

    name = db.Column(db.String(100), nullable=False)
    duration = db.Column(db.JSON, nullable=False)
    count = db.Column(db.Integer, nullable=False)
    count_left = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(50), nullable=False, default="upcoming")
    user_id = db.Column(db.String(50), db.ForeignKey("users.id"), nullable=False)
    user = db.relationship("User", back_populates="medications")
    last_sent = db.Column(db.Date, nullable=True)

    def __repr__(self):
        return f"<Medication {self.name}>"

    def to_dict(self):
        return {
            "name": getattr(self, "name", None),
            "duration": getattr(self, "duration", []),
            "count": getattr(self, "count", None),
            "count_left": getattr(self, "count_left", None),
            "status": getattr(self, "status", None),
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
