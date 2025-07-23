import os, asyncio, logging
from datetime import datetime

from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import (
    Message, CallbackQuery,
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.enums.parse_mode import ParseMode
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv

from app.storage import add_user, set_paid, list_members, unpaid
from app.scheduler import (
    setup_scheduler,
    remind_members,
    admin_summary,
    build_reminder_text,
    build_welcome_text,
    REMINDER_KB
)

# ── конфиг / лог ─────────────────────────────────────────────────────────
load_dotenv(".env")
BOT_TOKEN   = os.getenv("BOT_TOKEN")
ADMIN_ID    = int(os.getenv("ADMIN_ID"))
BILLING_DAY = int(os.getenv("BILLING_DAY", 15))
MAX_MEMBERS = 4    # лимит участников (без учёта админа)

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s: %(message)s")

# ── клавиатуры ───────────────────────────────────────────────────────────
USER_KB = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="ℹ️ Информация")],
        [KeyboardButton(text="💰 Мой статус")],      # ← новая кнопка
        [KeyboardButton(text="🆘 Помощь")]
    ],
    resize_keyboard=True
)

ADMIN_KB = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📢 Напомнить всем")],
        [KeyboardButton(text="👥 Напомнить участнику")],
        [KeyboardButton(text="📊 Статистика")],
        [KeyboardButton(text="ℹ️ Управление")]
    ],
    resize_keyboard=True
)

# ── бот / диспетчер ──────────────────────────────────────────────────────
bot = Bot(
    BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()
router = Router()
dp.include_router(router)

# ── handlers ─────────────────────────────────────────────────────────────
@router.message(F.text == "/start")
async def cmd_start(msg: Message):
    # администратор всегда проходит
    if msg.from_user.id == ADMIN_ID:
        add_user(msg.from_user.id, msg.from_user.full_name, msg.from_user.username, "admin")
        await msg.answer(
            "👋 Привет, <b>администратор</b>!\n"
            "• 📢 Напомнить всем — массовая рассылка\n"
            "• 👥 Напомнить участнику — выбрать любого\n"
            "• 📊 Статистика — кто оплатил / нет\n"
            "• ℹ️ Управление — эта подсказка",
            reply_markup=ADMIN_KB
        )
        return

    # ---- участник ----
    members = list_members(ADMIN_ID)

    # уже зарегистрирован — просто покажем клавиатуру/текст
    if str(msg.from_user.id) in members:
        await msg.answer(build_welcome_text(), reply_markup=USER_KB)
        return

    # проверяем лимит
    if len(members) >= MAX_MEMBERS:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(
                text="Связаться с администратором",
                url=f"tg://user?id={ADMIN_ID}"
            )]]
        )
        await msg.answer(
            "😔 К сожалению, слот свободных подключений исчерпан.\n"
            "Нажмите кнопку ниже, чтобы связаться с администратором.",
            reply_markup=kb
        )
        return

    # место есть — регистрируем
    add_user(msg.from_user.id, msg.from_user.full_name, msg.from_user.username, "member")
    await msg.answer(build_welcome_text(), reply_markup=USER_KB)

# ---------- УЧАСТНИКИ ----------------------------------------------------
@router.message(F.text.in_({"ℹ️ Информация", "/info"}))
async def msg_info(msg: Message):
    await msg.answer(build_welcome_text())

@router.message(F.text.in_({"💰 Мой статус", "/my_status"}))
async def msg_my_status(msg: Message):
    month = datetime.now().strftime("%Y-%m")
    is_paid = msg.from_user.id not in unpaid(month, ADMIN_ID)
    status = "✅ Оплачено" if is_paid else "⏳ Ожидается"
    await msg.answer(f"<b>Статус за {month}</b>: {status}")

@router.message(F.text == "🆘 Помощь")
async def msg_help(msg: Message):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Написать администратору",
                                              url=f"tg://user?id={ADMIN_ID}")]]
    )
    await msg.answer("Если возникли вопросы — напишите администратору:", reply_markup=kb)

# --- участник нажал «Оплачено ✅»
@router.callback_query(F.data == "paid")
async def cb_paid(call: CallbackQuery):
    month = datetime.now().strftime("%Y-%m")
    set_paid(call.from_user.id, month)
    await call.message.edit_text("✅ Спасибо, оплата зафиксирована!")
    if call.from_user.id != ADMIN_ID:
        await bot.send_message(ADMIN_ID,
                               f"{call.from_user.full_name} оплатил VPN за {month}")
    await call.answer()

# --- /paid текстом
@router.message(F.text == "/paid")
async def msg_paid(msg: Message):
    month = datetime.now().strftime("%Y-%m")
    set_paid(msg.from_user.id, month)
    await msg.answer("✅ Спасибо, оплата зафиксирована!")
    if msg.from_user.id != ADMIN_ID:
        await bot.send_message(ADMIN_ID,
                               f"{msg.from_user.full_name} оплатил VPN за {month}")

# ---------- АДМИН --------------------------------------------------------
@router.message(F.text == "📢 Напомнить всем", F.from_user.id == ADMIN_ID)
async def admin_remind_all(msg: Message):
    await remind_members(bot, ADMIN_ID)
    await msg.answer("✅ Напоминание всем отправлено.")

@router.message(F.text == "👥 Напомнить участнику", F.from_user.id == ADMIN_ID)
async def admin_pick_member(msg: Message):
    members = list_members(ADMIN_ID)
    rows = [
        [InlineKeyboardButton(text=info["name"], callback_data=f"forceping:{uid}")]
        for uid, info in members.items()
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=rows)
    await msg.answer("Выберите участника для напоминания:", reply_markup=kb)

@router.callback_query(F.data.startswith("forceping:"))
async def cb_force_ping(call: CallbackQuery):
    target_id = int(call.data.split(":")[1])
    await bot.send_message(target_id, build_reminder_text(), reply_markup=REMINDER_KB)
    await call.answer("Принудительное напоминание отправлено!")

@router.message(F.text == "📊 Статистика", F.from_user.id == ADMIN_ID)
async def admin_stats_button(msg: Message):
    await admin_summary(bot, ADMIN_ID)

@router.message(F.text == "ℹ️ Управление", F.from_user.id == ADMIN_ID)
async def admin_help_button(msg: Message):
    await msg.answer(
        "📋 <b>Команды администратора</b>\n"
        "• 📢 Напомнить всем — массовая рассылка\n"
        "• 👥 Напомнить участнику — выбрать любого\n"
        "• 📊 Статистика — отчёт\n"
        "• /summary, /remind_now — те же действия текстом",
        reply_markup=ADMIN_KB
    )

@router.callback_query(F.data.startswith("ping:"))
async def cb_ping(call: CallbackQuery):
    target_id = int(call.data.split(":")[1])
    await bot.send_message(target_id, build_reminder_text(), reply_markup=REMINDER_KB)
    await call.answer("Напоминание отправлено!")

# текстовые команды admin
@router.message(F.text == "/summary", F.from_user.id == ADMIN_ID)
async def cmd_summary(msg: Message):
    await admin_summary(bot, ADMIN_ID)

@router.message(F.text == "/remind_now", F.from_user.id == ADMIN_ID)
async def cmd_remind_now(msg: Message):
    await remind_members(bot, ADMIN_ID)
    await msg.answer("✅ Напоминание всем отправлено.")

# ── точка входа -----------------------------------------------------------
async def main():
    setup_scheduler(bot, BILLING_DAY, ADMIN_ID)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
