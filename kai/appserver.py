import flask
import os
from cas_bot import application

PORT: int = int(os.environ['SERVER_PORT'])
HOSTNAME: str = os.environ['SERVER_HOSTNAME']

if __name__ == '__main__':
    app = application.flask_app
    app.run(hostname=HOSTNAME, port=PORT)
else:
    gunicorn_app = application.flask_app
