import os


class Config:
    DEBUG = False

    SECRET_KEY = (
        os.environ.get("SECRET_KEY") or "shsuy3y9e8hhwa1i2#$@##4tlytyskb}{FG{}}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI")
    print(SQLALCHEMY_DATABASE_URI)
