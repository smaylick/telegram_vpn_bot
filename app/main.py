import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import ADMIN_ID, BILLING_DAY, BOT_TOKEN
from app.handlers import build_router
from app.scheduler import setup_scheduler


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
    )


async def main() -> None:
    _configure_logging()

    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not set in env")

    bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(build_router())

    setup_scheduler(bot, BILLING_DAY, ADMIN_ID)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
