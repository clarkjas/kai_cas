import datetime
import json
import uuid
EVENT_DAY: str = "DAY"
EVENT_WEEK: str = "WEEK"
USER_NAME_MAP: str = "USERS"
DATE_FORMAT="%m-%d-%Y"


class ScheduledEvent:
    msg: str
    event_date: datetime.date
    event_id:str

    def __init__(self, msg: str, event_date:str, event_id:str):
        self.event_date = datetime.datetime.strptime(event_date, DATE_FORMAT).date()
        self.msg = msg
        self.event_id = event_id

    @staticmethod
    def from_dict(d):
        return ScheduledEvent(**d)

    def to_dict(self):
        return {"msg": self.msg, "event_date": self.event_date.strftime(DATE_FORMAT), "event_id": self.event_id}

    def __str__(self):
        return f"EventId: {self.event_id}\tMsg: {self.msg}\tDate: {self.event_date.strftime(DATE_FORMAT)}"


if __name__ == "__main__":
    d={'msg': "Ok", 'event_date': '01-01-2001', 'event_id': "123"}
    e:ScheduledEvent = ScheduledEvent.from_dict(d)
    print(e.msg)
    print(e.event_date)
    print(e.event_id)
    d2 = e.to_dict()
    print(d2)


