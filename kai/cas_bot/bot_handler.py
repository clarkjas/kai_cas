import os
import logging
from typing import List
import re
import datetime
from kai.cas_bot.store import BaseStore, RedisStore
from kai.cas_bot.scheduler import BotScheduler
from kai.cas_bot.models import EVENT_WEEK, EVENT_DAY, ScheduledEvent, DATE_FORMAT
import uuid

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
    BroadcastRequest,
    ApiException
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
        failed_users = list()
        with ApiClient(self.configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            for user in users:
                success: bool = self.send_message(line_bot_api, user, message)
                if not success:
                    failed_users.append(user)
        return failed_users

    def send_message_to_user(self, user_id, message):
        with ApiClient(self.configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            success: bool = self.send_message(line_bot_api, user_id, message)
            return success

    def send_message(self, line_bot_api: MessagingApi, user_id, msg: str):
        try:
            response: PushMessageResponse = line_bot_api.push_message(PushMessageRequest(
                to=user_id,
                messages=[TextMessage(text=msg)]
            ))
            return True
        except ApiException as e:
            log.exception(e)
            if e.reason == "Bad Request":
                log.error("For our case, likely a bad user. Remove the user")
            return False


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

    def handle_interval(self, delta: int):
        log.info(f"Executing interval messaging on delta {delta}")
        messages_to_send: str = f"Events upcoming in {delta} days or less:\n"

        events: List[ScheduledEvent] = self.store.get_events()
        if not events:
            return

        now = datetime.datetime.now()
        from_now = now + datetime.timedelta(days=delta)
        for event in events:
            if event.event_date < from_now.date():
                messages_to_send += f"{event.event_date.strftime(DATE_FORMAT)} - {event.msg}\n"

        failed_users: list = self.messanger.send_message_to_all_users(self.store.get_all_users(), messages_to_send)
        for user in failed_users:
            log.error(f"Failed user request. Removing user. {user}")
            self.store.remove_user(user)

    def handle_maintenance(self):
        self.handle_day()
        events = self.store.get_events()
        for e in events:
            now = datetime.datetime.now().date()
            if e.event_date < now:
                log.info(f"Deleting old event: {str(e)}")
                self.store.remove_event(e.event_id)


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
                user_type: str = self.store.get_user_type(user_id)
                if user_type == "ADMIN":
                    response = self.process_event_request(text)
                    self.messanger.send_message_to_user(user_id, response)

    def process_event_request(self, text: str):
        pattern: str = r"^!(\w+)(?:,([^,]*),([^,]*))?$"
        match = re.match(pattern, text)
        if match:
            event = match.group(1)
            if event == 'addevent':
                return self.process_add_event_request(text)

    def process_add_event_request(self, text):
        pattern:str = r"^!(\w+),([\d-]+),(.+)$"
        match = re.match(pattern, text)
        if match:
            event = match.group(1)
            date = match.group(2)
            message = match.group(3)
            uid: str = str(uuid.uuid4())
            try:
                final_date = datetime.datetime.strptime(date, DATE_FORMAT)
            except ValueError as e:
                log.exception(f"Invalidate date format given in {text}", e)
                return f"Invalidate date format given in {text}"
            event: ScheduledEvent = ScheduledEvent(message, date, uid)
            log.info(f"creating event: {str(event)}")
            self.store.add_event(event)
            return "Event Added"
        return "Unable to add event"

    def handle(self, event, signature):
        log.info("Received handle request")
        self.handler.handle(event, signature)