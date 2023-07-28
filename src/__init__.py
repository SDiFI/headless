import logging

from flask import Flask
from flask_sock import Sock

from src.config import EnvvarConfig

sock: Sock = Sock()


def init_app():
    app = Flask(__name__)
    app.logger.setLevel(logging.DEBUG)
    app.config.from_object(EnvvarConfig)

    sock.init_app(app)
    with app.app_context():
        import src.app
        import src.streaming_asr

        return app
