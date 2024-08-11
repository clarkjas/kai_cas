import flask

flask_app=flask.Flask(__name__)


@flask_app.route("/health")
def ping():
    return "OK"
