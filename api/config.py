import os
import firebase_admin
from firebase_admin import storage, credentials
from pathlib import Path
import json


class Config:
    DEBUG = False

    SECRET_KEY = "shsuy3y9e8hhw##4tlytyskb}{FG{}}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI")

    REDIS_URL = os.environ.get("REDIS_URL")

    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("DEFAULT_FROM_EMAIL")


BASE_DIR = Path(__file__).resolve().parent.parent

cred = credentials.Certificate(json.loads(os.environ.get("GOOGLE_CLOUD_CREDENTIALS")))
firebase_admin.initialize_app(
    cred, {"storageBucket": "stockely-1.appspot.com"}
)
bucket = storage.bucket()
