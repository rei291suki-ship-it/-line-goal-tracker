from datetime import date

WEEKDAYS_JA = ["月", "火", "水", "木", "金", "土", "日"]
STATUS_WEIGHT = {"done": 1.0, "partial": 0.5, "failed": 0.0, "pending": 0.0}
STATUS_SYMBOL = {"done": "○", "partial": "△", "failed": "✕", "pending": "　"}


def _today_date_str() -> str:
    d = date.today()
    return f"{d.month}月{d.day}日{WEEKDAYS_JA[d.weekday()]}曜日"


def calc_rate(goals: list[dict]) -> int:
    if not goals:
        return 0
    return round(sum(STATUS_WEIGHT.get(g["status"], 0) for g in goals) / len(goals) * 100)


def _group_goals(goals: list) -> dict:
    groups: dict[str, list] = {}
    for g in goals:
        groups.setdefault(g["category"], []).append(g)
    return groups


def format_status(goals: list[dict]) -> str:
    lines = []
    for category, items in _group_goals(goals).items():
        lines.append(f"【{category}】")
        for g in items:
            sym = STATUS_SYMBOL.get(g["status"], "　")
            note = f"({g['note']})" if g.get("note") else ""
            lines.append(f"{g['symbol']}{g['text']} {sym}{note}")
        lines.append("")
    lines.append(f"達成率: {calc_rate(goals)}%")
    return "\n".join(lines)


def morning_message() -> str:
    from goals_config import FIXED_GOALS
    lines = [
        "おはようございます☀️",
        f"今日は{_today_date_str()}です",
        "",
    ]
    for category, items in _group_goals(FIXED_GOALS).items():
        lines.append(f"【{category}】")
        for g in items:
            lines.append(f"{g['symbol']}{g['text']}")
        lines.append("")
    lines += ["今日も当たり前を当たり前に！", "頑張りましょう！"]
    return "\n".join(lines)


def evening_message(goals: list[dict]) -> str:
    lines = [
        "お疲れ様です🌙",
        "今日の達成率を見てみましょう",
        "",
    ]
    for g in goals:
        sym = STATUS_SYMBOL.get(g["status"], "　")
        note = f"({g['note']})" if g.get("note") else ""
        lines.append(f"{g['symbol']}{g['text']} {sym}{note}")
    lines += [
        "",
        f"達成率は{calc_rate(goals)}%でした！",
        "今日もみんなをHAPPYにするために1歩近づけました♪︎",
        "おやすみなさい",
    ]
    return "\n".join(lines)


def weekly_message(week_data: dict) -> str:
    today = date.today()
    lines = ["【今週の達成率まとめ】", ""]
    rates = []
    for day, goals in week_data.items():
        weekday = WEEKDAYS_JA[day.weekday()]
        if day > today:
            lines.append(f"{weekday} ─")
        else:
            rate = calc_rate(goals)
            rates.append(rate)
            lines.append(f"{weekday} {rate}%")
    avg = round(sum(rates) / len(rates)) if rates else 0
    lines += ["", f"平均 {avg}%", "明日からの1週間も頑張りましょう！"]
    return "\n".join(lines)
