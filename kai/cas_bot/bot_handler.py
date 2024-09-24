import os
import logging

from kai.cas_bot.store import BaseStore, MemStore
from kai.cas_bot.scheduler import BotScheduler

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
    PushMessageRequest,
    TextMessage,
    BroadcastRequest
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
    FollowEvent,
    UnfollowEvent
)


class LineBot:
    handler: WebhookHandler
    configuration: Configuration
    store: BaseStore
    scheduler: BotScheduler

    def __init__(self):
        log.info("Setting up linebot with handler and config")
        self.handler = WebhookHandler(os.environ['CHANNEL_SECRET'])
        self.configuration = Configuration(access_token=os.environ['ACCESS_TOKEN'])
        self.store = MemStore()
        self.scheduler = BotScheduler(self.event_cb, self.maintenance_cb)

    def event_cb(self):
        ...

    def maintenance_cb(self):
        log.info("Got maintenance Request")
        with ApiClient(self.configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            for user in self.store.get_all_users():
                line_bot_api.push_message(PushMessageRequest(
                    to=user, messages=[TextMessage(text="Bot doing Maintenance")]
                ))


    def get_handler(self):
        return self.handler

    def get_configuration(self):
        return self.configuration

    def create_handlers(self):
        log.info("Creating handlers")
        handler: WebhookHandler = self.handler

        @handler.add(FollowEvent)
        def handle_follow_event(event:FollowEvent):
            log.info(event)
            user_id = getattr(event.source, "user_id", None)
            if user_id:
                log.info(f"Got new user: {user_id}")
                self.store.add_user(user_id)

        @handler.add(UnfollowEvent)
        def handle_unfollow_event(event:UnfollowEvent):
            log.info(event)
            user_id = getattr(event.source, "user_id", None)
            if user_id:
                log.info(f"Got remove user: {user_id}")
                self.store.remove_user(user_id)

        @handler.default()
        def handle_default(event):
            log.info("Got default")
            log.info(event)

        @handler.add(MessageEvent, message=TextMessageContent)
        def handle_message(event):
            log.info(event)
            user_id = getattr(event.source, "user_id", None)
            if not self.store.user_exists(user_id):
                self.store.add_user(user_id)

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