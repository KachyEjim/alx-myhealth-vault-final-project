import bcrypt
from flask_sqlalchemy import SQLAlchemy
from .base_model import BaseModel
from api import db


class Medication(BaseModel):

    __tablename__ = "medications"

    name = db.Column(db.String(100), nullable=False)
    when = db.Column(db.String(50), nullable=False)
    time = db.Column(db.Time, nullable=False)
    count = db.Colunm(db.Integer, nullable=False)
    count_left = db.Colunm(db.Integer, nullable=True)
    status = db.Column(db.String(50), nullable=False, default="upcoming")
    user_id = db.Column(db.String(50), db.ForeignKey("users.id"), nullable=False)
    user = db.relationship("User", back_populates="medications")

    def __repr__(self):
        return f"<Medication {self.name}, {self.when}, {self.time}>"

    def to_dict(self):
        return {
            "id": getattr(self, "id", None),
            "status": getattr(self, "status", None),
            "name": getattr(self, "name", None),
            "when": getattr(self, "when", None),
            "time": (
                self.time.strftime("%H:%M") if getattr(self, "time", None) else None
            ),
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
