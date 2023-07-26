import json

from flask import current_app, jsonify
from twilio.twiml.voice_response import VoiceResponse

from src import sock
from src.streaming_asr import StreamingASR


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
        resp.say(
            "The headless client is not available at this time. Please try again later."
        )


@sock.route("/echo")
def route_echo(ws):
    streaming_asr: StreamingASR = StreamingASR()

    def feed_data():
        try:
            while True:
                message = ws.receive()
                if message is None:
                    current_app.logger.info("No message received...")
                    continue

                data = json.loads(message)
                if data["event"] == "connected":
                    current_app.logger.info("CONNECT: {}".format(message))
                if data["event"] == "start":
                    current_app.logger.info("START: {}".format(message))
                if data["event"] == "media":
                    yield data["media"]["payload"]
                if data["event"] == "closed":
                    current_app.logger.info("CLOSE: {}".format(message))
                    ws.close()
                    break
        except:
            current_app.logger.exception("Something went wrong while receiving data.")
            raise

    for result in streaming_asr.recognize_stream(feed_data()):
        current_app.logger.info(result)
    current_app.logger.info("CONNECTION CLOSED.")
