from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from app.config import ADMIN_ID
from app.keyboards import ADMIN_BUTTON_TEXTS, ADMIN_KB, CANCEL_KB
from app.storage import add_user, list_members

router = Router()


class AddMember(StatesGroup):
    waiting = State()


CANCEL_TEXT = "❌ Отмена"


@router.message(F.text == "➕ Добавить участника", F.from_user.id == ADMIN_ID)
async def start_add(msg: Message, state: FSMContext):
    await state.set_state(AddMember.waiting)
    await msg.answer(
        "✏️ Отправьте ID и имя участника через пробел.\n"
        "Пример: <code>123456789 Иван</code>\n\n"
        "Чтобы выйти из режима добавления — нажмите «Отмена».",
        reply_markup=CANCEL_KB,
    )


@router.message(AddMember.waiting, F.text == CANCEL_TEXT)
async def cancel_add(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer("Добавление отменено.", reply_markup=ADMIN_KB)


@router.message(AddMember.waiting, F.text.in_(ADMIN_BUTTON_TEXTS))
async def abort_on_admin_button(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer(
        "Режим добавления участника прерван. Нажмите нужную кнопку ещё раз.",
        reply_markup=ADMIN_KB,
    )


@router.message(AddMember.waiting, F.text)
async def process_add(msg: Message, state: FSMContext):
    parts = msg.text.strip().split(maxsplit=1)
    if not parts or not parts[0].isdigit():
        await msg.answer(
            "⚠️ Первый токен должен быть числовым ID. Попробуйте ещё раз "
            "или нажмите «Отмена»."
        )
        return

    uid = int(parts[0])
    name = parts[1].strip() if len(parts) > 1 else f"User {uid}"

    if str(uid) in list_members(ADMIN_ID):
        await msg.answer("Этот пользователь уже есть в списке.", reply_markup=ADMIN_KB)
        await state.clear()
        return

    note = ""
    try:
        chat = await msg.bot.get_chat(uid)
        real_name = chat.full_name or name
        real_username = chat.username
        add_user(uid, real_name, real_username, "member")
        display_name = real_name
        if not real_username:
            note = (
                "\n\nℹ️ Username у пользователя не выставлен. "
                "Когда он поставит @username в Telegram — попроси нажать /start, "
                "и он станет кликабельным в списке."
            )
    except (TelegramBadRequest, TelegramForbiddenError):
        add_user(uid, name, None, "member")
        display_name = name
        note = (
            "\n\n⚠️ Не удалось подтянуть профиль автоматически. "
            "Попроси пользователя нажать /start в боте — тогда он станет "
            "кликабельным в списке участников."
        )

    await msg.answer(
        f"✅ Добавлен участник <b>{display_name}</b> (ID <code>{uid}</code>).{note}",
        reply_markup=ADMIN_KB,
    )
    await state.clear()
