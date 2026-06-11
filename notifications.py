from database import get_all_user_ids, get_today_status, get_week_status
from line_api import push_message
from formatting import morning_message, evening_message, weekly_message


async def send_morning_notifications():
    msg = morning_message()
    for user_id in get_all_user_ids():
        await push_message(user_id, msg)


async def send_evening_notifications():
    for user_id in get_all_user_ids():
        goals = get_today_status(user_id)
        await push_message(user_id, evening_message(goals))


async def send_weekly_notifications():
    for user_id in get_all_user_ids():
        week_data = get_week_status(user_id)
        msg = weekly_message(week_data)
        if msg:
            await push_message(user_id, msg)
