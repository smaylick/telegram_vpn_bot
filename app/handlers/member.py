from datetime import datetime

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.config import ADMIN_ID
from app.storage import set_paid, unpaid
from app.texts import build_welcome_text

router = Router()


@router.message(F.text.in_({"ℹ️ Информация", "/info"}))
async def msg_info(msg: Message):
    await msg.answer(build_welcome_text())


@router.message(F.text.in_({"💰 Мой статус", "/my_status"}))
async def msg_my_status(msg: Message):
    month = datetime.now().strftime("%Y-%m")
    debtors = unpaid(month, ADMIN_ID)
    status = "✅ Оплачено" if msg.from_user.id not in debtors else "⏳ Ожидается"
    await msg.answer(f"<b>Статус за {month}</b>: {status}")


@router.message(F.text == "🆘 Помощь")
async def msg_help(msg: Message):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Написать администратору", url=f"tg://user?id={ADMIN_ID}")]
        ]
    )
    await msg.answer("Если возникли вопросы — напишите администратору:", reply_markup=kb)


@router.callback_query(F.data == "paid")
async def cb_paid(call: CallbackQuery):
    month = datetime.now().strftime("%Y-%m")
    set_paid(call.from_user.id, month)
    await call.message.edit_text("✅ Спасибо, оплата зафиксирована!")
    if call.from_user.id != ADMIN_ID:
        await call.bot.send_message(
            ADMIN_ID, f"{call.from_user.full_name} оплатил VPN за {month}"
        )
    await call.answer()


@router.message(F.text == "/paid")
async def msg_paid(msg: Message):
    month = datetime.now().strftime("%Y-%m")
    set_paid(msg.from_user.id, month)
    await msg.answer("✅ Спасибо, оплата зафиксирована!")
    if msg.from_user.id != ADMIN_ID:
        await msg.bot.send_message(
            ADMIN_ID, f"{msg.from_user.full_name} оплатил VPN за {month}"
        )
