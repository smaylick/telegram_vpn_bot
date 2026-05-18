from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message

from app.keyboards import info_back_kb, info_list_kb
from app.texts import INFO_INTRO, INFO_TEXTS

router = Router()


@router.message(F.text.in_({"📖 Инструкции", "/instructions"}))
async def msg_instructions(msg: Message):
    await msg.answer(INFO_INTRO, reply_markup=info_list_kb(), disable_web_page_preview=True)


@router.callback_query(F.data == "info:list")
async def cb_info_list(call: CallbackQuery):
    try:
        await call.message.edit_text(
            INFO_INTRO, reply_markup=info_list_kb(), disable_web_page_preview=True
        )
    except TelegramBadRequest:
        await call.message.answer(
            INFO_INTRO, reply_markup=info_list_kb(), disable_web_page_preview=True
        )
    await call.answer()


@router.callback_query(F.data.startswith("info:") & ~F.data.in_({"info:list"}))
async def cb_info_show(call: CallbackQuery):
    key = call.data.split(":", 1)[1]
    text = INFO_TEXTS.get(key)
    if text is None:
        await call.answer("Раздел не найден.", show_alert=True)
        return

    kb = info_back_kb()
    try:
        await call.message.edit_text(text, reply_markup=kb, disable_web_page_preview=True)
    except TelegramBadRequest:
        await call.message.answer(text, reply_markup=kb, disable_web_page_preview=True)
    await call.answer()
