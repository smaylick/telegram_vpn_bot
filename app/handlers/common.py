from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.config import ADMIN_ID
from app.keyboards import ADMIN_KB, USER_KB
from app.storage import add_user, list_members, update_user_contact
from app.texts import build_welcome_text

router = Router()


ADMIN_HELP_TEXT = (
    "📋 <b>Команды администратора</b>\n"
    "• 📢 Напомнить всем\n"
    "• 👥 Напомнить участнику\n"
    "• 📣 Объявление — разослать сообщение всем участникам\n"
    "• 📋 Участники — открыть чат\n"
    "• 🗑 Удалить участника\n"
    "• ➕ Добавить участника\n"
    "• ✅ Отметить оплату — вручную отметить платеж\n"
    "• 💰 Изменить сумму — поменять сумму в напоминании\n"
    "• 💳 Изменить реквизиты — поменять реквизиты для перевода\n"
    "• 📖 Инструкции — описания протоколов и подключения\n"
    "• 📊 Статистика"
)


@router.message(F.text == "/start")
async def cmd_start(msg: Message):
    if msg.from_user.id == ADMIN_ID:
        add_user(msg.from_user.id, msg.from_user.full_name, msg.from_user.username, "admin")
        await msg.answer(
            "👋 Привет, <b>администратор</b>!\n\n" + ADMIN_HELP_TEXT,
            reply_markup=ADMIN_KB,
        )
        return

    members = list_members(ADMIN_ID)
    if str(msg.from_user.id) in members:
        update_user_contact(
            msg.from_user.id, msg.from_user.full_name, msg.from_user.username
        )
        await msg.answer(build_welcome_text(), reply_markup=USER_KB)
        return

    await msg.answer("🔄 Заявка на подключение отправлена администратору. Ожидайте решения.")

    kb_admin = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Принять", callback_data=f"join_ok:{msg.from_user.id}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"join_no:{msg.from_user.id}"),
            ]
        ]
    )
    await msg.bot.send_message(
        ADMIN_ID,
        "⚠️ Запрос на подключение от "
        f"<a href='tg://user?id={msg.from_user.id}'>{msg.from_user.full_name}</a>",
        reply_markup=kb_admin,
    )


@router.callback_query(F.data.startswith("join_ok:"))
async def cb_join_ok(call: CallbackQuery):
    uid = int(call.data.split(":")[1])

    if str(uid) in list_members(ADMIN_ID):
        await call.answer("Уже в списке.", show_alert=True)
        return

    chat = await call.bot.get_chat(uid)
    add_user(uid, chat.full_name, chat.username, "member")

    await call.bot.send_message(uid, build_welcome_text(), reply_markup=USER_KB)
    await call.message.edit_text("✅ Участник добавлен.")
    await call.answer()


@router.callback_query(F.data.startswith("join_no:"))
async def cb_join_no(call: CallbackQuery):
    uid = int(call.data.split(":")[1])

    kb_no = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Написать админу", url=f"tg://user?id={ADMIN_ID}")]]
    )

    await call.bot.send_message(
        uid,
        "❌ Администратор отклонил заявку на подключение.\nСвяжитесь с ним для уточнения.",
        reply_markup=kb_no,
    )
    await call.message.edit_text("🚫 Заявка отклонена.")
    await call.answer()


@router.callback_query(F.data == "noop")
async def cb_noop(call: CallbackQuery):
    await call.answer()
