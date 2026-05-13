from datetime import datetime

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.keyboards import REMINDER_KB
from app.storage import list_members, unpaid
from app.texts import build_reminder_text


async def remind_members(bot: Bot, admin_id: int) -> None:
    month = datetime.now().strftime("%Y-%m")
    for uid in unpaid(month, admin_id):
        try:
            await bot.send_message(uid, build_reminder_text(), reply_markup=REMINDER_KB)
        except TelegramBadRequest:
            continue


async def admin_summary(bot: Bot, admin_id: int) -> None:
    month = datetime.now().strftime("%Y-%m")
    debtors = unpaid(month, admin_id)
    members = list_members(admin_id)
    paid_cnt = len(members) - len(debtors)

    bar = "▓" * paid_cnt + "░" * len(debtors)
    rows = [
        [
            InlineKeyboardButton(
                text=f"Пнуть 🚀 {members[str(uid)]['name']}",
                callback_data=f"ping:{uid}",
            )
        ]
        for uid in debtors
    ]

    kb = InlineKeyboardMarkup(inline_keyboard=rows) if rows else None

    await bot.send_message(
        admin_id,
        f"<b>Отчёт об оплате за {month}</b>\n"
        f"{bar}  {paid_cnt}/{len(members)} участников оплатили.",
        reply_markup=kb,
    )


def setup_scheduler(bot: Bot, billing_day: int, admin_id: int) -> None:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler

    sched = AsyncIOScheduler(timezone="Europe/Moscow")
    sched.add_job(
        remind_members,
        "cron",
        day=billing_day,
        hour=12,
        minute=0,
        args=[bot, admin_id],
        id="members_reminder",
    )
    sched.add_job(
        admin_summary,
        "cron",
        day=billing_day,
        hour=21,
        minute=0,
        args=[bot, admin_id],
        id="admin_report",
    )
    sched.start()
