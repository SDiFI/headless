from src import init_app

app = init_app()
if __name__ == "__main__":
    port: int = app.config["PORT"]
    app.logger.info(f"Server listening on port: {port}.")
    app.run(host="0.0.0.0", port=port, debug=True)
