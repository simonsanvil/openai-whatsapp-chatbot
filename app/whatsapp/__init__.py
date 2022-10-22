from .whatsapp_app import app, send_whatsapp_message
import os,sys

__all__ = ['app','send_whatsapp_message']

sys.path.append('whatsapp-app')
def main():
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 8000)))
    # app.run()