from .app import app
import os

def main():
    # start the app
    app.run(debug=False, host=os.environ.get('APP_HOST', '0.0.0.0'), port=int(os.environ.get('APP_PORT', 8000)))

if __name__=='__main__':
    main()