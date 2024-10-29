from . import app_views
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from api import db
from models.user import User
from PIL import Image

from api.config import bucket
from api.views.routes import upload_file, allowed_file, IMAGE_EXTENSIONS


@app_views.route("/all_users/", methods=["GET"], strict_slashes=False)
@jwt_required()
def all_users():
    try:
        users = User.query.all()
        user_dict = [user.to_dict() for user in users]
        return (
            jsonify(
                {
                    "status": True,
                    "statusCode": 200,
                    "data": user_dict,
                }
            ),
            200,
        )
    except Exception as e:
        return (
            jsonify(
                {
                    "error": "INTERNAL_SERVER_ERROR",
                    "status": False,
                    "statusCode": 500,
                    "msg": str(e),
                }
            ),
            500,
        )


@app_views.route("/user/", methods=["GET", "POST"], strict_slashes=False)
@app_views.route("/user/<id>", methods=["GET", "POST"], strict_slashes=False)
@jwt_required()
def get_user(id=None):

    try:
        try:
            data = request.get_json()
        except Exception:
            data = {}
        email = data.get("email")
        user_id = data.get("id")
        if id:
            user = User.query.get(id)
        elif user_id:
            user = User.query.get(user_id)
        elif email:
            user = User.query.filter_by(email=email).first()
        else:
            return (
                jsonify(
                    {
                        "error": "MISSING_CRITERIA",
                        "status": False,
                        "statusCode": 400,
                        "msg": "Please provide a valid ID or email.",
                    }
                ),
                400,
            )

        if user:
            return (
                jsonify(
                    {
                        "status": True,
                        "statusCode": 200,
                        "data": user.to_dict(),
                    }
                ),
                200,
            )
        else:
            return (
                jsonify(
                    {
                        "error": "USER_NOT_FOUND",
                        "status": False,
                        "statusCode": 404,
                        "msg": "User not found.",
                    }
                ),
                404,
            )
    except Exception as e:
        return (
            jsonify(
                {
                    "error": "INTERNAL_SERVER_ERROR",
                    "status": False,
                    "statusCode": 500,
                    "msg": str(e),
                }
            ),
            500,
        )


@app_views.route(
    "/update_user/<user_id>", methods=["PUT", "PATCH"], strict_slashes=False
)
@jwt_required()
def update_user(user_id):
    data = get_jwt()
    if (data.get("sub") != user_id) and (data.get("role") != "SuperAdmin"):
        return (
            jsonify(
                {
                    "error": "UNAUTHORIZED",
                    "status": False,
                    "statusCode": 403,
                    "msg": "You can only update your own information.",
                }
            ),
            403,
        )

    user = User.query.get(user_id)
    if not user:
        return (
            jsonify(
                {
                    "error": "USER_NOT_FOUND",
                    "status": False,
                    "statusCode": 404,
                    "msg": "User not found.",
                }
            ),
            404,
        )
    try:
        data = request.get_json()

        user.full_name = data.get("full_name", user.full_name)
        user.phone_number = data.get("phone_number", user.phone_number)
        user.gender = data.get("gender", user.gender)
        user.address = data.get("address", user.address)
        user.age = data.get("age", user.age)
        user.bio = data.get("bio", user.bio)
        user.role = data.get("role", user.role)

        db.session.commit()
        return (
            jsonify(
                {
                    "status": True,
                    "statusCode": 200,
                    "msg": "User updated successfully!",
                    "data": user.to_dict(),
                }
            ),
            200,
        )
    except Exception as e:
        return (
            jsonify(
                {
                    "error": "INTERNAL_SERVER_ERROR",
                    "status": False,
                    "statusCode": 500,
                    "msg": str(e),
                }
            ),
            500,
        )


@app_views.route("/delete_user/<user_id>", methods=["DELETE"], strict_slashes=False)
@jwt_required()
def delete_user(user_id):
    data = get_jwt()

    if data["role"] != "SuperAdmin":
        return (
            jsonify(
                {
                    "error": "UNAUTHORIZED",
                    "status": False,
                    "statusCode": 403,
                    "msg": "You are not authorized to delete this account.",
                }
            ),
            403,
        )

    user = User.query.get(user_id)

    if not user:
        return (
            jsonify(
                {
                    "error": "USER_NOT_FOUND",
                    "status": False,
                    "statusCode": 404,
                    "msg": "User not found.",
                }
            ),
            404,
        )

    try:
        db.session.delete(user)
        db.session.commit()
        jti = get_jwt()["jti"]
        expires_in = get_jwt()["exp"] - get_jwt()["iat"]
        from api.app import add_token_to_blocklist

        add_token_to_blocklist(jti, expires_in)
        return (
            jsonify(
                {
                    "status": True,
                    "statusCode": 200,
                    "msg": f"User {user_id} successfully deleted!",
                    "data": user_id,
                }
            ),
            200,
        )
    except Exception as e:
        return (
            jsonify(
                {
                    "error": "INTERNAL_SERVER_ERROR",
                    "status": False,
                    "statusCode": 500,
                    "msg": str(e),
                }
            ),
            500,
        )


@app_views.route(
    "/upload-profile-picture/<user_id>", methods=["POST"], strict_slashes=False
)
@jwt_required()
def profile_picture_upload(user_id):
    current_user_id = get_jwt_identity()

    if current_user_id != user_id:
        return (
            jsonify(
                {
                    "error": "UNAUTHORIZED",
                    "status": False,
                    "statusCode": 403,
                    "msg": "You can only upload a profile picture to your own account.",
                }
            ),
            403,
        )

    if request.method == "POST":
        try:
            if "image" not in request.files:
                return (
                    jsonify(
                        {
                            "status": False,
                            "statusCode": 400,
                            "error": "NO_FILE_UPLOADED",
                            "msg": "No file was uploaded.",
                        }
                    ),
                    400,
                )

            img = request.files["image"]  # Make sure to use "image" key

            if img.filename == "":
                return (
                    jsonify(
                        {
                            "status": False,
                            "statusCode": 400,
                            "error": "NO_FILE_UPLOADED",
                            "msg": "No file was selected.",
                        }
                    ),
                    400,
                )

            if not allowed_file(img.filename, IMAGE_EXTENSIONS):
                return (
                    jsonify(
                        {
                            "status": False,
                            "statusCode": 400,
                            "error": "INVALID_FILE_TYPE",
                            "msg": "Invalid file type.",
                        }
                    ),
                    400,
                )

            # Verify the image using PIL
            try:
                image = Image.open(img)
                image.verify()  # Verify image integrity
                img_format = image.format
            except Exception as e:
                print(f"Image verification failed: {str(e)}")  # Log the error
                return (
                    jsonify(
                        {
                            "status": False,
                            "statusCode": 400,
                            "error": "INVALID_IMAGE_FILE",
                            "msg": "The uploaded file is not a valid image.",
                        }
                    ),
                    400,
                )

            if img.mimetype and img.content_length > 10 * 1024 * 1024:
                return (
                    jsonify(
                        {
                            "status": False,
                            "statusCode": 400,
                            "error": "FILE_TOO_LARGE",
                            "msg": "File size exceeds 10MB limit.",
                        }
                    ),
                    400,
                )

            # Extract content type from the image
            content_type = img.mimetype

            try:
                user = User.query.get(user_id)
                if not user:
                    raise Exception("User not found")

                # Delete the existing profile picture if exists
                if user.profile_picture:
                    try:
                        existing_blob = bucket.blob(
                            f"profile_pictures/{user_id}.{user.profile_picture.split('.')[-1]}"
                        )
                        existing_blob.delete()
                    except Exception as e:
                        print(f"Error deleting existing profile picture: {e}")

                # Save the uploaded file temporarily
                image_url = upload_file(
                    f"profile_pictures/{user.id}.{img_format}",
                    img,  # Passing the image file
                    content_type,  # Pass the dynamically extracted content type
                )
                user.profile_picture = image_url
                db.session.add(user)
                db.session.commit()

            except Exception as e:
                return (
                    jsonify(
                        {
                            "status": False,
                            "statusCode": 500,
                            "error": "UPLOAD_ERROR",
                            "msg": f"Error uploading image or updating user: {str(e)}",
                        }
                    ),
                    500,
                )

            return (
                jsonify(
                    {
                        "status": True,
                        "statusCode": 200,
                        "msg": "Image uploaded successfully.",
                        "data": image_url,
                    }
                ),
                200,
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

    return (
        jsonify(
            {
                "status": False,
                "statusCode": 405,
                "error": "INVALID_REQUEST_METHOD",
                "msg": "Invalid request method.",
            }
        ),
        405,
    )
