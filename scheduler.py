import os
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

TIMEZONE = pytz.timezone("Asia/Tokyo")
MORNING_HOUR = int(os.getenv("MORNING_HOUR", "7"))
EVENING_HOUR = int(os.getenv("EVENING_HOUR", "22"))


def start_scheduler() -> AsyncIOScheduler:
    from notifications import (
        send_morning_notifications,
        send_evening_notifications,
        send_weekly_notifications,
    )

    scheduler = AsyncIOScheduler(timezone=TIMEZONE)
    scheduler.add_job(
        send_morning_notifications,
        CronTrigger(hour=MORNING_HOUR, minute=0, timezone=TIMEZONE),
        id="morning",
    )
    scheduler.add_job(
        send_evening_notifications,
        CronTrigger(hour=EVENING_HOUR, minute=0, timezone=TIMEZONE),
        id="evening",
    )
    scheduler.add_job(
        send_weekly_notifications,
        CronTrigger(day_of_week="sun", hour=EVENING_HOUR, minute=0, timezone=TIMEZONE),
        id="weekly",
    )
    scheduler.start()
    return scheduler
