import asyncio
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


class Broadcast(StatesGroup):
    waiting_text = State()
    waiting_confirm = State()


CANCEL_TEXT = "❌ Отмена"


def _confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Отправить всем", callback_data="broadcast:send"),
                InlineKeyboardButton(text="❌ Отмена", callback_data="broadcast:cancel"),
            ]
        ]
    )


@router.message(F.text == "📣 Объявление", F.from_user.id == ADMIN_ID)
async def start_broadcast(msg: Message, state: FSMContext):
    await state.set_state(Broadcast.waiting_text)
    await msg.answer(
        "✏️ Введи текст объявления, который получат все участники.\n\n"
        "Можно использовать HTML-теги: <code>&lt;b&gt;</code>, <code>&lt;i&gt;</code>, "
        "<code>&lt;u&gt;</code>, <code>&lt;a href='...'&gt;</code>, <code>&lt;code&gt;</code>.",
        reply_markup=CANCEL_KB,
    )


@router.message(Broadcast.waiting_text, F.text == CANCEL_TEXT)
async def cancel_broadcast_text(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer("Рассылка отменена.", reply_markup=ADMIN_KB)


@router.message(Broadcast.waiting_text, F.text.in_(ADMIN_BUTTON_TEXTS))
async def abort_broadcast_on_admin_button(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer(
        "Рассылка прервана. Нажми нужную кнопку ещё раз.",
        reply_markup=ADMIN_KB,
    )


@router.message(Broadcast.waiting_text, F.text)
async def receive_broadcast_text(msg: Message, state: FSMContext):
    text = msg.text.strip()
    if not text:
        await msg.answer("⚠️ Пустое сообщение. Введи текст или нажми «Отмена».")
        return

    try:
        await msg.bot.send_message(
            ADMIN_ID,
            "👇 <b>Превью объявления:</b>\n\n" + text,
        )
    except TelegramBadRequest as exc:
        await msg.answer(
            "⚠️ Не удалось распарсить сообщение — скорее всего, кривой HTML.\n"
            f"<code>{html.escape(str(exc))}</code>\n\n"
            "Попробуй ещё раз или нажми «Отмена»."
        )
        return

    await state.update_data(text=text)
    await state.set_state(Broadcast.waiting_confirm)
    await msg.answer(
        "Отправить это объявление всем участникам?",
        reply_markup=_confirm_kb(),
    )


@router.callback_query(Broadcast.waiting_confirm, F.data == "broadcast:cancel")
async def cb_broadcast_cancel(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("🚫 Рассылка отменена.")
    await call.message.answer("Готов к новым командам.", reply_markup=ADMIN_KB)
    await call.answer()


@router.callback_query(Broadcast.waiting_confirm, F.data == "broadcast:send")
async def cb_broadcast_send(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    text: str | None = data.get("text")
    if not text:
        await state.clear()
        await call.answer("Текст рассылки потерян, начни заново.", show_alert=True)
        return

    members = list_members(ADMIN_ID)
    sent = 0
    failed: list[str] = []

    for uid, info in members.items():
        try:
            await call.bot.send_message(int(uid), text)
            sent += 1
        except TelegramForbiddenError:
            failed.append(f"{info['name']} (заблокировал бота)")
        except TelegramBadRequest as exc:
            failed.append(f"{info['name']} ({exc.message})")
        await asyncio.sleep(0.05)  # лёгкий троттлинг, чтобы не упереться в лимиты

    await state.clear()
    await call.message.edit_text("✅ Рассылка завершена.")

    report = [f"📨 Отправлено: <b>{sent}</b> из <b>{len(members)}</b>."]
    if failed:
        report.append("")
        report.append("Не доставлено:")
        report.extend(f"• {item}" for item in failed)
    await call.message.answer("\n".join(report), reply_markup=ADMIN_KB)
    await call.answer()
