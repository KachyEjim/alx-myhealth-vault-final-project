import bcrypt
from .base_model import BaseModel
from api import db


class TeamMember(BaseModel):
    """
    TeamMember model inheriting from BaseModel.

    Attributes:
        id (StringField): A UUID string field representing the unique identifier.
        created_at (DateTimeField): A DateTime field representing the creation timestamp.
        updated_at (DateTimeField): A DateTime field representing the last update timestamp.
        full_name (StringField): The full name of the team member.
        email (EmailField): The email address of the team member.
        phone_number (StringField): The phone number of the team member.
        designation (StringField): The role or designation of the team member.
        address (StringField): The address of the team member.
        profile_picture (URLField): URL of the team member's profile picture.
        social_links (JSON): A JSON field for storing social media links (e.g., LinkedIn, Twitter).
    """

    __tablename__ = "team_members"

    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    phone_number = db.Column(db.String(15), nullable=True)
    designation = db.Column(db.String(100), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    profile_picture = db.Column(db.String(500), nullable=True)
    facebook_link = db.Column(db.String(225), nullable=True)
    x_link = db.Column(db.String(225), nullable=True)
    linkdin_link = db.Column(db.String(225), nullable=True)
    insta_link = db.Column(db.String(225), nullable=True)
    github_link = db.Column(db.String(225), nullable=True)

    role = db.Column(db.String(225), default="team_memeber", nullable=True)
    gender = db.Column(db.String(100), nullable=False, default="Male")
    age = db.Column(db.Integer, nullable=True)

    def __repr__(self):
        return f"<TeamMember {self.full_name} ({self.email})>"

    def to_dict(self):
        """
        Convert the TeamMember object into a dictionary.
        """
        return {
            "id": getattr(self, "id", None),
            "full_name": getattr(self, "full_name", None),
            "email": getattr(self, "email", None),
            "phone_number": getattr(self, "phone_number", None),
            "designation": getattr(self, "designation", None),
            "address": getattr(self, "address", None),
            "profile_picture": getattr(self, "profile_picture", None),
            "github_link": getattr(self, "github_link", None),
            "insta_link": getattr(self, "insta_link", None),
            "linkdin_link": getattr(self, "linkdin_link", None),
            "x_link": getattr(self, "x_link", None),
            "facebook_link": getattr(self, "facebook_link", None),
            "gender": getattr(self, "gender", None),
            "age": getattr(self, "age", None),
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
