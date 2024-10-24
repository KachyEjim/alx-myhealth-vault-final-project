"""from flask import render_template


from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)


def log_message(message, color):
    
    Print a formatted log message to the terminal with the specified color.

    :param message: The message to print
    :param color: The color to use (from colorama.Fore)
    time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{color}[{time_now}] {message}{Style.RESET_ALL}")


def send_email(name, to, subject, body, template_name="email_template.html", **kwargs):
    Send a dynamic email using a template.

    :param to: Recipient's email address
    :param subject: Subject of the email
    :param body: Main body message of the email
    :param template_name: Template file name for the email content
    :param kwargs: Additional dynamic fields for the email template
    
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
        now = datetime.utcnow().time()  # Get current UTC time
        now = now + timedelta(hours=1)

        log_message("Checking medications for emails...", Fore.YELLOW)

        medications = Medication.query.filter(
            (Medication.time <= now) & (Medication.status == "upcoming")
        ).all()

        for medication in medications:
            user = User.query.get(medication.user_id)
            user = User.query.get(medication.user_id)
            log_message(
                f"Checking medications for emails... {user.email}     {medication.time.strftime('%I:%M %p')}       {now}",
                Fore.BLUE,
            )
            # If the medication is about to be taken
            if medication.count_left > 0:
                # Compose the email body with witty and funny elements
                email_body = (
                    f"Hey {user.full_name},\n\n"
                    f"🎉 It's time to take your {medication.name}! 🎉\n\n"
                    "You know what they say, 'A pill a day keeps the doctor away... unless you’re too busy binging your favorite show!'\n\n"
                    f"🕒 Scheduled Time: {medication.time.strftime('%I:%M %p')}\n"
                    f"💊 Count Left: {medication.count_left} (but who’s counting? Just take it! 😄)\n\n"
                    "Don’t forget, taking your meds is important! Remember, the only thing that should be on the rocks is your drink, not your health!\n\n"
                    "Cheers to good health!\n"
                    "Best,\nThe HealthCare Team 😊"
                )

                # Send the notification email
                send_email(
                    to=user.email,
                    name=user.full_name,
                    subject=f"Time to Take Your Medication: {medication.name}",
                    body=email_body,
                    footer="Stay healthy and keep smiling! Remember, laughter is the best medicine, but don't skip the actual medicine! 😂\n\nBest regards,\nThe HealthCare Team",
                    current_year=datetime.datetime.now().year,
                )

                # Update medication status to 'ongoing' and decrement count_left
                medication.status = "ongoing"
                medication.count_left -= 1

                # If count_left reaches zero, send a congratulatory email
                if medication.count_left == 0:
                    # Compose the congratulatory email body
                    congratulatory_email_body = (
                        f"Congratulations, {user.full_name}! 🎉\n\n"
                        f"You've successfully completed your course of {medication.name}!\n\n"
                        "They say good things come to those who wait, but great things come to those who take their medication!\n\n"
                        "Now, go ahead and treat yourself! Maybe a little ice cream? Just don’t forget to take your next dose... of happiness!\n\n"
                        "Cheers to your health and well-being!\n"
                        "Best,\nThe HealthCare Team 😊"
                    )

                    # Send the completion notification email
                    send_email(
                        to=user.email,
                        name=user.full_name,
                        subject=f"Congrats on Completing Your Medication: {medication.name}!",
                        body=congratulatory_email_body,
                        footer="Keep up the great work, and remember, taking care of yourself is a lifelong adventure! 🏆\n\nBest regards,\nThe HealthCare Team",
                        current_year=datetime.datetime.now().year,
                    )

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
            (Appointment.start_time <= now)
            & (Appointment.end_time >= now)
            & (Appointment.status != "Completed")
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
                    appointment.status = "Notified"
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
                        current_year=datetime.datetime.now().year,
                    )

            # If the appointment is ongoing and status is still 'Upcoming'
            if (
                appointment.start_time <= now <= appointment.end_time
                and appointment.status == "Notified"
            ):
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
                    action_url=f"https://myhealthvault-backend.onrender.com/join_appointment/{appointment.id}",
                    action_text="Join The Meeting",
                    footer="We hope to see you soon!\nIf you have any questions or need assistance during your appointment, please feel free to contact us.\n\n"
                    "Best regards,\nThe HealthCare Team",
                    current_year=datetime.datetime.now().year,
                )

            # If the appointment is finished and the status is not 'Completed'
            elif now > appointment.end_time and appointment.status == "Ongoing":
                # Update appointment status to 'Completed'
                appointment.status = "Completed"

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
                    current_year=datetime.datetime.now().year,
                )

            elif now > appointment.end_time and appointment.status == "Notified":
                # Update appointment status to 'Missed'
                appointment.status = "Missed"

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
                    action_url="https://example.com/get-started",
                    action_text="Reschedule Your Appointment",
                    body=email_body,
                    footer="We'd love to help you get back on track. Please use the link above to reschedule. If you need assistance, feel free to contact us.\n\nBest regards,\nThe HealthCare Team",
                    current_year=datetime.datetime.now().year,
                )

            db.session.commit()


# Scheduler to check appointments every minute
"""
