import audioop
import base64
import json
from typing import Literal
import requests

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

    TTS_SAMPLE_RATE_IN: Literal[22050] = 22050
    TTS_SAMPLE_RATE_OUT: Literal[8000] = 8000

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
            tts_resp = requests.post(
                current_app.config["TTS_SERVER_URL"],
                json={
                    "Engine": "standard",
                    "LanguageCode": "is-IS",
                    "LexiconNames": [],
                    "OutputFormat": "pcm",
                    "SampleRate": str(TTS_SAMPLE_RATE_IN),
                    "SpeechMarkTypes": ["word"],
                    "Text": result,
                    "TextType": "text",
                    "VoiceId": current_app.config["TTS_VOICE_ID"],
                },
            )

            if tts_resp.status_code == 200:
                tts_audio = audioop.ratecv(
                    tts_resp.content,
                    2,
                    1,
                    TTS_SAMPLE_RATE_IN,
                    TTS_SAMPLE_RATE_OUT,
                    None,
                )[0]
                tts_audio = audioop.lin2ulaw(tts_audio, 2)
                tts_audio = bytes.decode(base64.b64encode(tts_audio))

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
            else:
                current_app.logger.warning(
                    f"TTS_REQ_FAILURE_CODE: {tts_resp.status_code}"
                )
        except:
            current_app.logger.exception(
                "Something went wrong while processing ASR data.",
            )
    current_app.logger.info("CONNECTION CLOSED.")
