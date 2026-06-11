from datetime import date


def format_goals(goals: list[dict]) -> str:
    if not goals:
        return "（目標なし）"
    return "\n".join(
        f"{'✅' if g['completed'] else '⬜'} {g['index']}. {g['text']}"
        for g in goals
    )


def calc_rate(goals: list[dict]) -> int:
    if not goals:
        return 0
    return round(sum(1 for g in goals if g["completed"]) / len(goals) * 100)


def morning_message(goals: list[dict]) -> str:
    today = date.today().strftime("%m/%d")
    if not goals:
        return (
            f"🌅 おはようございます！{today}\n"
            "今日の目標を登録しましょう。\n\n「追加 [目標]」で追加できます。"
        )
    return f"🌅 おはようございます！{today}の目標\n\n{format_goals(goals)}"


def evening_message(goals: list[dict]) -> str:
    if not goals:
        return ""
    rate = calc_rate(goals)
    msg = f"🌙 本日の達成率: {rate}%\n\n{format_goals(goals)}"
    if rate == 100:
        msg += "\n\n🎊 全目標達成！素晴らしい！"
    return msg


def weekly_message(week_data: dict[str, list[dict]]) -> str:
    if not week_data:
        return ""
    all_goals = [g for goals in week_data.values() for g in goals]
    if not all_goals:
        return ""
    rate = calc_rate(all_goals)
    lines = ["📊 今週の達成サマリー\n"]
    for day_label, goals in week_data.items():
        day_rate = calc_rate(goals)
        done = sum(1 for g in goals if g["completed"])
        lines.append(f"  {day_label}: {day_rate}%（{done}/{len(goals)}）")
    lines.append(f"\n週間達成率: {rate}%")
    if rate == 100:
        lines.append("🏆 完璧な一週間！")
    return "\n".join(lines)
