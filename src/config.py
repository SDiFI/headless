import os

import flask_env


class EnvvarConfig(metaclass=flask_env.MetaFlaskEnv):
    TIRO_ACCESS_TOKEN = os.environ.get("TIRO_ACCESS_TOKEN", "")
    ASR_SERVER_URL = os.environ.get("ASR_SERVER_URL", "speech.talgreinir.is:443")
    SOCK_SERVER_OPTIONS = os.environ.get("SOCK_SERVER_OPTIONS", {"ping_interval": 25})
    PORT = os.environ.get("PORT", 9001)
