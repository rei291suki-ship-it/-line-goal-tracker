import os
import httpx

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")

_HEADERS = lambda: {"Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"}


async def reply_message(reply_token: str, text: str):
    async with httpx.AsyncClient() as client:
        await client.post(
            "https://api.line.me/v2/bot/message/reply",
            headers=_HEADERS(),
            json={"replyToken": reply_token, "messages": [{"type": "text", "text": text}]},
        )


async def push_message(user_id: str, text: str):
    async with httpx.AsyncClient() as client:
        await client.post(
            "https://api.line.me/v2/bot/message/push",
            headers=_HEADERS(),
            json={"to": user_id, "messages": [{"type": "text", "text": text}]},
        )
