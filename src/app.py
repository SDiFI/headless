import base64
import json
from flask import current_app, jsonify
from flask_apispec import marshal_with, use_kwargs
from webargs.flaskparser import abort
from twilio.twiml.voice_response import VoiceResponse

from src import schemas
from src import sockets


# TODO(Smári): Handle error codes 404 and 500
@current_app.errorhandler(422)
@current_app.errorhandler(400)
def handle_error(err):
    """Handle request validation errors."""
    headers = err.data.get("headers", None)
    messages = err.data.get("messages", ["Invalid request."])

    json_parameters = None
    query_parameters = None
    if isinstance(messages, dict):
        json_parameters = messages.get("json", {})
        query_parameters = messages.get("query", {})

    message: str = "Invalid request."
    if not (isinstance(json_parameters, dict) and isinstance(query_parameters, dict)):
        message = "Malformed body or query parameters."
    else:
        parameter_errors = {**json_parameters, **query_parameters}
        if parameter_errors:
            message = "Validation failure for the following fields: {}".format(
                ", ".join(
                    "{}: {}".format(field, err)
                    for field, err in parameter_errors.items()
                )
            )

    if headers:
        return jsonify({"message": message}), err.code, headers
    else:
        return jsonify({"message": message}), err.code


@current_app.route("/call", methods=["POST"])
def route_call():
    try:
        resp = VoiceResponse()
        resp.say("Hello, you have reached the headless client.")
        return str(resp), 200
    except Exception as e:
        current_app.logger.exception("Something went wrong.")
        resp.say("The headless client is not available at this time. Please try again later.")
        

@sockets.route("/echo")
def route_echo(ws):
    current_app.logger.info("Halló")

    has_seen_media: bool = False
    message_count: int = 0

    while not ws.closed:
        message = ws.receive()
        if message is None:
            current_app.logger.info("No message received...")
            continue
        
        data = json.loads(message)
        
        if data['event'] == "connected":
            current_app.logger.info("Connected Message received: {}".format(message))
        if data['event'] == "start":
            current_app.logger.info("Start Message received: {}".format(message))
        if data['event'] == "media":
            if not has_seen_media:
                current_app.logger.info("Media message: {}".format(message))
                payload = data['media']['payload']
                current_app.logger.info("Payload is: {}".format(payload))
                chunk = base64.b64decode(payload)
                current_app.logger.info("That's {} bytes".format(len(chunk)))
                current_app.logger.info("Additional media messages from WebSocket are being suppressed....")
                has_seen_media = True
        if data['event'] == "closed":
            current_app.logger.info("Closed Message received: {}".format(message))
            break
        message_count += 1

        current_app.logger.info("Connection closed. Received a total of {} messages".format(message_count))


@current_app.route("/foo", methods=["POST"])
@use_kwargs(schemas.Foo)
@marshal_with(schemas.Foo, code=201, description="Success return value description.")
@marshal_with(schemas.Error, code=422, description="Malformed request body")
@marshal_with(schemas.Error, code=500, description="Internal server error")
def route_add_foo(**kwargs):
    try:
        # Some logic here...
        return "Posted some foo!", 201
    except Exception as e:
        print(f"Failed to post any foo! :(")
        abort(500)


@current_app.route("/hemi", methods=["GET"])
@marshal_with(
    schemas.Hemi(many=True),
    code=200,
    description="Success return value description.",
)
@marshal_with(schemas.Error, code=400, description="Bad request")
@marshal_with(schemas.Error, code=500, description="Internal server error")
def route_get_all_hemis():
    try:
        return [
            {
                "demi": 1,
                "semi": 2,
                "quasi": 3,
            },
            {
                "demi": 11,
                "semi": 12,
                "quasi": 13,
            },
            {
                "demi": 21,
                "semi": 22,
                "quasi": 23,
            },
        ],
        200
    except Exception as e:
        print(f"Failed to get hemis! :(")
        abort(500)
