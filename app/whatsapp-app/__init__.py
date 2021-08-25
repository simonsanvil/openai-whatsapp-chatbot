from .whatsapp_app import app
import os
def main():
    app.run(debug=False, port=int(os.environ.get('PORT', 8000)))
    # app.run()