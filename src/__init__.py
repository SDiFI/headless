import logging

from flask import Flask
from flask_sock import Sock

from src.config import EnvvarConfig

sock: Sock = Sock()


def init_app():
    app = Flask(__name__)
    sock.init_app(app)
    app.logger.setLevel(logging.DEBUG)
    app.config.from_object(EnvvarConfig)

    with app.app_context():
        import src.app

        return app
