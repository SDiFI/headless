import audioop
import base64
from typing import Iterable, Iterator, Optional

import grpc
from flask import current_app
from proto.sdifi.speech.v1alpha.speech_pb2 import (
    RecognitionConfig,
    StreamingRecognitionConfig,
    StreamingRecognizeRequest,
)
from proto.sdifi.speech.v1alpha.speech_pb2_grpc import SpeechServiceStub as SpeechStub


class StreamingASR:
    _stub: Optional[SpeechStub] = None
    _channel: Optional[grpc.Channel] = None
    _creds: Optional[grpc.ChannelCredentials] = None

    _stream_started: bool = False
    _stream_sid: Optional[str] = None

    # These values are hard-coded for now.
    _preferred_sample_rate: int = 16000
    _language_code: str = "is-IS"

    _conversation_id: str

    def __init__(self, /, *, conversation_id) -> None:
        self._set_creds()
        self._init_stub()
        self._conversation_id = conversation_id

    def is_secure(self) -> bool:
        return current_app.config["ASR_SERVER_URL"].startswith("grpcs://")

    def _set_creds(self):
        self.creds = (
            grpc.ssl_channel_credentials()
            if self.is_secure()
            else grpc.insecure_server_credentials()
        )

    def _init_stub(self):
        if self.is_secure():
            self._channel = grpc.secure_channel(
                current_app.config["ASR_SERVER_URL"].removeprefix("grpcs://"),
                self.creds,
            )
        else:
            self._channel = grpc.insecure_channel(
                current_app.config["ASR_SERVER_URL"].removeprefix("grpc://")
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
                        conversation=self._conversation_id,
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
                        if res.is_final and len(transcript) > 0:
                            final_transcripts.append(transcript)
                if final_transcripts:
                    yield "".join(final_transcripts)
                    final_transcripts = []
        except:
            current_app.logger.exception(
                "Something went wrong during server-ASR interaction."
            )
            raise

    @property
    def stream_sid(self):
        return self._stream_sid

    @stream_sid.setter
    def stream_sid(self, stream_sid_val: str):
        self._stream_sid = stream_sid_val
