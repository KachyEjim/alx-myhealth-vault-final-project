from . import app_views
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from api import db
from models.user import User
from werkzeug.utils import secure_filename
from PIL import Image
import os
import tempfile


# Allowed image extensions
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}


@app_views.route("/user", methods=["GET"], strict_slashes=False)
@jwt_required()
def get_user():
    data = request.get_json()
    email = data.get("email")
    user_id = data.get("id")
    if user_id:
        user = User.query.get(user_id)
    elif email:
        user = User.query.filter_by(email=email).first()
    else:
        return (
            jsonify(
                {
                    "error": "MISSING_CRITERIA",
                    "message": "Please provide a valid ID or email.",
                }
            ),
            400,
        )

    if user:
        return jsonify({"user": user.to_dict()}), 200
    else:
        return jsonify({"error": "USER_NOT_FOUND", "message": "User not found."}), 404


@app_views.route("/update_user/<user_id>", methods=["PUT"], strict_slashes=False)
@jwt_required()
def update_user(user_id):
    current_user_id = get_jwt_identity()

    if current_user_id != user_id:
        return (
            jsonify(
                {
                    "error": "UNAUTHORIZED",
                    "message": "You can only update your own information.",
                }
            ),
            403,
        )

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "USER_NOT_FOUND", "message": "User not found."}), 404
    try:
        data = request.get_json()

        user.full_name = data.get("full_name", user.full_name)
        user.phone_number = data.get("phone_number", user.phone_number)
        user.gender = data.get("gender", user.gender)
        user.address = data.get("address", user.address)
        user.age = data.get("age", user.age)

        db.session.commit()
        return (
            jsonify({"message": "User updated successfully!", "user": user.to_dict()}),
            200,
        )
    except Exception as e:
        return jsonify({"error": "INTERNAL_SERVER_ERROR", "message": str(e)}), 500


@app_views.route("/delete_user/<user_id>", methods=["DELETE"], strict_slashes=False)
@jwt_required()
def delete_user(user_id):
    current_user_id = get_jwt_identity()

    if current_user_id != user_id:
        return (
            jsonify(
                {
                    "error": "UNAUTHORIZED",
                    "message": "You can only delete your own account.",
                }
            ),
            403,
        )

    user = User.query.get(user_id)

    if not user:
        return jsonify({"error": "USER_NOT_FOUND", "message": "User not found."}), 404

    try:
        db.session.delete(user)
        db.session.commit()
        jti = get_jwt()["jti"]
        expires_in = get_jwt()["exp"] - get_jwt()["iat"]
        from api.app import add_token_to_blocklist

        add_token_to_blocklist(jti, expires_in)
        return jsonify({"message": f"User {user_id} successfully deleted!"}), 200
    except Exception as e:
        return jsonify({"error": "INTERNAL_SERVER_ERROR", "message": str(e)}), 500


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app_views.route(
    "/upload-profile-picture/<user_id>", methods=["POST"], strict_slashes=False
)
def profile_picture_upload(user_id):
    current_user_id = get_jwt_identity()

    if current_user_id != user_id:
        return (
            jsonify(
                {
                    "error": "UNAUTHORIZED",
                    "message": "You can only upload profile picture on your own account.",
                }
            ),
            403,
        )
    if request.method == "POST":
        try:
            # Get the uploaded image
            if "image" not in request.files:
                return (
                    jsonify(
                        {
                            "status": "ERROR",
                            "error": "NO_FILE_UPLOADED",
                            "message": "No file was uploaded.",
                        }
                    ),
                    400,
                )

            img = request.files["image"]

            if img.filename == "":
                return (
                    jsonify(
                        {
                            "status": "ERROR",
                            "error": "NO_FILE_UPLOADED",
                            "message": "No file was selected.",
                        }
                    ),
                    400,
                )

            if not allowed_file(img.filename):
                return (
                    jsonify(
                        {
                            "status": "ERROR",
                            "error": "INVALID_FILE_TYPE",
                            "message": "Invalid file type.",
                        }
                    ),
                    400,
                )

            # Verify the image using PIL
            try:
                image = Image.open(img)
                image.verify()
                img_format = image.format
            except Exception:
                return (
                    jsonify(
                        {
                            "status": "ERROR",
                            "error": "INVALID_IMAGE_FILE",
                            "message": "The uploaded file is not a valid image.",
                        }
                    ),
                    400,
                )

            if img.mimetype and img.content_length > 10 * 1024 * 1024:
                return (
                    jsonify(
                        {
                            "status": "ERROR",
                            "error": "FILE_TOO_LARGE",
                            "message": "File size exceeds 10MB limit.",
                        }
                    ),
                    400,
                )

            try:
                # Save the uploaded file temporarily
                with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                    for chunk in img.stream:
                        temp_file.write(chunk)
                    temp_file.flush()

                print(temp_file.name)
                print(os.path.isfile(temp_file.name))

                user = User.query.get(user_id)
                if not user:
                    raise Exception
                image_url = user.upload_file([(temp_file.name, img_format)], user_id)

                # For the sake of this example, we'll simulate a success response

                # Update the Firestore database or any other DB with the image URL
                # db.collection("users").document(user_id).set({"profile_images": image_url}, merge=True)

            except Exception as e:
                return (
                    jsonify(
                        {
                            "status": "ERROR",
                            "error": "UPLOAD_ERROR",
                            "message": f"Error uploading image or updating user: {str(e)}",
                        }
                    ),
                    500,
                )
            finally:
                # Clean up the temporary file
                if os.path.exists(temp_file.name):
                    os.remove(temp_file.name)

            return (
                jsonify(
                    {
                        "status": "SUCCESS",
                        "success": "IMAGE_UPLOADED",
                        "message": f"Image '{img.filename}' uploaded successfully.",
                        "image_url": image_url,
                    }
                ),
                200,
            )

        except Exception as e:
            return (
                jsonify(
                    {
                        "status": "ERROR",
                        "error": "INTERNAL_SERVER_ERROR",
                        "message": f"An unexpected error occurred: {str(e)}",
                    }
                ),
                500,
            )

    return (
        jsonify(
            {
                "status": "ERROR",
                "error": "INVALID_REQUEST_METHOD",
                "message": "Invalid request method.",
            }
        ),
        405,
    )
