import bcrypt
from flask_sqlalchemy import SQLAlchemy
from .base_model import BaseModel
from api import db


class User(BaseModel):
    """
    User model inheriting from BaseModel.

    Attributes:
        id (StringField): A UUID string field representing the unique identifier.
        created_at (DateTimeField): A DateTime field representing the creation timestamp.
        updated_at (DateTimeField): A DateTime field representing the last update timestamp.
        full_name (StringField): The full name of the user.
        phone_number (StringField): The phone number of the user.
        gender (StringField): The gender of the user.
        address (StringField): The address of the user.
        email (EmailField): The email address of the user.
        password (StringField): The password of the user.
        age (IntField): The age of the user.
        date_of_birth (DateField): The date of birth of the user.
        profile_picture (URLField): URL of the user's profile picture.
        is_active (BooleanField): Boolean field indicating if the user's account is active.
        bio (StringField): Short biography or description of the user.
        last_login (DateTimeField): Timestamp of the last login.
    """

    __tablename__ = "users"

    full_name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(15), nullable=True)
    gender = db.Column(db.String(10), nullable=False, default="Other")
    address = db.Column(db.String(255), nullable=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    age = db.Column(db.Integer, nullable=True)
    profile_picture = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=False)
    is_verified = db.Column(db.Boolean, default=False)
    bio = db.Column(db.String(500), nullable=True, default="")
    last_login = db.Column(db.DateTime, nullable=True)
    role = db.Column(db.String(10), default="patient", nullable=True)

    def __repr__(self):
        return f"<User {self.full_name} ({self.email})>"

    def hash_password(self):
        """
        Hash the user's password before saving it.
        """
        if isinstance(self.password, str):
            self.password = bcrypt.hashpw(
                self.password.encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")

    def check_password(self, password):
        """
        Check if the provided password matches the hashed password.
        """
        return bcrypt.checkpw(password.encode("utf-8"), self.password.encode("utf-8"))

    def to_dict(self):
        """
        Convert the User object into a dictionary, using `.get()` to avoid attribute errors.
        """
        return {
            "id": getattr(self, "id", None),
            "full_name": getattr(self, "full_name", None),
            "phone_number": getattr(self, "phone_number", None),
            "gender": getattr(self, "gender", None),
            "address": getattr(self, "address", None),
            "email": getattr(self, "email", None),
            "age": getattr(self, "age", None),
            "profile_picture": getattr(self, "profile_picture", None),
            "is_active": getattr(self, "is_active", None),
            "bio": getattr(self, "bio", None),
            "last_login": (
                self.last_login.isoformat()
                if getattr(self, "last_login", None)
                else None
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
            "role": getattr(self, "role", None),
        }
