import hashlib
import hmac
import base64
import json
import os
from contextlib import asynccontextmanager
from datetime import date

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

from database import init_db, register_user, add_goal, complete_goal, get_today_goals
from line_api import reply_message
from formatting import format_goals, calc_rate
from scheduler import start_scheduler

LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")

HELP_TEXT = """📌 コマンド一覧

追加 [目標] — 今日の目標を追加
完了 [番号] — 目標を完了にする
一覧 — 今日の目標と達成率を表示
ヘルプ — このメッセージを表示

例:
追加 運動30分
完了 1
一覧"""

WELCOME_TEXT = (
    "🌟 目標管理ボットへようこそ！\n\n"
    "「追加 [目標]」で今日の目標を登録してください。\n"
    "「ヘルプ」でコマンド一覧を確認できます。"
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


def _handle_command(text: str, user_id: str) -> str:
    text = text.strip()

    if text.startswith("追加 ") or text.startswith("目標 "):
        goal_text = text.split(" ", 1)[1].strip()
        if not goal_text:
            return "目標を入力してください。\n例: 追加 運動30分"
        add_goal(user_id, goal_text)
        goals = get_today_goals(user_id)
        return f"✅ 追加しました！\n\n今日の目標（{date.today().strftime('%m/%d')}）:\n{format_goals(goals)}"

    if text.startswith("完了 "):
        try:
            num = int(text.split(" ", 1)[1].strip())
        except ValueError:
            return "番号を入力してください。\n例: 完了 1"
        if complete_goal(user_id, num):
            goals = get_today_goals(user_id)
            rate = calc_rate(goals)
            return f"🎉 #{num} 完了！達成率: {rate}%\n\n{format_goals(goals)}"
        return f"目標 #{num} が見つかりません。「一覧」で番号を確認してください。"

    if text in ("一覧", "リスト", "状況", "list", "status"):
        goals = get_today_goals(user_id)
        if not goals:
            return "今日の目標はまだ登録されていません。\n「追加 [目標]」で追加してください。"
        rate = calc_rate(goals)
        return f"📋 今日の目標（{date.today().strftime('%m/%d')}）達成率: {rate}%\n\n{format_goals(goals)}"

    if text in ("ヘルプ", "help", "？", "?"):
        return HELP_TEXT

    return "コマンドが認識できませんでした。\n「ヘルプ」でコマンド一覧を確認してください。"


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
