import logging

from flask import Flask
from flask_sock import Sock

sock: Sock = Sock()


def init_app():
    app = Flask(__name__)
    sock.init_app(app)
    app.logger.setLevel(logging.DEBUG)

    app.config["SOCK_SERVER_OPTIONS"] = {"ping_interval": 25}
    app.config["PORT"] = 9001

    with app.app_context():
        import src.app

        return app
