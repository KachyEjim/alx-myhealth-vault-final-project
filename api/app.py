from flask import Flask, abort, jsonify, make_response, request
from flask_cors import CORS
from flasgger import Swagger
from os import environ
from . import db, bcrypt, jwt_redis_blocklist
from .config import Config
from .views import app_views
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, create_refresh_token, get_jwt_identity, get_jwt
from datetime import timedelta
from flask_mail import Mail, Message

app = Flask(__name__)
app.config.from_object(Config)
bcrypt.init_app(app)
jwt = JWTManager(app)
mail = Mail(app)

db.init_app(app)
migrate = Migrate(app, db)

app.register_blueprint(app_views)
CORS(app, resources={r"/api/*": {"origins": "*"}})

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
        "message": "The token is invalid. Please log in again."
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
def test():
    return jsonify("test view")






if __name__ == "__main__":
    """ Main Function """
    with app.app_context():
        db.create_all()
    host = environ.get('HBNB_API_HOST', '0.0.0.0')
    port = environ.get('HBNB_API_PORT', '5000')
    app.run(host=host, port=port, threaded=True)
