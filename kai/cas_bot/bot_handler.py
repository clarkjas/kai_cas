import os
import logging
from typing import List
import datetime
from kai.cas_bot.store import BaseStore, RedisStore
from kai.cas_bot.scheduler import BotScheduler
from kai.cas_bot.models import EVENT_WEEK, EVENT_DAY, ScheduledEvent

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
    PushMessageResponse,
    TextMessage,
    BroadcastRequest
)

from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
    FollowEvent,
    UnfollowEvent
)

log = logging.getLogger(__name__)


class Messanger:
    configuration: Configuration

    def __init__(self, configuration: Configuration):
        self.configuration = configuration

    def send_message_to_all_users(self, users: list, message: str):
        try:
            with ApiClient(self.configuration) as api_client:
                line_bot_api = MessagingApi(api_client)
                for user in users:
                    response: PushMessageResponse = line_bot_api.push_message(PushMessageRequest(
                        to=user, messages=[TextMessage(text=message)]
                    ))
                    print(response)
        except Exception as e:
            log.exception("Failed while sending to all users", e)

    def send_message_to_user(self, user_id, message):
        try:
            with ApiClient(self.configuration) as api_client:
                line_bot_api = MessagingApi(api_client)
                response: PushMessageResponse = line_bot_api.push_message(PushMessageRequest(
                    to=user_id, messages=[TextMessage(text=message)]
                ))
                print(response)
        except Exception as e:
            log.exception("Failed while sending to all users", e)


class ScheduledEventHandler:
    store: BaseStore
    messanger: Messanger

    def __init__(self, store: BaseStore, messanger: Messanger):
        self.store = store
        self.messanger = messanger

    def handle_event(self, event_type):
        log.info(f"Got event: {event_type}")
        if event_type == EVENT_WEEK:
            self.handle_week()

        if event_type == EVENT_DAY:
            self.handle_day()

    def handle_day(self):
        self.handle_interval(7)

    def handle_week(self):
        self.handle_interval(30)

    def handle_interval(self, delta:int):
        log.info(f"Executing interval messaging on delta {delta}")
        messages_to_send: str = f"Events upcoming in {delta} days or less:\n"

        events: List[ScheduledEvent] = self.store.get_events()
        now = datetime.datetime.now()
        from_now = now + datetime.timedelta(days=delta)
        for event in events:
            if event.event_date < from_now.date():
                messages_to_send += f"{event.event_date.strftime("%m-%d-%Y")} - {event.msg}\n"

        self.messanger.send_message_to_all_users(self.store.get_all_users(), messages_to_send)

    def handle_maintenance(self):
        self.handle_day()


class LineBot:
    handler: WebhookHandler
    configuration: Configuration
    store: BaseStore
    scheduler: BotScheduler
    event_handler: ScheduledEventHandler
    messanger: Messanger

    def __init__(self):
        log.info("Setting up linebot with handler and config")
        self.handler = WebhookHandler(os.environ['CHANNEL_SECRET'])
        self.configuration = Configuration(access_token=os.environ['ACCESS_TOKEN'])
        self.store = RedisStore()
        self.scheduler = BotScheduler(self.event_cb, self.maintenance_cb)
        self.messanger = Messanger(self.configuration)
        self.event_handler = ScheduledEventHandler(self.store, self.messanger)

    def event_cb(self, event_type: str):
        self.event_handler.handle_event(event_type)

    def maintenance_cb(self):
        self.event_handler.handle_maintenance()

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

            text: str = event.message.text
            if text.startswith("!"):
                ...

            # with ApiClient(self.configuration) as api_client:
            #     line_bot_api = MessagingApi(api_client)
            #     line_bot_api.reply_message_with_http_info(
            #         ReplyMessageRequest(
            #             reply_token=event.reply_token,
            #             messages=[TextMessage(text=event.message.text)]
            #         )
            #     )

    def process_set_event_request(self, text:str):
        data = text.split(text)


    def handle(self, event, signature):
        log.info("Received handle request")
        self.handler.handle(event, signature)