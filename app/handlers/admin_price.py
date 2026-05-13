from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from app.config import ADMIN_ID
from app.keyboards import ADMIN_BUTTON_TEXTS, ADMIN_KB, CANCEL_KB
from app.storage import get_payment_info, get_price, set_setting

router = Router()


class ChangePrice(StatesGroup):
    waiting = State()


class ChangePaymentInfo(StatesGroup):
    waiting = State()


CANCEL_TEXT = "❌ Отмена"


@router.message(F.text == "💰 Изменить сумму", F.from_user.id == ADMIN_ID)
async def start_change_price(msg: Message, state: FSMContext):
    await state.set_state(ChangePrice.waiting)
    await msg.answer(
        f"Текущая сумма: <b>{get_price()} ₽</b>\n\n"
        "Отправьте новую сумму (только число, например <code>700</code>).",
        reply_markup=CANCEL_KB,
    )


@router.message(ChangePrice.waiting, F.text == CANCEL_TEXT)
async def cancel_price(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer("Изменение суммы отменено.", reply_markup=ADMIN_KB)


@router.message(ChangePrice.waiting, F.text.in_(ADMIN_BUTTON_TEXTS))
async def abort_price_on_admin_button(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer(
        "Изменение суммы прервано. Нажмите нужную кнопку ещё раз.",
        reply_markup=ADMIN_KB,
    )


@router.message(ChangePrice.waiting, F.text)
async def process_price(msg: Message, state: FSMContext):
    raw = msg.text.strip().replace(" ", "").replace(",", ".")
    try:
        value = float(raw)
        if value < 0:
            raise ValueError
    except ValueError:
        await msg.answer(
            "⚠️ Это не похоже на число. Введите положительную сумму или нажмите «Отмена»."
        )
        return

    formatted = str(int(value)) if value.is_integer() else f"{value:.2f}"
    set_setting("price", formatted)
    await msg.answer(
        f"✅ Сумма обновлена: <b>{formatted} ₽</b>.\n"
        "В следующих напоминаниях участники увидят новую сумму.",
        reply_markup=ADMIN_KB,
    )
    await state.clear()


@router.message(F.text == "💳 Изменить реквизиты", F.from_user.id == ADMIN_ID)
async def start_change_info(msg: Message, state: FSMContext):
    await state.set_state(ChangePaymentInfo.waiting)
    await msg.answer(
        f"Текущие реквизиты: <b>{get_payment_info()}</b>\n\n"
        "Отправьте новые реквизиты одной строкой (карта/телефон/комментарий).",
        reply_markup=CANCEL_KB,
    )


@router.message(ChangePaymentInfo.waiting, F.text == CANCEL_TEXT)
async def cancel_info(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer("Изменение реквизитов отменено.", reply_markup=ADMIN_KB)


@router.message(ChangePaymentInfo.waiting, F.text.in_(ADMIN_BUTTON_TEXTS))
async def abort_info_on_admin_button(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer(
        "Изменение реквизитов прервано. Нажмите нужную кнопку ещё раз.",
        reply_markup=ADMIN_KB,
    )


@router.message(ChangePaymentInfo.waiting, F.text)
async def process_info(msg: Message, state: FSMContext):
    new_info = msg.text.strip()
    if not new_info:
        await msg.answer("⚠️ Пустая строка. Введите реквизиты или нажмите «Отмена».")
        return
    set_setting("payment_info", new_info)
    await msg.answer(
        f"✅ Реквизиты обновлены: <b>{new_info}</b>.",
        reply_markup=ADMIN_KB,
    )
    await state.clear()
