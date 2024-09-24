from flask import Flask, request, abort
import os
import logging
from kai.cas_bot.bot_handler import LineBot

from linebot.v3 import (
    WebhookHandler
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent
)

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

flask_app = Flask(__name__)
bot: LineBot = LineBot()
bot.create_handlers()


@flask_app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    flask_app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        bot.handle(body, signature)
    except InvalidSignatureError:
        flask_app.logger.info("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)
    return 'OK'


@flask_app.route("/health")
def ping():
    return "OK"
