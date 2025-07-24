import os, asyncio, logging, json, pathlib
from datetime import datetime

from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import (
    Message, CallbackQuery,
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardRemove
)
from aiogram.enums.parse_mode import ParseMode
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv

# модуль storage используем как источник пути к state.json
from app import storage
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
        [KeyboardButton(text="💰 Мой статус")],
        [KeyboardButton(text="🆘 Помощь")]
    ],
    resize_keyboard=True
)

ADMIN_KB = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📢 Напомнить всем")],
        [KeyboardButton(text="👥 Напомнить участнику")],
        [KeyboardButton(text="📋 Участники")],
        [KeyboardButton(text="🗑 Удалить участника")],
        [KeyboardButton(text="✅ Отметить оплату")],
        [KeyboardButton(text="📊 Статистика")],
        [KeyboardButton(text="ℹ️ Управление")]
    ],
    resize_keyboard=True
)

# ── helper: удаление из state.json ───────────────────────────────────────
def _remove_user(chat_id: int):
    """Убираем пользователя из users и всех payments"""
    with storage.DATA_PATH.open() as f:
        data = json.load(f)
    uid = str(chat_id)
    data["users"].pop(uid, None)
    for month in data["payments"]:
        data["payments"][month].pop(uid, None)
    with storage.DATA_PATH.open("w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

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
    # администратор …
    if msg.from_user.id == ADMIN_ID:
        add_user(msg.from_user.id, msg.from_user.full_name, msg.from_user.username, "admin")
        await msg.answer(
            "👋 Привет, <b>администратор</b>!\n"
            "• 📢 Напомнить всем — массовая рассылка\n"
            "• 👥 Напомнить участнику — выбрать любого\n"
            "• 📋 / 🗑  — список / удаление\n"
            "• 📊 Статистика — кто оплатил / нет",
            reply_markup=ADMIN_KB
        )
        return

    # ---- участник ----
    members = list_members(ADMIN_ID)
    if str(msg.from_user.id) in members:
        await msg.answer(build_welcome_text(), reply_markup=USER_KB)
        return

    if len(members) >= MAX_MEMBERS:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(
                text="Связаться с администратором",
                url=f"tg://user?id={ADMIN_ID}"
            )]]
        )
        await msg.answer(
            "😔 Свободных слотов нет. Напишите администратору.",
            reply_markup=kb
        )
        return

    await msg.answer("🔄 Заявка на подключение отправлена администратору. Ожидайте решения.")

    kb_admin = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="✅ Принять", callback_data=f"join_ok:{msg.from_user.id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"join_no:{msg.from_user.id}")
        ]]
    )
    await bot.send_message(
        ADMIN_ID,
        f"⚠️ Запрос на подключение от "
        f"<a href='tg://user?id={msg.from_user.id}'>{msg.from_user.full_name}</a>",
        reply_markup=kb_admin
    )

# ---------- УЧАСТНИКИ ----------------------------------------------------
@router.message(F.text.in_({"ℹ️ Информация", "/info"}))
async def msg_info(msg: Message):
    await msg.answer(build_welcome_text())

@router.message(F.text.in_({"💰 Мой статус", "/my_status"}))
async def msg_my_status(msg: Message):
    month = datetime.now().strftime("%Y-%m")
    status = "✅ Оплачено" if msg.from_user.id not in unpaid(month, ADMIN_ID) else "⏳ Ожидается"
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
    await msg.answer("Выберите участника для напоминания:",
                     reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))

@router.message(F.text == "📋 Участники", F.from_user.id == ADMIN_ID)
async def admin_list_members(msg: Message):
    rows = [
        [InlineKeyboardButton(text=info["name"], url=f"tg://user?id={uid}")]
        for uid, info in list_members(ADMIN_ID).items()
    ] or [[InlineKeyboardButton(text="(пусто)", callback_data="noop")]]
    await msg.answer("Все участники:",
                     reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))

# --- удалить участника ---------------------------------------------------
@router.message(F.text == "🗑 Удалить участника", F.from_user.id == ADMIN_ID)
async def admin_delete_member_pick(msg: Message):
    members = list_members(ADMIN_ID)
    rows = [
        [InlineKeyboardButton(text=f"❌ {info['name']}", callback_data=f"delask:{uid}")]
        for uid, info in members.items()
    ] or [[InlineKeyboardButton(text="(пусто)", callback_data="noop")]]
    await msg.answer("Кого удалить?", reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))

@router.callback_query(F.data.startswith("delask:"))
async def cb_del_confirm(call: CallbackQuery):
    uid = call.data.split(":")[1]
    info = list_members(ADMIN_ID).get(uid)
    if not info:
        await call.answer("Участник уже удалён.", show_alert=True)
        return
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Да", callback_data=f"delyes:{uid}"),
                InlineKeyboardButton(text="❌ Нет", callback_data="delno")
            ]
        ]
    )
    await call.message.edit_text(
        f"Удалить <b>{info['name']}</b> из списка участников?",
        reply_markup=kb
    )
    await call.answer()

@router.callback_query(F.data.startswith("delyes:"))
async def cb_del_yes(call: CallbackQuery):
    uid = int(call.data.split(":")[1])
    _remove_user(uid)
    await call.message.edit_text("🗑 Участник удалён.")
    # убираем клавиатуру у пользователя
    try:
        await bot.send_message(
            uid,
            "⛔️ Ваш доступ к VPN отключён администратором.\nНажмите /start, чтобы запросить подключение снова.",
            reply_markup=ReplyKeyboardRemove()
        )
    except Exception:
        pass
    await call.answer()


@router.callback_query(F.data == "delno")
async def cb_del_no(call: CallbackQuery):
    await call.message.edit_text("Удаление отменено.")
    await call.answer()

# ---------- вручную отметить оплату -------------------------------------
@router.message(F.text == "✅ Отметить оплату", F.from_user.id == ADMIN_ID)
async def admin_mark_paid_pick(msg: Message):
    month   = datetime.now().strftime("%Y-%m")
    debtors = unpaid(month, ADMIN_ID)

    if not debtors:
        await msg.answer("🎉 Все участники уже отмечены как оплатившие.")
        return

    rows = [
        [InlineKeyboardButton(
            text=list_members(ADMIN_ID)[str(uid)]["name"],
            callback_data=f"markpaid:{uid}"
        )] for uid in debtors
    ]
    await msg.answer(
        f"Кто уже оплатил за {month}?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows)
    )


@router.callback_query(F.data.startswith("markpaid:"))
async def cb_mark_paid(call: CallbackQuery):
    uid   = int(call.data.split(":")[1])
    month = datetime.now().strftime("%Y-%m")
    set_paid(uid, month)

    await call.message.edit_text("✅ Оплата отмечена.")
    await bot.send_message(
        uid,
        f"✅ Администратор отметил вашу оплату за {month}. Спасибо!"
    )
    await call.answer("Отметил как оплачено.")

# -------- согласие / отказ админа на подключение --------
@router.callback_query(F.data.startswith("join_ok:"))
async def cb_join_ok(call: CallbackQuery):
    uid = int(call.data.split(":")[1])

    if str(uid) in list_members(ADMIN_ID):           # уже добавлен
        await call.answer("Уже в списке.", show_alert=True)
        return

    chat = await bot.get_chat(uid)                   # имя/ник для storage
    add_user(uid, chat.full_name, chat.username, "member")

    await bot.send_message(uid, build_welcome_text(), reply_markup=USER_KB)
    await call.message.edit_text("✅ Участник добавлен.")
    await call.answer()

@router.callback_query(F.data.startswith("join_no:"))
async def cb_join_no(call: CallbackQuery):
    uid = int(call.data.split(":")[1])

    kb_no = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="Написать админу", url=f"tg://user?id={ADMIN_ID}")
        ]]
    )

    await bot.send_message(
        uid,
        "❌ Администратор отклонил заявку на подключение.\n"
        "Свяжитесь с ним для уточнения.",
        reply_markup=kb_no
    )
    await call.message.edit_text("🚫 Заявка отклонена.")
    await call.answer()

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
        "• 📢 Напомнить всем\n"
        "• 👥 Напомнить участнику\n"
        "• 📋 Участники — открыть чат\n"
        "• 🗑 Удалить участника\n"
        "• ✅ Отметить оплату — вручную отметить платеж\n"
        "• 📊 Статистика",
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