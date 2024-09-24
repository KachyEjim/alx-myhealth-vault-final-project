from datetime import datetime
import pytz
import uuid
from api import db


class BaseModel(db.Model):
    """
    The BaseModel class for MongoEngine documents.
    Future models will inherit from this class.

    Attributes:
        id (StringField): A UUID string field representing the unique identifier.
        created_at (DateTimeField): A DateTime field representing the creation timestamp.
        updated_at (DateTimeField): A DateTime field representing the last update timestamp.
        tz (str): Time zone identifier for the instance.
    """

    __abstract__ = True

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def to_dict(self):
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def __str__(self):
        """
        Return a string representation of the model instance.
        """
        return f"[{self.__class__.__name__}] ({self.id}) {self.to_dict()}"

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.id}>"
