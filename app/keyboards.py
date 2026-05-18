from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

USER_KB = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="ℹ️ Информация")],
        [KeyboardButton(text="📖 Инструкции")],
        [KeyboardButton(text="💰 Мой статус")],
        [KeyboardButton(text="🆘 Помощь")],
    ],
    resize_keyboard=True,
)

ADMIN_KB = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📢 Напомнить всем")],
        [KeyboardButton(text="👥 Напомнить участнику")],
        [KeyboardButton(text="📣 Объявление")],
        [KeyboardButton(text="✉️ Написать участнику")],
        [KeyboardButton(text="📋 Участники")],
        [KeyboardButton(text="🗑 Удалить участника")],
        [KeyboardButton(text="➕ Добавить участника")],
        [KeyboardButton(text="✅ Отметить оплату")],
        [KeyboardButton(text="💰 Изменить сумму")],
        [KeyboardButton(text="💳 Изменить реквизиты")],
        [KeyboardButton(text="📖 Инструкции")],
        [KeyboardButton(text="📊 Статистика")],
        [KeyboardButton(text="ℹ️ Управление")],
    ],
    resize_keyboard=True,
)

CANCEL_KB = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="❌ Отмена")]],
    resize_keyboard=True,
)

ADMIN_BUTTON_TEXTS: frozenset[str] = frozenset(
    btn.text for row in ADMIN_KB.keyboard for btn in row
)

REMINDER_KB = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text="Оплачено ✅", callback_data="paid")]]
)


def info_list_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🟣 AmneziaVPN • WireGuard", callback_data="info:wg")],
            [InlineKeyboardButton(text="🟣 AmneziaVPN • X-Ray", callback_data="info:amnezia")],
            [InlineKeyboardButton(text="🔵 3X-UI • VLESS напрямую ⭐", callback_data="info:xray_direct")],
            [InlineKeyboardButton(text="🔵 3X-UI • VLESS двойной хоп", callback_data="info:xray")],
        ]
    )


def info_back_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="← Назад к списку", callback_data="info:list")]]
    )
