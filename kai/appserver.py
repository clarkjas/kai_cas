import flask
import os
from cas_bot import application

SERVER_PORT: int = int(os.environ['SERVER_PORT'])
SERVER_HOSTNAME: str = os.environ['SERVER_HOSTNAME']

if __name__ == '__main__':
    app = application.flask_app
    app.run(host=SERVER_HOSTNAME, port=SERVER_PORT)
else:
    gunicorn_app = application.flask_app
