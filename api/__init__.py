
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

# Create the SQLAlchemy instance once here
db = SQLAlchemy()
bcrypt = Bcrypt()
