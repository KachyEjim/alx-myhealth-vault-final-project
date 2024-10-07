import os


class Config:
    DEBUG = False

    SECRET_KEY = (
        os.environ.get("SECRET_KEY") or "shsuy3y9e8hhw##4tlytyskb}{FG{}}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI")
    JWT_SECRET_KEY = SECRET_KEY
    JWT_REFRESH_TOKEN_EXPIRES = 2600
    JWT_REFRESH_TOKEN_EXPIRES = 2592000
    JWT_BLACKLIST_ENABLED = True
    JWT_BLACKLIST_TOKEN_CHECKS = ["access", "refresh"]
    REDIS_URL = os.environ.get("REDIS_URL")

    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True 
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("DEFAULT_FROM_EMAIL")
