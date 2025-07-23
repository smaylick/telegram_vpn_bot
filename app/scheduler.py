import os
from datetime import datetime

from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from app.storage import unpaid, list_members

load_dotenv(".env")
PRICE        = os.getenv("PRICE", "0")
PAYMENT_INFO = os.getenv("PAYMENT_INFO", "—")

REMINDER_KB = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text="Оплачено ✅", callback_data="paid")]]
)

def build_reminder_text() -> str:
    return (
        "👋 <b>Напоминание об оплате VPN</b>\n"
        f"Сумма: <b>{PRICE} ₽</b>\n"
        f"Перевести: <b>{PAYMENT_INFO}</b>\n\n"
        "После перевода нажмите кнопку ↓"
    )

def build_welcome_text() -> str:
    return (
        "👋 <b>Вы подключились к нашему VPN-серверу</b>\n\n"
        "• Оплата <b>каждый месяц 23-го числа</b>\n"
        f"• Сумма: <b>{PRICE} ₽</b>\n"
        f"• Перевести: <b>{PAYMENT_INFO}</b>\n\n"
        "После перевода нажмите кнопку <b>«Оплачено ✅»</b> в напоминании."
    )

async def remind_members(bot: Bot, admin_id: int):
    month = datetime.now().strftime("%Y-%m")
    for uid in unpaid(month, admin_id):
        await bot.send_message(uid, build_reminder_text(), reply_markup=REMINDER_KB)

async def admin_summary(bot: Bot, admin_id: int):
    month    = datetime.now().strftime("%Y-%m")
    debtors  = unpaid(month, admin_id)
    members  = list_members(admin_id)
    paid_cnt = len(members) - len(debtors)

    bar = "▓" * paid_cnt + "░" * len(debtors)
    rows = [[InlineKeyboardButton(
                text=f"Пнуть 🚀 {members[str(uid)]['name']}",
                callback_data=f"ping:{uid}")
            ] for uid in debtors]

    kb = InlineKeyboardMarkup(inline_keyboard=rows) if rows else None

    await bot.send_message(
        admin_id,
        f"<b>Отчёт об оплате за {month}</b>\n"
        f"{bar}  {paid_cnt}/{len(members)} участников оплатили.",
        reply_markup=kb
    )

def setup_scheduler(bot: Bot, billing_day: int, admin_id: int):
    sched = AsyncIOScheduler(timezone="Europe/Moscow")
    sched.add_job(remind_members, "cron",
                  day=billing_day, hour=12, minute=0,
                  args=[bot, admin_id], id="members_reminder")
    sched.add_job(admin_summary, "cron",
                  day=billing_day, hour=21, minute=0,
                  args=[bot, admin_id], id="admin_report")
    sched.start()
