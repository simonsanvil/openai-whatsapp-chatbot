"""
Run the app that handles whatsapp conversations with the agent
"""
from .app import app
import typer


def main(port: int = None, host: str = "0.0.0.0", debug: bool = False):
    """
    Run the app that handles whatsapp conversations with the agent

    Args:
        port (int, optional): Port to run the app on. Defaults to null.
        host (str, optional): Host to run the app on. Defaults to "*"
        debug (bool, optional): Run the app in debug mode. Defaults to False.
    """
    print(f"Starting server for whatsapp app on {host}:{port}")
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    typer.run(main)
