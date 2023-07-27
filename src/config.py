import flask_env


class EnvvarConfig(metaclass=flask_env.MetaFlaskEnv):
    TIRO_ACCESS_TOKEN = ""
    ASR_SERVER_URL = "speech.talgreinir.is:443"
    TTS_SERVER_URL = "https://tts.tiro.is/v0/speech"
    TTS_VOICE_ID = "Dilja_v2"
    SOCK_SERVER_OPTIONS = {"ping_interval": 25}
    PORT = 9001
