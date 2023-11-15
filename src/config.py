import flask_env


class EnvvarConfig(metaclass=flask_env.MetaFlaskEnv):
    MASDIF_SERVER_URL = "http://localhost:8080"
    ASR_SERVER_URL = "grpc://localhost:50051"
    SOCK_SERVER_OPTIONS = {"ping_interval": 25}
    PORT = 9001
