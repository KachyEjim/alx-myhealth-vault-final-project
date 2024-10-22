from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from api.config import bucket


# Firebase initialization
# Allowed file extensions for security purposes
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "pdf", "txt", "docx"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# File upload route
def upload_file(file_name, request, img_format=None):
    # Check if the file part is in the request

    print("File part found in the request.")

    file = request.files["file"]

    if file.filename == "":
        raise Exception("Filename is empty")

    print("Filename is not empty.")

    if not allowed_file(file.filename):
        raise Exception("File format not allowed")

    print("File format is allowed.")

    # Extract the file extension
    file_extension = file.filename.rsplit(".", 1)[1].lower()
    new_filename = f"{file_name}.{file_extension}"

    print(f"New filename: {new_filename}")

    try:
        file.seek(0)
        blob = bucket.blob(new_filename)

        # Use the upload_from_file method correctly
        blob.upload_from_file(file)
        print("File uploaded successfully.")

        blob.make_public()
        print("Blob made public.")

        return blob.public_url
    except Exception as e:
        print(f"Error uploading file: {str(e)}")
        raise
