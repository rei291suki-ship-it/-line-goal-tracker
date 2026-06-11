from database import get_all_user_ids, get_today_goals, get_week_goals
from line_api import push_message
from formatting import morning_message, evening_message, weekly_message


async def send_morning_notifications():
    for user_id in get_all_user_ids():
        goals = get_today_goals(user_id)
        msg = morning_message(goals)
        await push_message(user_id, msg)


async def send_evening_notifications():
    for user_id in get_all_user_ids():
        goals = get_today_goals(user_id)
        msg = evening_message(goals)
        if msg:
            await push_message(user_id, msg)


async def send_weekly_notifications():
    for user_id in get_all_user_ids():
        week_data = get_week_goals(user_id)
        msg = weekly_message(week_data)
        if msg:
            await push_message(user_id, msg)
