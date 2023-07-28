import audioop
import base64
from typing import Iterable, Iterator, Optional

import grpc
from flask import current_app
from lr.speech.v2beta1.speech_pb2 import (
    RecognitionConfig,
    StreamingRecognitionConfig,
    StreamingRecognizeRequest,
)
from lr.speech.v2beta1.speech_pb2_grpc import SpeechStub


class StreamingASR:
    _stub: Optional[SpeechStub] = None
    _channel: Optional[grpc.Channel] = None
    _creds: Optional[grpc.ChannelCredentials] = None

    _stream_started: bool = False

    # These values are hard-coded for now.
    _preferred_sample_rate: int = 16000
    _language_code: str = "is-IS"

    def __init__(self) -> None:
        self._set_creds()
        self._init_stub()

    def _set_creds(self):
        self.creds = grpc.composite_channel_credentials(
            grpc.ssl_channel_credentials(),
            grpc.access_token_call_credentials(current_app.config["TIRO_ACCESS_TOKEN"]),
        )

    def _init_stub(self):
        self._channel = grpc.secure_channel(
            current_app.config["ASR_SERVER_URL"], self.creds
        )
        self._stub = SpeechStub(self._channel)

    def _requests(
        self, media_payload: Optional[Iterable[bytes]] = None
    ) -> Iterator[StreamingRecognizeRequest]:
        try:
            if not media_payload:
                return

            if not self._stream_started:
                yield StreamingRecognizeRequest(
                    streaming_config=StreamingRecognitionConfig(
                        interim_results=True,
                        config=RecognitionConfig(
                            encoding=RecognitionConfig.LINEAR16,
                            sample_rate_hertz=self._preferred_sample_rate,
                            language_code=self._language_code,
                        ),
                    )
                )
                self._stream_started = True
            for chunk in media_payload:
                # Change data encoding for our ASR service.
                audio_data = base64.b64decode(chunk)
                audio_data = audioop.ulaw2lin(audio_data, 2)
                audio_data = audioop.ratecv(
                    audio_data, 2, 1, 8000, self._preferred_sample_rate, None
                )[0]

                yield StreamingRecognizeRequest(
                    audio_content=audio_data,
                )
        except:
            current_app.logger.exception(
                "Something went wrong while generating ASR requests."
            )
            raise

    def recognize_stream(self, media_payload: Iterable[bytes]) -> Iterable[str]:
        try:
            responses = self._stub.StreamingRecognize(self._requests(media_payload))
            final_transcripts = []
            for response in responses:
                for res in response.results:
                    if len(res.alternatives) > 0:
                        transcript = res.alternatives[0].transcript
                        if res.is_final:
                            final_transcripts.append(transcript)
                        yield "{}{}".format("".join(final_transcripts), transcript)
            yield "".join(final_transcripts)
        except:
            current_app.logger.exception(
                "Something went wrong during server-ASR interaction."
            )
            raise
