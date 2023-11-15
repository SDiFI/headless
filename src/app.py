import json
import subprocess

import requests
from flask import current_app, jsonify

from src import sock
from src.streaming_asr import StreamingASR
from src import tts


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


@sock.route("/convo")
def route_convo(ws):
    language_code = "is-IS"
    conversation_url = current_app.config["MASDIF_SERVER_URL"] + "/conversations"
    r = requests.post(conversation_url)
    conversation_id = r.json()["conversation_id"]

    # TODO(rkjaran): There's no TTS generated for the MOTD... We need to prompt the user
    #   somehow

    # TODO(rkjaran): handle errors (and client cancellations) properly

    streaming_asr = StreamingASR(conversation_id=conversation_id)

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
                elif data["event"] == "start":
                    current_app.logger.info("START: {}".format(message))
                    streaming_asr.stream_sid = data["start"]["streamSid"]
                elif data["event"] == "media":
                    yield data["media"]["payload"]
                elif data["event"] == "closed":
                    current_app.logger.info("CLOSE: {}".format(message))
                    ws.close()
                    break
                elif data["event"] == "mark":
                    current_app.logger.info("MARK")
                else:
                    current_app.logger.info(f"UNHANDLED_MSG_TYPE: {data['event']}")
        except:
            current_app.logger.exception("Something went wrong while receiving data.")
            raise

    for result in streaming_asr.recognize_stream(feed_data()):
        try:
            current_app.logger.info(f"ASR: {result}")

            masdif_resp = requests.put(
                f"{conversation_url}/{conversation_id}",
                json={
                    "text": result,
                    "metadata": {
                        "asr_generated": True,
                        "language": language_code,
                    },
                },
            )
            # TODO(rkjaran): handle non 200 status
            masdif_resp.raise_for_status()
            responses = masdif_resp.json()

            current_app.logger.info("Got responses: %s", responses)

            for response in responses:
                for attachment in response["data"]["attachment"]:
                    if attachment["type"] == "audio":
                        tts_resp = requests.get(attachment["payload"]["src"])
                        tts_resp.raise_for_status()

                        tts_audio = tts.encode_tts_response_for_twilio(tts_resp.content)

                        ws.send(
                            json.dumps(
                                {
                                    "event": "media",
                                    "streamSid": streaming_asr.stream_sid,
                                    "media": {
                                        "payload": tts_audio,
                                    },
                                }
                            )
                        )
                        ws.send(
                            json.dumps(
                                {
                                    "event": "mark",
                                    "streamSid": streaming_asr.stream_sid,
                                    "mark": {"name": "end_of_tts_audio"},
                                }
                            )
                        )

        except subprocess.CalledProcessError as e:
            current_app.logger.exception("Subprocess failure.")
        except:
            current_app.logger.exception(
                "Something went wrong while processing ASR data.",
            )
            raise
    current_app.logger.info("CONNECTION CLOSED.")
