from .app import app, send_whatsapp_message
import os,sys

__all__ = ['app','send_whatsapp_message']

def main():
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 8000)))

if __name__=='__main__':
    app.run(debug=False)