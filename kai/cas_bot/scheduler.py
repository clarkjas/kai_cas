import logging
from apscheduler.schedulers.background import BackgroundScheduler
from kai.cas_bot.models import EVENT_WEEK, EVENT_DAY

# scheduler = BackgroundScheduler()
# scheduler.add_jobstore('redis', 'text_scheduler', run_times_key='test.run_times')
# scheduler.start()
log = logging.getLogger(__name__)


class BotScheduler:
    scheduler: BackgroundScheduler

    def __init__(self, event_cb, maint_cb):
        self.event_cb = event_cb
        self.maintenance_cb = maint_cb
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        self.scheduler.add_job(self.maintenance, 'interval', minutes=1)
        self.scheduler.add_job(self.event_cb, "interval", ['EVENT_WEEK'], weeks=1)
        self.scheduler.add_job(self.event_cb, "interval", ['EVENT_DAY'], days=1)

    def maintenance(self):
        self.maintenance_cb()
