from datetime import datetime

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    ReplyKeyboardRemove,
)

from app.config import ADMIN_ID
from app.handlers.common import ADMIN_HELP_TEXT
from app.keyboards import ADMIN_KB, REMINDER_KB
from app.scheduler import admin_summary, remind_members
from app.storage import list_members, remove_user, set_paid, unpaid
from app.texts import build_reminder_text

router = Router()


def _is_admin(msg: Message) -> bool:
    return msg.from_user.id == ADMIN_ID


@router.message(F.text == "📢 Напомнить всем", F.from_user.id == ADMIN_ID)
async def admin_remind_all(msg: Message):
    await remind_members(msg.bot, ADMIN_ID)
    await msg.answer("✅ Напоминание всем отправлено.")


@router.message(F.text == "👥 Напомнить участнику", F.from_user.id == ADMIN_ID)
async def admin_pick_member(msg: Message):
    members = list_members(ADMIN_ID)
    rows = [
        [InlineKeyboardButton(text=info["name"], callback_data=f"forceping:{uid}")]
        for uid, info in members.items()
    ] or [[InlineKeyboardButton(text="(пусто)", callback_data="noop")]]
    await msg.answer(
        "Выберите участника для напоминания:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
    )


@router.message(F.text == "📋 Участники", F.from_user.id == ADMIN_ID)
async def admin_list_members(msg: Message):
    members = list_members(ADMIN_ID)
    if not members:
        await msg.answer("Участников пока нет.")
        return

    no_username_lines: list[str] = []
    kb_rows: list[list[InlineKeyboardButton]] = []

    for uid, info in members.items():
        name = info["name"]
        username = info.get("username")
        if username:
            kb_rows.append([InlineKeyboardButton(text=name, url=f"https://t.me/{username}")])
        else:
            no_username_lines.append(
                f"• <b>{name}</b> (ID <code>{uid}</code>) — <i>нет @username, попроси нажать /start</i>"
            )

    text_parts = ["<b>Все участники:</b>"]
    if no_username_lines:
        text_parts.append("")
        text_parts.extend(no_username_lines)
    if kb_rows:
        text_parts.append("")
        text_parts.append("↓ Открыть чат:")
    text = "\n".join(text_parts)

    kb = InlineKeyboardMarkup(inline_keyboard=kb_rows) if kb_rows else None
    await msg.answer(text, reply_markup=kb, disable_web_page_preview=True)


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
                InlineKeyboardButton(text="❌ Нет", callback_data="delno"),
            ]
        ]
    )
    await call.message.edit_text(
        f"Удалить <b>{info['name']}</b> из списка участников?", reply_markup=kb
    )
    await call.answer()


@router.callback_query(F.data.startswith("delyes:"))
async def cb_del_yes(call: CallbackQuery):
    uid = int(call.data.split(":")[1])
    remove_user(uid)
    await call.message.edit_text("🗑 Участник удалён.")
    try:
        await call.bot.send_message(
            uid,
            "⛔️ Ваш доступ к VPN отключён администратором.\n"
            "Нажмите /start, чтобы запросить подключение снова.",
            reply_markup=ReplyKeyboardRemove(),
        )
    except TelegramBadRequest:
        pass
    await call.answer()


@router.callback_query(F.data == "delno")
async def cb_del_no(call: CallbackQuery):
    await call.message.edit_text("Удаление отменено.")
    await call.answer()


@router.message(F.text == "✅ Отметить оплату", F.from_user.id == ADMIN_ID)
async def admin_mark_paid_pick(msg: Message):
    month = datetime.now().strftime("%Y-%m")
    debtors = unpaid(month, ADMIN_ID)

    if not debtors:
        await msg.answer("🎉 Все участники уже отмечены как оплатившие.")
        return

    members = list_members(ADMIN_ID)
    rows = [
        [InlineKeyboardButton(text=members[str(uid)]["name"], callback_data=f"markpaid:{uid}")]
        for uid in debtors
    ]
    await msg.answer(
        f"Кто уже оплатил за {month}?", reply_markup=InlineKeyboardMarkup(inline_keyboard=rows)
    )


@router.callback_query(F.data.startswith("markpaid:"))
async def cb_mark_paid(call: CallbackQuery):
    uid = int(call.data.split(":")[1])
    month = datetime.now().strftime("%Y-%m")
    set_paid(uid, month)

    await call.message.edit_text("✅ Оплата отмечена.")
    await call.answer("Отметил как оплачено.")


@router.callback_query(F.data.startswith("forceping:"))
async def cb_force_ping(call: CallbackQuery):
    target_id = int(call.data.split(":")[1])
    try:
        await call.bot.send_message(target_id, build_reminder_text(), reply_markup=REMINDER_KB)
        await call.answer("Принудительное напоминание отправлено!")
    except TelegramBadRequest:
        await call.answer(
            "❌ Не удалось отправить: пользователь не открывал чат с ботом.", show_alert=True
        )


@router.callback_query(F.data.startswith("ping:"))
async def cb_ping(call: CallbackQuery):
    target_id = int(call.data.split(":")[1])
    try:
        await call.bot.send_message(target_id, build_reminder_text(), reply_markup=REMINDER_KB)
        await call.answer("Напоминание отправлено!")
    except TelegramBadRequest:
        await call.answer(
            "❌ Не удалось отправить: пользователь не открывал чат с ботом.", show_alert=True
        )


@router.message(F.text == "📊 Статистика", F.from_user.id == ADMIN_ID)
async def admin_stats_button(msg: Message):
    await admin_summary(msg.bot, ADMIN_ID)


@router.message(F.text == "ℹ️ Управление", F.from_user.id == ADMIN_ID)
async def admin_help_button(msg: Message):
    await msg.answer(ADMIN_HELP_TEXT, reply_markup=ADMIN_KB)


@router.message(F.text == "/summary", F.from_user.id == ADMIN_ID)
async def cmd_summary(msg: Message):
    await admin_summary(msg.bot, ADMIN_ID)


@router.message(F.text == "/remind_now", F.from_user.id == ADMIN_ID)
async def cmd_remind_now(msg: Message):
    await remind_members(msg.bot, ADMIN_ID)
    await msg.answer("✅ Напоминание всем отправлено.")
