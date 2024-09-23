import flask
import os
from kai.cas_bot import application

if __name__ == '__main__':
    app = application.flask_app
    app.run(host="0.0.0.0", port=8081)
else:
    gunicorn_app = application.flask_app
