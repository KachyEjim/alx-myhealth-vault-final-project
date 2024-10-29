from flask import Flask, jsonify, request, render_template
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
    get_jwt_identity,
    get_jwt,
)
from datetime import timedelta, date, datetime
from models.medication import Medication
from models.user import User
from models.doctor import Doctor
from flask_mail import Message
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor

from threading import Event
from colorama import Fore, Style, init


app = Flask(__name__)
app.config.from_object(Config)
bcrypt.init_app(app)
jwt = JWTManager(app)
mail.init_app(app)
db.init_app(app)
migrate = Migrate(app, db)


CORS(app, resources={r"/api/*": {"origins": "*"}})
app.config["JWT_SECRET_KEY"] = "shsuy3y9e8hhw##4tlytyskb}{FG{}}"

app.register_blueprint(app_views)

scheduler = BackgroundScheduler(
    executors={"default": ThreadPoolExecutor(max_workers=6)}
)
scheduler.start()
stop_event = Event()
# Initialize colorama
init(autoreset=True)


def add_token_to_blocklist(jti, expires_in):
    jwt_redis_blocklist.setex(jti, expires_in, "true")


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


def log_message(message, color):
    """
    Print a formatted log message to the terminal with the specified color.

    :param message: The message to print
    :param color: The color to use (from colorama.Fore)
    """
    time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{color}[{time_now}] {message}{Style.RESET_ALL}")


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
    log_message(f"Email sent to {to} with subject: '{subject}'", Fore.GREEN)


def check_medications():
    with app.app_context():
        now = (datetime.utcnow() + timedelta(hours=1)).time()

        # Define time slots and their names
        time_slots = {
            "morning": (8, 12),  # 8:00 AM to 11:59 AM
            "afternoon": (12, 18),  # 12:00 PM to 5:59 PM
            "night": (18, 24),  # 6:00 PM to 11:59 PM
        }

        # Determine current time slot
        current_hour = now.hour
        current_period = None
        for period, (start, end) in time_slots.items():
            if start <= current_hour < end:
                current_period = period
                break

        log_message("Checking medications for emails...", Fore.YELLOW)

        medications = Medication.query.filter(
            ((Medication.status == "upcoming") | (Medication.status == "ongoing"))
        ).all()

        for medication in medications:
            for schedule in medication.duration:
                try:
                    scheduled_time = datetime.strptime(schedule["time"], "%H:%M").time()
                except (KeyError, ValueError):
                    log_message(
                        f"Invalid time format in duration: {schedule}", Fore.RED
                    )
                    continue

                # Only proceed if the time slot has not been sent today
                if current_period and medication.last_sent_period != current_period:
                    # Check if current time matches scheduled time within 5 minutes
                    if (
                        abs(
                            (
                                datetime.combine(date.today(), scheduled_time)
                                - datetime.combine(date.today(), now)
                            ).total_seconds()
                        )
                        <= 700
                    ):
                        user = User.query.get(medication.user_id)
                        log_message(
                            f"Medication reminder for {user.email} - {medication.name} at {scheduled_time.strftime('%I:%M %p')} - current time: {now}",
                            Fore.BLUE,
                        )

                        if medication.count_left > 0:
                            email_body = (
                                f"Hey {user.full_name},\n\n"
                                f"🎉 It's time to take your {medication.name}! 🎉\n\n"
                                f"🕒 Scheduled Time: {scheduled_time.strftime('%I:%M %p')}\n"
                                f"💊 Count Left: {medication.count_left}\n\n"
                                "Cheers to good health!\nThe HealthCare Team 😊"
                            )

                            send_email(
                                to=user.email,
                                name=user.full_name,
                                subject=f"Time to Take Your Medication: {medication.name}",
                                body=email_body,
                                footer="Stay healthy and keep smiling!",
                                current_year=datetime.now().year,
                            )

                            # Update medication status and decrement count
                            medication.status = "ongoing"
                            medication.count_left -= 1
                            medication.last_sent_period = (
                                current_period  # Mark period as sent
                            )

                            if medication.count_left == 0:
                                congratulatory_email_body = (
                                    f"Congratulations, {user.full_name}! 🎉\n\n"
                                    f"You've completed your course of {medication.name}!\n\n"
                                    "Cheers to your health and well-being!\nThe HealthCare Team 😊"
                                )
                                send_email(
                                    to=user.email,
                                    name=user.full_name,
                                    subject=f"Congrats on Completing Your Medication: {medication.name}!",
                                    body=congratulatory_email_body,
                                    footer="Keep up the great work!",
                                    current_year=datetime.now().year,
                                )
                                medication.status = "completed"

                            db.session.commit()


# Function to update appointment statuses and send notifications
def check_appointments():
    from datetime import datetime
    from models.appointment import Appointment
    from models.user import User

    with app.app_context():
        now = datetime.utcnow()
        now = now + timedelta(hours=1)

        appointments = Appointment.query.filter(
            (Appointment.status != "Completed") & (Appointment.status != "Missed")
        ).all()
        log_message("Checking appointments for emails...", Fore.RED)

        for appointment in appointments:
            user = User.query.get(appointment.user_id)
            log_message(
                f"Checking appointments for ... {user.email}     "
                f"{appointment.start_time.strftime('%A, %B %d, %Y at %I:%M %p')}        "
                f"{appointment.end_time.strftime('%A, %B %d, %Y at %I:%M %p')}  {now}",
                Fore.BLUE,
            )

            # If the appointment is about to start (within 30 minutes)
            if now <= appointment.start_time <= now + timedelta(minutes=30):
                if appointment.status == "Upcoming":
                    formatted_start_time = appointment.start_time.strftime(
                        "%A, %B %d, %Y at %I:%M %p"
                    )
                    email_body = (
                        f"Dear {user.full_name},\n\n"
                        f"This is a reminder for your upcoming appointment:\n\n"
                        f"Description: {appointment.description or 'General Checkup'}\n"
                        f"Date & Time: {formatted_start_time}\n"
                        f"Doctor: {appointment.doctor.full_name if appointment.doctor else 'N/A'}\n\n"
                    )

                    send_email(
                        to=user.email,
                        name=user.full_name,
                        subject="Upcoming Appointment Reminder",
                        body=email_body,
                        footer="Looking forward to seeing you soon!\nPlease arrive 10 minutes before your scheduled time. If you have any questions or need to reschedule, feel free to contact us.\n\nBest regards,\nThe HealthCare Team",
                        current_year=datetime.now().year,
                    )
                    appointment.status = "30mins_Notified"

            # If the appointment is ongoing and status is still 'Upcoming'
            if (
                appointment.start_time <= now <= appointment.end_time
                and appointment.status == "30mins_Notified"
            ):
                formatted_start_time = appointment.start_time.strftime(
                    "%A, %B %d, %Y at %I:%M %p"
                )
                email_body = (
                    f"Dear {user.full_name},\n\n"
                    f"This is a reminder that your appointment is currently ongoing:\n\n"
                    f"Description: {appointment.description or 'General Checkup'}\n"
                    f"Started at: {formatted_start_time}\n"
                    f"Doctor: {appointment.doctor.full_name if appointment.doctor else 'N/A'}\n\n"
                    "To join the meeting, please follow the link below:\n"
                )

                send_email(
                    to=user.email,
                    name=user.full_name,
                    subject="Your Appointment is Ongoing",
                    body=email_body,
                    action_url=f"https://myhealthvault-backend.onrender.com/api/join_appointment/{appointment.id}",
                    action_text="Join The Meeting",
                    footer="We hope to see you soon!\nIf you have any questions or need assistance during your appointment, please feel free to contact us.\n\n"
                    "Best regards,\nThe HealthCare Team",
                    current_year=datetime.now().year,
                )
                appointment.status = "Notified"
            # If the appointment is finished and the status is not 'Completed'
            elif now > appointment.end_time and appointment.status == "Ongoing":
                # Update appointment status to 'Completed'

                # Format the end time
                formatted_end_time = appointment.end_time.strftime(
                    "%A, %B %d, %Y at %I:%M %p"
                )

                # Compose the email body
                email_body = (
                    f"Dear {user.full_name},\n\n"
                    f"We wanted to inform you that your appointment has ended:\n\n"
                    f"Description: {appointment.description or 'General Checkup'}\n"
                    f"Ended at: {formatted_end_time}\n"
                    f"Doctor: {appointment.doctor.full_name if appointment.doctor else 'N/A'}\n\n"
                    "Thank you for attending your appointment."
                )

                # Send the completion notification email
                send_email(
                    to=user.email,
                    name=user.full_name,
                    subject="Appointment Completed",
                    body=email_body,
                    footer="We hope your appointment went well! If you have any questions or need additional help, feel free to contact us.\n\nBest regards,\nThe HealthCare Team",
                    current_year=datetime.now().year,
                )
                appointment.status = "Completed"

            elif now > appointment.end_time and appointment.status == "Notified":
                # Update appointment status to 'Missed'

                # Format the end time
                formatted_end_time = appointment.end_time.strftime(
                    "%A, %B %d, %Y at %I:%M %p"
                )

                # Compose the email body
                email_body = (
                    f"Dear {user.full_name},\n\n"
                    f"It appears that you missed your appointment:\n\n"
                    f"Description: {appointment.description or 'General Checkup'}\n"
                    f"Scheduled Time: {formatted_end_time}\n"
                    f"Doctor: {appointment.doctor.full_name if appointment.doctor else 'N/A'}\n\n"
                    "We understand that things come up, and we'd be happy to help you reschedule at your convenience.\n\n"
                    "To reschedule your appointment, please follow the link below:\n"
                )

                # Send the missed appointment notification email
                send_email(
                    to=user.email,
                    name=user.full_name,
                    subject="Missed Appointment",
                    action_url="https://myhealthvault-backend.onrender.com/apidocs",
                    action_text="Reschedule Your Appointment",
                    body=email_body,
                    footer="We'd love to help you get back on track. Please use the link above to reschedule. If you need assistance, feel free to contact us.\n\nBest regards,\nThe HealthCare Team",
                    current_year=datetime.now().year,
                )
                appointment.status = "Missed"

            db.session.commit()


# Scheduler to check appointments every minute

swagger = Swagger(app, template_file="swagger_doc.yaml")

# Scheduler to check appointments and medications
scheduler.add_job(func=check_appointments, trigger="interval", seconds=60)
scheduler.add_job(func=check_medications, trigger="interval", seconds=20)

# Scheduler setup


if __name__ == "__main__":
    """Main Function"""
    with app.app_context():
        from datetime import datetime

        db.create_all()
    host = environ.get("HBNB_API_HOST", "0.0.0.0")
    port = environ.get("HBNB_API_PORT", "5000")
    app.run(host=host, port=port, threaded=True, debug=True)
