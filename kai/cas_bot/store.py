import os
import redis
from urllib.parse import urlparse
import logging
from typing import List
import json
from kai.cas_bot.models import ScheduledEvent, USER_NAME_MAP

log = logging.getLogger(__name__)


class BaseStore:

    def user_exists(self, user_id) -> bool:
        ...

    def add_user(self, user_id) -> None:
        ...

    def remove_user(self, user_id) -> None:
        ...

    def get_user_type(self, user_id) -> str:
        ...

    def get_all_users(self) -> List[str]:
        ...

    def add_event(self, event: ScheduledEvent) -> None:
        ...

    def get_events(self) -> List[ScheduledEvent]:
        ...

    def remove_event(self, event_id) -> None:
        ...


class RedisStore(BaseStore):
    redis: redis.Redis

    def __init__(self):
        log.info("Connecting to redis")
        url = urlparse(os.environ.get("REDIS_TLS_URL"))
        self.redis = redis.Redis(host=url.hostname, port=url.port, password=url.password, ssl=(url.scheme == "rediss"),
                                 ssl_cert_reqs=None)

    def user_exists(self, user_id):
        return self.redis.hexists(USER_NAME_MAP, user_id) > 0

    def add_user(self, user_id):
        self.redis.hset(USER_NAME_MAP, user_id, "USER")

    def get_user_type(self, user_id):
        if not self.user_exists(user_id):
            return ""
        ut = self.redis.hget(USER_NAME_MAP, user_id).decode('utf-8')
        return ut

    def remove_user(self, user_id):
        self.redis.hdel(USER_NAME_MAP, user_id)

    def get_all_users(self):
        data = [a.decode('utf-8') for a in self.redis.hgetall(USER_NAME_MAP)]
        return data

    def add_event(self, event: ScheduledEvent):
        data: str = json.dumps(event.to_dict())
        key: str = f"event:{event.event_id}"
        self.redis.set(key, data)

    def get_events(self):
        results: list = list()
        keys = self.redis.keys("event:*")
        for k in keys:
            raw_data: bytes = self.redis.get(k)
            if raw_data:
                data = json.loads(raw_data.decode('utf-8'))
                results.append(ScheduledEvent.from_dict(data))
        return results

    def remove_event(self, event_id):
        self.redis.delete(f"event:{event_id}")


if __name__ == "__main__":
    store = RedisStore()
    print(store.user_exists("a"))
    store.add_user("a")
    print(store.get_user_type("a"))
    print(store.user_exists("a"))
    print(store.get_all_users())
    store.remove_user("a")
    print(store.get_all_users())
    print(store.user_exists("a"))

    events = store.get_events()
    [print(e) for e in events]
    store.add_event(ScheduledEvent("ok", '07-14-1977', '123'))
    events: List[ScheduledEvent] = store.get_events()
    [print(e) for e in events]
    for e in events:
        store.remove_event(e.event_id)
    events = store.get_events()
    print(events)
