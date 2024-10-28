from datetime import datetime, timedelta, date
from flask import current_app as app
from api import db
from models import Medication, User
from utils import send_email, log_message
from colorama import Fore


