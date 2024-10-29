from flask import jsonify, request
from api import db
from models.extra import Inquiry, Subscriber
from . import app_views


@app_views.route("/subscribe", methods=["POST"], strict_slashes=False)
def subscribe():
    """Endpoint to subscribe to the newsletter"""
    try:
        data = request.get_json()
        email = data.get("email")

        if not email:
            return (
                jsonify(
                    {
                        "statusCode": 400,
                        "status": False,
                        "error": "EMAI_REQUIRED",
                        "msg": "Email is required",
                    }
                ),
                400,
            )

        # Check if email is already subscribed
        if Subscriber.query.filter_by(email=email).first():
            return (
                jsonify(
                    {
                        "statusCode": 400,
                        "status": False,
                        "error": "EMAI_EXIST",
                        "msg": "This email is already subscribed",
                    }
                ),
                400,
            )

        subscriber = Subscriber(email=email)
        db.session.add(subscriber)
        db.session.commit()

        return (
            jsonify(
                {"statusCode": 201, "status": True, "msg": "Subscribed successfully!"}
            ),
            201,
        )
    except Exception as e:
        return (
            jsonify(
                {
                    "status": False,
                    "statusCode": 500,
                    "error": "INTERNAL_SERVER_ERROR",
                    "msg": f"An unexpected error occurred: {str(e)}",
                }
            ),
            500,
        )


@app_views.route("/subscribers", methods=["GET"], strict_slashes=False)
def list_subscribers():
    """Endpoint to list all subscribers"""
    subscribers = Subscriber.query.all()
    subscriber_list = [
        {"id": s.id, "email": s.email, "subscribed_at": s.created_at}
        for s in subscribers
    ]
    return jsonify({"statusCode": 201, "status": True, "data": subscriber_list}), 200


@app_views.route("/inquiry", methods=["POST"], strict_slashes=False)
def submit_inquiry():
    """Endpoint to submit an inquiry on the contact page"""
    data = request.get_json()
    name = data.get("name")
    email = data.get("email")
    message = data.get("message")

    if not name or not email or not message:
        return (
            jsonify(
                {
                    "error": "MISSING_FIELDS",
                    "statusCode": 400,
                    "status": False,
                    "msg": "All fields (name, email, message) are required",
                }
            ),
            400,
        )

    inquiry = Inquiry(name=name, email=email, message=message)
    db.session.add(inquiry)
    db.session.commit()

    return (
        jsonify(
            {
                "statusCode": 201,
                "status": True,
                "msg": "Inquiry submitted successfully!",
            }
        ),
        201,
    )


# Fetch All Inquiries Endpoint
@app_views.route("/inquiries", methods=["GET"], strict_slashes=False)
def get_all_inquiries():
    """Endpoint to retrieve all submitted inquiries"""
    inquiries = Inquiry.query.all()
    inquiries_list = [
        {
            "id": inquiry.id,
            "name": inquiry.name,
            "email": inquiry.email,
            "message": inquiry.message,
            "submitted_at": inquiry.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }
        for inquiry in inquiries
    ]

    return (
        jsonify(
            {
                "statusCode": 200,
                "status": True,
                "msg": "Inquiries retrieved successfully",
                "data": inquiries_list,
            }
        ),
        200,
    )
