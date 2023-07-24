import logging

from flask import Flask
from flask_sockets import Sockets
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler

PORT = 9001

sockets: Sockets = Sockets()

def init_server():
    server = Flask(__name__)
    sockets.init_app(server)
    server.logger.setLevel(logging.DEBUG)
    
    with server.app_context():
        import src.app
        return pywsgi.WSGIServer(
            ('', PORT),
            server,
            handler_class=WebSocketHandler,
            log=server.logger,
        )
