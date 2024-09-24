from flask import Flask, abort, jsonify, make_response, request
from flask_cors import CORS
from flasgger import Swagger
from os import environ
from . import db, bcrypt
from .config import Config
from .views import app_views
from flask_migrate import Migrate

app = Flask(__name__)
app.config.from_object(Config)
bcrypt.init_app(app)

db.init_app(app)
migrate = Migrate(app, db)
app.register_blueprint(app_views)

CORS(app, resources={r"/api/*": {"origins": "*"}})

Swagger(app)

@app.route('/test/', methods=['GET', 'POST'], strict_slashes=False)
def test():
    return jsonify("test view")

if __name__ == "__main__":
    """ Main Function """
    host = environ.get('HBNB_API_HOST', '0.0.0.0')
    port = environ.get('HBNB_API_PORT', '5000')
    app.run(host=host, port=port, threaded=True)
