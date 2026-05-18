import html

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from app.config import ADMIN_ID
from app.keyboards import ADMIN_BUTTON_TEXTS, ADMIN_KB, CANCEL_KB
from app.storage import list_members

router = Router()


class DirectMessage(StatesGroup):
    waiting_text = State()


def _members_kb() -> InlineKeyboardMarkup:
    members = list_members(ADMIN_ID)
    rows = [
        [InlineKeyboardButton(text=info["name"], callback_data=f"dm_pick:{uid}")]
        for uid, info in members.items()
    ] or [[InlineKeyboardButton(text="(пусто)", callback_data="noop")]]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _confirm_kb(uid: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Отправить", callback_data=f"dm_send:{uid}"),
                InlineKeyboardButton(text="❌ Отмена", callback_data="dm_cancel"),
            ]
        ]
    )


@router.message(F.text == "✉️ Написать участнику", F.from_user.id == ADMIN_ID)
async def start_dm(msg: Message, state: FSMContext):
    await msg.answer("Кому написать?", reply_markup=_members_kb())


@router.callback_query(F.data.startswith("dm_pick:"))
async def cb_dm_pick(call: CallbackQuery, state: FSMContext):
    uid = int(call.data.split(":")[1])
    members = list_members(ADMIN_ID)
    info = members.get(str(uid))
    if not info:
        await call.answer("Участник не найден.", show_alert=True)
        return

    await state.set_state(DirectMessage.waiting_text)
    await state.update_data(target_uid=uid, target_name=info["name"])
    await call.message.edit_text(
        f"✏️ Введи сообщение для <b>{info['name']}</b>.\n\n"
        "Поддерживается HTML и обычный текст. Можно вставить vpn:// ключ — он придёт как обычный текст для копирования.",
        reply_markup=None,
    )
    await call.message.answer("Или нажми «Отмена»:", reply_markup=CANCEL_KB)
    await call.answer()


@router.message(DirectMessage.waiting_text, F.text == "❌ Отмена")
async def cancel_dm(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer("Отменено.", reply_markup=ADMIN_KB)


@router.message(DirectMessage.waiting_text, F.text.in_(ADMIN_BUTTON_TEXTS))
async def abort_dm_on_admin_button(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer("Отправка прервана. Нажми нужную кнопку ещё раз.", reply_markup=ADMIN_KB)


@router.message(DirectMessage.waiting_text, F.text)
async def receive_dm_text(msg: Message, state: FSMContext):
    text = msg.text.strip()
    if not text:
        await msg.answer("⚠️ Пустое сообщение. Введи текст или нажми «Отмена».")
        return

    data = await state.get_data()
    uid: int = data["target_uid"]
    name: str = data["target_name"]

    try:
        await msg.bot.send_message(
            ADMIN_ID,
            f"👇 <b>Превью для {name}:</b>\n\n" + text,
        )
    except TelegramBadRequest as exc:
        await msg.answer(
            "⚠️ Ошибка HTML-парсинга:\n"
            f"<code>{html.escape(str(exc))}</code>\n\n"
            "Исправь теги или нажми «Отмена»."
        )
        return

    await state.update_data(text=text)
    await state.set_state(DirectMessage.waiting_text)
    await msg.answer(
        f"Отправить это сообщение участнику <b>{name}</b>?",
        reply_markup=_confirm_kb(uid),
    )


@router.callback_query(F.data == "dm_cancel")
async def cb_dm_cancel(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("🚫 Отправка отменена.")
    await call.message.answer("Готов к новым командам.", reply_markup=ADMIN_KB)
    await call.answer()


@router.callback_query(F.data.startswith("dm_send:"))
async def cb_dm_send(call: CallbackQuery, state: FSMContext):
    uid = int(call.data.split(":")[1])
    data = await state.get_data()
    text: str | None = data.get("text")
    name: str = data.get("target_name", str(uid))

    if not text:
        await state.clear()
        await call.answer("Текст потерян, начни заново.", show_alert=True)
        return

    try:
        await call.bot.send_message(uid, text)
        await state.clear()
        await call.message.edit_text(f"✅ Сообщение отправлено участнику <b>{name}</b>.")
        await call.message.answer("Готов к новым командам.", reply_markup=ADMIN_KB)
    except TelegramForbiddenError:
        await state.clear()
        await call.message.edit_text(f"❌ Не доставлено: {name} заблокировал бота.")
        await call.message.answer("Готов к новым командам.", reply_markup=ADMIN_KB)
    except TelegramBadRequest as exc:
        await state.clear()
        await call.message.edit_text(f"❌ Ошибка доставки: <code>{html.escape(exc.message)}</code>")
        await call.message.answer("Готов к новым командам.", reply_markup=ADMIN_KB)

    await call.answer()
