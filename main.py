from src import init_server

server = init_server()
if __name__ == "__main__":
    server.log.info(f"Server listening on port {str(server.server_port)}.")
    server.serve_forever()
