from .base_model import BaseModel
from api import db


class Subscriber(BaseModel):
    email = db.Column(db.String(120), unique=True, nullable=False)


class Inquiry(BaseModel):
    name = db.Column(db.String(100), nullable=False, default="")
    email = db.Column(db.String(120), nullable=False, default="")
    message = db.Column(db.Text, nullable=False, default="")
