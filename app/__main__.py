import importlib
import logging
import sys
import os

logger = logging.getLogger(__name__)

def run_main(app_name):
    module_name = get_module_name(app_name)
    if module_name is None:
        logger.error("Unknown job app_name: %s", app_name)
        return

    module = get_module(module_name)
    if module is None:
        logger.error("Unknown module app_name: %s (job app_name: %s)",
                     module_name, app_name)
        return

    if not hasattr(module, 'main'):
        logger.error(
            "No main function in module %s (job app_name: %s)", module_name, app_name)
        return

    module.main()

def get_module_name(app_name):
    if app_name in ['webapp','api','webchat','apichat','web-app','web_app']:
        return "app.webapp"

    if app_name in ['whatsapp-app','whatsappapp','whatsapp','twillioapp','twillio','whatsappchat','whatsapp-app','whatsapp_app']:
        return "app.whatsapp-app"

    return None


def get_module(module_name):
    module_spec = importlib.util.find_spec(module_name)
    if module_spec is None:
        return None

    module = importlib.import_module(module_name)

    return module

if __name__ == '__main__':
    args = sys.argv
    if len(args)==1:
        logging.info("Starting server for web app")
        run_main('webapp')
    else:
        app_name = args[1]
        run_main(app_name)
else:
    logging.warn("Not starting. Try: python3 -m app")