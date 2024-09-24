import flask
import os
from kai.cas_bot import wsgi

if __name__ == '__main__':
    app = wsgi.flask_app
    app.run(host="0.0.0.0", port=8081)
else:
    gunicorn_app = wsgi.flask_app
