from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flasgger import Swagger
import redis
import os
from flask_mail import Mail

REDIS_URL = os.environ.get("REDIS_URL")
mail = Mail()
db = SQLAlchemy()
bcrypt = Bcrypt()
jwt_redis_blocklist = redis.StrictRedis.from_url(REDIS_URL, decode_responses=True)
