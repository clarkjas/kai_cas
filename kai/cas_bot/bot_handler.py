import os
import logging

log = logging.getLogger(__name__)

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


class LineBot:
    handler: WebhookHandler
    configuration: Configuration

    def __init__(self):
        log.info("Setting up linebot with handler and config")
        self.handler = WebhookHandler(os.environ['CHANNEL_SECRET'])
        self.configuration = Configuration(access_token=os.environ['ACCESS_TOKEN'])

    def get_handler(self):
        return self.handler

    def get_configuration(self):
        return self.configuration

    def create_handlers(self):
        log.info("Creating handlers")
        handler:WebhookHandler = self.handler

        @handler.add(MessageEvent, message=TextMessageContent)
        def handle_message(event):
            log.info(event)
            with ApiClient(self.configuration) as api_client:
                line_bot_api = MessagingApi(api_client)
                line_bot_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=event.message.text)]
                    )
                )

    def handle(self, event, signature):
        log.info("Received handle request")
        self.handler.handle(event, signature)