from flask import Flask, abort, jsonify, make_response, request
from flask_cors import CORS
from flasgger import Swagger
from os import environ
from . import db, bcrypt, jwt_redis_blocklist, mail
from .config import Config
from .views import app_views
from flask_migrate import Migrate
from flask_jwt_extended import (
    JWTManager,
    jwt_required,
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    get_jwt,
)
from datetime import timedelta
from models.medication import Medication
from models.doctor import Doctor
from flask_mail import Message
from apscheduler.schedulers.background import BackgroundScheduler
from threading import Event

app = Flask(__name__)
app.config.from_object(Config)
bcrypt.init_app(app)
jwt = JWTManager(app)
mail.init_app(app)
db.init_app(app)
migrate = Migrate(app, db)


CORS(app, resources={r"/api/*": {"origins": "*"}})
app.config["JWT_SECRET_KEY"] = "shsuy3y9e8hhw##4tlytyskb}{FG{}}"

try:
    app.register_blueprint(app_views)
except Exception:
    for rule in app.url_map.iter_rules():
        print(rule.endpoint, rule.rule)
    exit()


def add_token_to_blocklist(jti, expires_in):
    jwt_redis_blocklist.setex(jti, expires_in, "true")


"""
@app.before_request
def before_request():
    for rule in app.url_map.iter_rules():
        print(f"Endpoint: {rule.endpoint}, Route: {rule.rule}")
"""


@jwt.token_in_blocklist_loader
def check_if_token_in_blocklist(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]
    token_in_redis = jwt_redis_blocklist.get(jti)
    return token_in_redis is not None


# Error handlers
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    token_type = jwt_payload["type"]
    if token_type == "access":
        return (
            jsonify(
                {
                    "error": "ACCESS_TOKEN_EXPIRED",
                    "message": "The access token has expired. Please refresh your token.",
                }
            ),
            401,
        )
    elif token_type == "refresh":
        return (
            jsonify(
                {
                    "error": "REFRESH_TOKEN_EXPIRED",
                    "message": "The refresh token has expired. Please log in again.",
                }
            ),
            401,
        )


@jwt.invalid_token_loader
def invalid_token_callback(error):
    return (
        jsonify(
            {
                "error": "INVALID_TOKEN",
                "message": f"The token is invalid. Please log in again. {error}",
            }
        ),
        401,
    )


@jwt.revoked_token_loader
def revoked_token_callback(jwt_header, jwt_payload):
    token_type = jwt_payload["type"]
    return (
        jsonify(
            {
                "error": f"{token_type.upper()}_TOKEN_REVOKED",
                "message": f"The {token_type} token has been revoked.",
            }
        ),
        401,
    )


@app.route("/logout", methods=["DELETE"])
@jwt_required()
def logout():
    jti = get_jwt()["jti"]
    expires_in = get_jwt()["exp"] - get_jwt()["iat"]
    add_token_to_blocklist(jti, expires_in)
    return jsonify({"message": "User successfully logged out"}), 200


@app.route("/test/", methods=["GET", "POST"], strict_slashes=False)
@jwt_required()
def test():
    try:
        # Extract token data
        jwt_data = get_jwt()  # Gets all claims of the token
        user_id = get_jwt_identity()  # Gets the user identity from the token

        # Print "Yes" if the token is valid
        print("Yes, token is valid")

        # Print all JWT data (including custom claims like role)
        print("JWT Data:", user_id, jwt_data)

        # Return a response
        return jsonify({"message": "Token is valid", "token_data": jwt_data}), 200

    except Exception as e:
        # Print "No" if there's an issue with the token
        print("No, token is invalid")
        print(f"Error: {str(e)}")

        # Return an error response
        return jsonify({"error": "Invalid token", "message": str(e)}), 401


# Scheduler setup
scheduler = BackgroundScheduler()
scheduler.start()
stop_event = Event()


# Function to send email
from flask import render_template


def send_email(name, to, subject, body, template_name="email_template.html", **kwargs):
    """
    Send a dynamic email using a template.

    :param to: Recipient's email address
    :param subject: Subject of the email
    :param body: Main body message of the email
    :param template_name: Template file name for the email content
    :param kwargs: Additional dynamic fields for the email template
    """
    msg = Message(subject, recipients=[to])

    # Render the HTML template with dynamic content
    msg.html = render_template(
        template_name, subject=subject, body=body, name=name, **kwargs
    )

    # Send the email
    mail.send(msg)


# Function to update appointment statuses and send notifications
def check_appointments():
    from datetime import datetime
    from models.appointment import Appointment
    from models.user import User

    with app.app_context():
        now = datetime.utcnow()
        appointments = Appointment.query.filter(
            (Appointment.start_time <= now)
            & (Appointment.end_time >= now)
            & (Appointment.status != "Completed")
        ).all()

        for appointment in appointments:
            user = User.query.get(appointment.user_id)
            # If the appointment is about to start (within 30 minutes)
            if now <= appointment.start_time <= now + timedelta(minutes=30):
                if appointment.status == "Upcoming":
                    appointment.status = "Notified"
                    send_email(
                        user.email,
                        "Upcoming Appointment Reminder",
                        f"Your appointment with {appointment.description} is scheduled to start at {appointment.start_time}.",
                    )

            # If the appointment is ongoing and status is still 'Upcoming'
            if (
                appointment.start_time <= now <= appointment.end_time
                and appointment.status == "Notified"
            ):

                send_email(
                    user.email,
                    "Your Appointment is Ongoing",
                    f"Your appointment with {appointment.description} has started.",
                )

            # If the appointment is finished and the status is not 'Completed'
            elif now > appointment.end_time and appointment.status == "Ongoing":
                appointment.status = "Completed"
                send_email(
                    user.email,
                    "Appointment Completed",
                    f"Your appointment with {appointment.description} has ended.",
                )

            # If the user missed the appointment
            elif now > appointment.end_time and appointment.status == "Notified":
                appointment.status = "Missed"
                send_email(
                    user.email,
                    "Missed Appointment",
                    f"You missed your appointment with {appointment.description}.",
                )

            db.session.commit()


# Scheduler to check appointments every minute
scheduler.add_job(func=check_appointments, trigger="interval", seconds=60)


swagger = Swagger(app, template_file="swagger_doc.yaml")


if __name__ == "__main__":
    """Main Function"""
    with app.app_context():

        db.create_all()
    host = environ.get("HBNB_API_HOST", "0.0.0.0")
    port = environ.get("HBNB_API_PORT", "5000")
    app.run(host=host, port=port, threaded=True, debug=True)
