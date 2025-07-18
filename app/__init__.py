from flask import Flask
from flasgger import Swagger
from .routes import api_blueprint

def create_app():
    app = Flask(__name__)
    Swagger(app)
    app.register_blueprint(api_blueprint)
    return app