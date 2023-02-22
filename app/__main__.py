"""
Main entry point for the application

Usage
-----
python -m app.<app_name> <app_args>

Examples
--------
python -m app.webapp # runs the HTTP webapp
python -m app.whatsapp # runs the whatsapp app
"""
import importlib
import logging
import sys

logger = logging.getLogger(__name__)

def main(app_name):
    module_name = get_module_name(app_name)
    if module_name is None:
        logger.error("Unknown job app_name: %s", app_name)
        return

    module = get_module(module_name)
    if module is None:
        logger.error(
            "Unknown module app_name: %s (job app_name: %s)", module_name, app_name
        )
        return

    if not hasattr(module, "main"):
        logger.error(
            "No main function in module %s (job app_name: %s)", module_name, app_name
        )
        return

    module.main()


def get_module_name(app_name):
    # if app_name in ["webapp", "api", "webchat", "apichat", "web-app", "web_app"]:
    #     return "app.webapp"

    if app_name in [
        "whatsapp-app",
        "whatsappapp",
        "whatsapp",
        "twillioapp",
        "twillio",
        "whatsappchat",
        "whatsapp-app",
        "whatsapp_app",
    ]:
        return "app.whatsapp"

    return None


def get_module(module_name):
    module_spec = importlib.util.find_spec(module_name)
    if module_spec is None:
        return None

    module = importlib.import_module(module_name)

    return module


if __name__ == "__main__":
    import typer, dotenv

    args = sys.argv
    logging.basicConfig()
    dotenv.load_dotenv()
    if len(args) == 1:
        # Defaults to webapp
        logging.info("Starting server for web app")
        from app.webapp.__main__ import main

        typer.run(main)
    else:
        app_name = args[1]
        module_name = get_module_name(app_name)
        if module_name is None:
            logger.error("Unknown job app_name: %s", app_name)
            sys.exit(1)
        logging.info("Starting server for app: %s", app_name)
        module = importlib.import_module(module_name + ".__main__")
        sys.argv = args[1:]
        typer.run(module.main)
else:
    logging.warn("Not starting. Try: python3 -m app")
