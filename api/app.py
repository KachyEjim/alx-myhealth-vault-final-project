from flask import Flask, abort, jsonify, make_response, request
from flask_cors import CORS
from flasgger import Swagger
from os import environ
from . import db, bcrypt, jwt_redis_blocklist, mail
from .config import Config
from .views import app_views
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, create_refresh_token, get_jwt_identity, get_jwt
from datetime import timedelta
from models.doctor import Doctor

app = Flask(__name__)
app.config.from_object(Config)
bcrypt.init_app(app)
jwt = JWTManager(app)
mail.init_app(app)
db.init_app(app)
migrate = Migrate(app, db)
for rule in app.url_map.iter_rules():
    print(rule.endpoint, rule.rule)
try:
    app.register_blueprint(app_views)
except Exception:
    for rule in app.url_map.iter_rules():
        print(rule.endpoint, rule.rule)
    exit()
CORS(app, resources={r"/api/*": {"origins": "*"}})
app.config["JWT_SECRET_KEY"] = "your_secret_key" 

def add_token_to_blocklist(jti, expires_in):
    jwt_redis_blocklist.setex(jti, expires_in, 'true')


@jwt.token_in_blocklist_loader
def check_if_token_in_blocklist(jwt_header, jwt_payload):
    jti = jwt_payload['jti']
    token_in_redis = jwt_redis_blocklist.get(jti)
    return token_in_redis is not None
# Error handlers
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    token_type = jwt_payload['type']
    if token_type == 'access':
        return jsonify({
            "error": "ACCESS_TOKEN_EXPIRED",
            "message": "The access token has expired. Please refresh your token."
        }), 401
    elif token_type == 'refresh':
        return jsonify({
            "error": "REFRESH_TOKEN_EXPIRED",
            "message": "The refresh token has expired. Please log in again."
        }), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({
        "error": "INVALID_TOKEN",
        "message": f"The token is invalid. Please log in again. {error}"
    }), 401

@jwt.revoked_token_loader
def revoked_token_callback(jwt_header, jwt_payload):
    token_type = jwt_payload['type']
    return jsonify({
        "error": f"{token_type.upper()}_TOKEN_REVOKED",
        "message": f"The {token_type} token has been revoked."
    }), 401

@app.route('/logout', methods=['DELETE'])
@jwt_required()
def logout():
    jti = get_jwt()['jti']
    expires_in = get_jwt()['exp'] - get_jwt()['iat']
    add_token_to_blocklist(jti, expires_in)
    return jsonify({"message": "User successfully logged out"}), 200


@app.route('/test/', methods=['GET', 'POST'], strict_slashes=False)
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
        return jsonify({
            "message": "Token is valid",
            "token_data": jwt_data
        }), 200

    except Exception as e:
        # Print "No" if there's an issue with the token
        print("No, token is invalid")
        print(f"Error: {str(e)}")

        # Return an error response
        return jsonify({
            "error": "Invalid token",
            "message": str(e)
        }), 401

swagger = Swagger(app, template_file='swagger_doc.yaml')




if __name__ == "__main__":
    """ Main Function """
    with app.app_context():
        db.create_all()
    host = environ.get('HBNB_API_HOST', '0.0.0.0')
    port = environ.get('HBNB_API_PORT', '5000')
    app.run(host=host, port=port, threaded=True, debug=True)
