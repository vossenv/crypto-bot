import asyncio
import logging
import math
from datetime import datetime, timedelta

import pytz
from dateutil.parser import parse, ParserError

config_loader = None


class Countdown():

    def __init__(self, alert_time, name, schedule=None, callback=None, channels=None, alert_date=None, message=None):

        self.alert_date = self.parse_date(alert_date).date() if alert_date else None
        self.alert_time = self.parse_date(alert_time)
        if self.alert_date is not None:
            self.alert_time = datetime.combine(self.alert_date, self.alert_time.time())
        else:
            self.alert_time = datetime.combine(datetime.utcnow(), self.alert_time.time())
        self.alert_time = pytz.timezone("UTC").localize(self.alert_time)
        self.message = message
        self.name = name
        self.logger = logging.getLogger(name)
        self.channels = channels
        self.callback = callback
        if not schedule:
            self.notifications = {}
        else:
            if isinstance(schedule, list):
                self.schedule = {a: None for a in schedule}
            else:
                self.schedule = dict(schedule)
            self.notifications = self.create_notifications()
        self.notifications[self.alert_time] = self.message

    def create_notifications(self):
        return {self.alert_time - timedelta(minutes=t): m for t, m in self.schedule.items()}

    def parse_date(self, date_obj) -> datetime:
        try:
            date_obj = parse(date_obj, ignoretz=True)
            return pytz.timezone("UTC").localize(date_obj)
        except ParserError:
            raise AssertionError(
                "Invalid time format {} - please specific in 24 hour %H:%M:%S".format(date_obj))

    def now(self) -> datetime:
        return pytz.timezone("UTC").localize(datetime.utcnow())

    def delta_to_event(self):
        return round((self.alert_time - self.now()).total_seconds() / 60)

    def get_alert_message(self, custom=None):
        if custom:
            return custom.replace('%%time%%', str(self.delta_to_event()))
        return "**Alert!** {} minutes to {}!".format(self.delta_to_event(), self.name)

    async def send_message(self, msg):
        await self.callback(msg, self.channels)

    async def run_loop(self):
        n = self.notifications
        while True:
            now = self.now()
            for t in list(n):
                try:
                    m = math.floor((now - t).total_seconds() / 60)
                    if m < 0:
                        continue
                    if m == 0:
                        msg = self.get_alert_message(n[t])
                        self.logger.debug(msg)
                        await self.send_message(msg)
                    if not self.alert_date:
                        new = t + timedelta(days=1)
                        n[new] = n[t]
                        if t == self.alert_time:
                            self.alert_time = new
                    else:
                        self.logger.debug("Discarding old alert: {} {}".format(t, n[t]))
                    n.pop(t)
                except Exception as e:
                    self.logger.error("Error sending notification: {}".format(e))
            if not n:
                break
            await asyncio.sleep(5)
