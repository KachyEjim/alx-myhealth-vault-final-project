from . import app_views
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from api import db
from models.team_members import TeamMember


# Route to create a new team member
@app_views.route("/team_member", methods=["POST"], strict_slashes=False)
def create_team_member():
    try:
        data = request.get_json()

        # Extract and validate individual fields
        full_name = data.get("full_name")
        email = data.get("email")
        phone_number = data.get("phone_number", "")
        designation = data.get("designation", "")
        address = data.get("address", "")
        profile_picture = data.get("profile_picture", "")

        github_link = data.get("github_link", "")
        insta_link = data.get("insta_link", "")
        linkdin_link = data.get("linkdin_link", "")
        x_link = data.get("x_link", "")
        facebook_link = data.get("facebook_link", "")
        gender = data.get("gender", "")
        age = data.get("age")

        # Basic validation for required fields
        if not full_name or not email:
            return (
                jsonify(
                    {
                        "statusCode": 400,
                        "status": False,
                        "error": "MISSING_DATA",
                        "msg": "Full name and email are required.",
                    }
                ),
                400,
            )

        # Create new member
        new_member = TeamMember(
            full_name=full_name,
            email=email,
            phone_number=phone_number,
            designation=designation,
            address=address,
            profile_picture=profile_picture,
            github_link=github_link,
            insta_link=insta_link,
            x_link=x_link,
            facebook_link=facebook_link,
            linkdin_link=linkdin_link,
            gender=gender,
            age=age,
        )

        db.session.add(new_member)
        db.session.commit()

        return (
            jsonify(
                {
                    "statusCode": 200,
                    "status": True,
                    "msg": "Team member created successfully",
                    "data": new_member.to_dict(),
                }
            ),
            201,
        )
    except Exception as e:
        return (
            jsonify(
                {
                    "statusCode": 500,
                    "status": False,
                    "error": "INTERNAL_SERVER_ERROR",
                    "msg": str(e),
                }
            ),
            500,
        )


# Route to update a team member
@app_views.route("/team_member/member_id>", methods=["PUT"], strict_slashes=False)
def update_team_member(member_id):
    try:
        data = request.get_json()
        team_member = TeamMember.query.get(member_id)

        if not team_member:
            return (
                jsonify(
                    {
                        "statusCode": 404,
                        "status": False,
                        "error": "TeamMember_NOT_FOUND",
                        "msg": "Team member not found.",
                    }
                ),
                404,
            )

        team_member.full_name = data.get("full_name", team_member.full_name)
        team_member.email = data.get("email", team_member.email)
        team_member.phone_number = data.get("phone_number", team_member.phone_number)
        team_member.designation = data.get("designation", team_member.designation)
        team_member.address = data.get("address", team_member.address)

        team_member.github_link = data.get("github_link", team_member.github_link)
        team_member.insta_link = data.get("insta_link", team_member.insta_link)
        team_member.linkdin_link = data.get("linkdin_link", team_member.linkdin_link)
        team_member.x_link = data.get("x_link", team_member.x_link)
        team_member.facebook_link = data.get("facebook_link", team_member.facebook_link)

        team_member.gender = data.get("gender", team_member.gender)
        team_member.age = data.get("age", team_member.age)

        # Update each field individually
        db.session.commit()
        return (
            jsonify(
                {
                    "statusCode": 200,
                    "status": True,
                    "msg": "Team member updated successfully",
                    "data": team_member.to_dict(),
                }
            ),
            200,
        )
    except Exception as e:
        return (
            jsonify(
                {
                    "statusCode": 500,
                    "status": False,
                    "error": "INTERNAL_SERVER_ERROR",
                    "msg": str(e),
                }
            ),
            500,
        )


@app_views.route("/team_member/<member_id>", methods=["DELETE"], strict_slashes=False)
@jwt_required()
def delete_team_member(member_id):
    data = get_jwt()

    if data["role"] != "SuperAdmin":
        return (
            jsonify(
                {
                    "error": "UNAUTHORIZED",
                    "status": False,
                    "statusCode": 403,
                    "msg": "You are not authorized to delete this TeamMemeber.",
                }
            ),
            403,
        )

    team_member = TeamMember.query.get(member_id)

    if not team_member:
        return (
            jsonify(
                {
                    "error": "TeamMember_NOT_FOUND",
                    "status": False,
                    "statusCode": 404,
                    "msg": "TeamMember not found.",
                }
            ),
            404,
        )

    try:
        db.session.delete(team_member)
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
                    "msg": f"Team memeber {member_id} successfully deleted!",
                    "data": member_id,
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


@app_views.route("/team_members", methods=["GET"], strict_slashes=False)
def get_all_team_members():
    try:
        members = TeamMember.query.all()
        member_list = [member.to_dict() for member in members]
        return jsonify({"statusCode": 200, "status": True, "data": member_list}), 200
    except Exception as e:
        return jsonify({"error": "INTERNAL_SERVER_ERROR", "msg": str(e)}), 500


# Route to get a specific team member by criteria (ID or email)
@app_views.route("/team_member", methods=["GET"], strict_slashes=False)
def get_team_member():
    try:
        data = request.get_json() or {}
        member_id = data.get("id")
        email = data.get("email")

        # Search by either ID or email
        if member_id:
            member = TeamMember.query.get(member_id)
        elif email:
            member = TeamMember.query.filter_by(email=email).first()
        else:
            return (
                jsonify(
                    {
                        "error": "MISSING_CRITERIA",
                        "msg": "Provide an ID or email to search.",
                    }
                ),
                400,
            )

        if member:
            return (
                jsonify({"statusCode": 200, "status": True, "data": member.to_dict()}),
                200,
            )
        else:
            return (
                jsonify(
                    {
                        "statusCode": 404,
                        "status": False,
                        "error": "TeamMember_NOT_FOUND",
                        "msg": "Team member not found.",
                    }
                ),
                404,
            )
    except Exception as e:
        return (
            jsonify(
                {
                    "statusCode": 500,
                    "status": False,
                    "error": "INTERNAL_SERVER_ERROR",
                    "msg": str(e),
                }
            ),
            500,
        )


@app_views.route(
    "/team-memeber/profile-picture/<id>", methods=["POST"], strict_slashes=False
)
def team_picture_upload(id):
    from PIL import Image

    from api.config import bucket
    from api.views.routes import upload_file, allowed_file, IMAGE_EXTENSIONS

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
            print(content_type)

            try:
                team_memeber = TeamMember.query.get(id)
                if not team_memeber:
                    raise Exception("Team_memeber not found")

                # Delete the existing profile picture if exists
                if team_memeber.profile_picture:
                    try:
                        existing_blob = bucket.blob(
                            f"profile_pictures/{id}.{team_memeber.profile_picture.split('.')[-1]}"
                        )
                        existing_blob.delete()
                    except Exception as e:
                        print(f"Error deleting existing profile picture: {e}")

                # Save the uploaded file temporarily
                image_url = upload_file(
                    f"profile_pictures/{team_memeber.id}.{img_format}",
                    img,  # Passing the image file
                    content_type,  # Pass the dynamically extracted content type
                )
                team_memeber.profile_picture = image_url
                db.session.add(team_memeber)
                db.session.commit()

            except Exception as e:
                return (
                    jsonify(
                        {
                            "status": False,
                            "statusCode": 500,
                            "error": "UPLOAD_ERROR",
                            "msg": f"Error uploading image or updating team_memeber: {str(e)}",
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
