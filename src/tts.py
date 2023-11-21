import subprocess
import base64


TTS_SAMPLE_RATE_OUT = 8000


def encode_tts_response_for_twilio(content: bytes) -> str:
    tts_conv = subprocess.run(
        [
            "ffmpeg",
            "-nostats",
            "-hide_banner",
            "-i",
            "-",
            "-c:a",
            "pcm_mulaw",
            "-ar",
            str(TTS_SAMPLE_RATE_OUT),
            "-f",
            "mulaw",
            "-",
        ],
        capture_output=True,
        check=True,
        input=content,
    )

    return bytes.decode(base64.b64encode(tts_conv.stdout))
