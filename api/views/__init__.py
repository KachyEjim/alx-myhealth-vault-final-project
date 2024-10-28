""" Blueprint for API """

from flask import Blueprint

app_views = Blueprint("app_views", __name__, url_prefix="/api/")
from .user import *
from .auth import *
from .medical_records import *
from .appointment import *
from .dashboard import *
from .medicaton import *
from .auth_doctor import *
from .doctor import *
from .team_members import *
