from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from api.config import bucket


# Firebase initialization
# Allowed file extensions for security purposes
ALLOWED_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "gif",
    "pdf",
    "txt",
    "docx",
    "doc",
    "xls",
    "xlsx",
    "ppt",
    "pptx",
    "odt",
    "ods",
    "odp",
    "csv",
    "mp3",
    "wav",
    "mp4",
    "mov",
    "avi",
    "mpeg",
    "zip",
    "rar",
    "7z",
    "tar",
    "bmp",
    "svg",
    "tiff",
    "html",
    "css",
    "js",
    "json",
    "xml",
    "yaml",
    "yml",
}
IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp", "svg", "tiff"}
DOCUMENT_EXTENSIONS = {
    "pdf",
    "txt",
    "docx",
    "doc",
    "xls",
    "xlsx",
    "ppt",
    "pptx",
    "odt",
    "ods",
    "odp",
    "csv",
}
MEDIA_EXTENSIONS = {"mp3", "wav", "mp4", "mov", "avi", "mpeg"}
COMPRESSED_EXTENSIONS = {"zip", "rar", "7z", "tar"}
CODE_EXTENSIONS = {"html", "css", "js", "json", "xml", "yaml", "yml"}


def allowed_file(filename, otherExtensions1=None, otherExtensions2=None):
    if otherExtensions1:
        if "." in filename and filename.rsplit(".", 1)[1].lower() in otherExtensions1:
            return True
        if otherExtensions2:
            if (
                "." in filename
                and filename.rsplit(".", 1)[1].lower() in otherExtensions2
            ):
                return True
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# File upload route
def upload_file(file_name, file):
    # Check if the file part is in the request



    if file.filename == "":
        raise Exception("Filename is empty")

    print("Filename is not empty.")

    if not allowed_file(file.filename):
        raise Exception("File format not allowed")


    # Extract the file extension


    try:
        file.seek(0)
        blob = bucket.blob(file_name)

        # Use the upload_from_file method correctly
        blob.upload_from_file(file)

        blob.make_public()

        return blob.public_url
    except Exception as e:
        raise Exception(f"Error uploading file: {str(e)}")


def delete_file_from_firebase(file_path):
    try:
        # Reference to the file in Firebase Storage
        blob = bucket.blob(file_path)

        # Check if the file exists before deleting
        if not blob.exists():
            return (
                jsonify(
                    {
                        "error": "FILE_NOT_FOUND",
                        "status": False,
                        "statusCode": 404,
                        "msg": f"File '{file_path}' not found.",
                    }
                ),
                404,
            )

        # Delete the file
        blob.delete()
        return (
            jsonify(
                {
                    "msg": f"File '{file_path}' successfully deleted.",
                    "status": True,
                    "statusCode": 200,
                }
            ),
            200,
        )
    except Exception as e:
        return (
            jsonify(
                {
                    "error": "FILE_DELETION_ERROR",
                    "status": False,
                    "statusCode": 500,
                    "msg": f"An error occurred while deleting the file: {str(e)}",
                }
            ),
            500,
        )