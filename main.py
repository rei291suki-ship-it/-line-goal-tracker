import hashlib
import hmac
import base64
import json
import os
import unicodedata
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

from database import init_db, register_user, update_goal_status, get_today_status
from line_api import reply_message
from formatting import format_status
from goals_config import FIXED_GOALS
from scheduler import start_scheduler

LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")

HELP_TEXT = """📌 コマンド一覧

○ [番号] — 達成
△ [番号] [メモ] — 部分達成
✕ [番号] — 未達成
一覧 — 今日の状況を確認
ヘルプ — このメッセージ

例:
○ 1
△ 5 20分
✕ 3"""

WELCOME_TEXT = (
    "🌟 目標管理ボットへようこそ！\n\n"
    "○ △ ✕ で毎日の達成状況を記録できます。\n"
    "「ヘルプ」でコマンド一覧を確認してください。"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    start_scheduler()
    yield


app = FastAPI(lifespan=lifespan)


def _verify_signature(body: bytes, signature: str) -> bool:
    digest = hmac.new(LINE_CHANNEL_SECRET.encode(), body, hashlib.sha256).digest()
    return base64.b64encode(digest).decode() == signature


# ①=U+2460 ～ ⑤=U+2464 をコードポイントで生成（ソースファイルの文字化け対策）
CIRCLED = {chr(0x2460 + i): i + 1 for i in range(5)}


def _clean(text: str) -> str:
    # 不可視文字・制御文字・異体字セレクタを除去
    return "".join(c for c in text if unicodedata.category(c) not in ("Cf", "Cc"))


def _parse_index(s: str) -> int | None:
    try:
        idx = int(s.strip())
        if 1 <= idx <= len(FIXED_GOALS):
            return idx
    except ValueError:
        pass
    return None


def _handle_command(text: str, user_id: str) -> str:
    text = _clean(text.strip())
    first = text[0] if text else ""

    # 先頭の丸数字を全部収集（例: ①②できた → [1, 2]）
    indices = []
    for ch in text:
        if ch in CIRCLED:
            indices.append(CIRCLED[ch])
        else:
            break
    if indices:
        for idx in indices:
            update_goal_status(user_id, idx, "done")
        lines = [f"{FIXED_GOALS[idx-1]['symbol']}{FIXED_GOALS[idx-1]['text']}　達成！" for idx in indices]
        return "\n".join(lines) + f"\n\n{format_status(get_today_status(user_id))}"

    if first == "○":
        parts = text[1:].strip().split(None, 1)
        idx = _parse_index(parts[0]) if parts else None
        if not idx:
            return "番号を入力してください。\n例: ○ 1"
        update_goal_status(user_id, idx, "done")
        g = FIXED_GOALS[idx - 1]
        return f"○ {g['symbol']}{g['text']} 達成！\n\n{format_status(get_today_status(user_id))}"

    if first == "△":
        parts = text[1:].strip().split(None, 1)
        idx = _parse_index(parts[0]) if parts else None
        if not idx:
            return "番号とメモを入力してください。\n例: △ 5 20分"
        note = parts[1].strip() if len(parts) > 1 else None
        update_goal_status(user_id, idx, "partial", note)
        g = FIXED_GOALS[idx - 1]
        return f"△ {g['symbol']}{g['text']} 部分達成！\n\n{format_status(get_today_status(user_id))}"

    if first in ("✕", "×", "✗"):
        idx = _parse_index(text[1:].strip())
        if not idx:
            return "番号を入力してください。\n例: ✕ 1"
        update_goal_status(user_id, idx, "failed")
        g = FIXED_GOALS[idx - 1]
        return f"✕ {g['symbol']}{g['text']} を記録しました\n\n{format_status(get_today_status(user_id))}"

    if text in ("一覧", "状況", "list"):
        return format_status(get_today_status(user_id))

    if text in ("テスト朝", "test朝"):
        from formatting import morning_message
        return morning_message()

    if text in ("テスト夜", "test夜"):
        from formatting import evening_message
        return evening_message(get_today_status(user_id))

    if text in ("テスト週", "test週"):
        from formatting import weekly_message
        from database import get_week_status
        return weekly_message(get_week_status(user_id))

    if text in ("ヘルプ", "help", "？", "?"):
        return HELP_TEXT

    return "「ヘルプ」でコマンド一覧を確認してください。"


@app.post("/webhook")
async def webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("X-Line-Signature", "")

    if not _verify_signature(body, signature):
        raise HTTPException(status_code=400, detail="Invalid signature")

    data = json.loads(body)

    for event in data.get("events", []):
        user_id = event["source"].get("userId")
        if not user_id:
            continue

        if event["type"] == "follow":
            register_user(user_id)
            await reply_message(event["replyToken"], WELCOME_TEXT)

        elif event["type"] == "message" and event["message"]["type"] == "text":
            register_user(user_id)
            response = _handle_command(event["message"]["text"], user_id)
            await reply_message(event["replyToken"], response)

    return JSONResponse({"status": "ok"})


@app.get("/")
async def health():
    return {"status": "running"}
