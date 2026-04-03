import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from config import BOT_TOKEN
from database import init_db
from handlers import start, survey, admin

logging.basicConfig(level=logging.INFO)


async def main():
    await init_db()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(start.router)
    dp.include_router(admin.router)
    dp.include_router(survey.router)

    await bot.set_my_commands([
        BotCommand(command="start", description="Подать заявку"),
        BotCommand(command="db_add", description="Добавить вручную (админ)"),
        BotCommand(command="db", description="Просмотр базы (админ)"),
        BotCommand(command="db_delete", description="Удалить из базы (админ)"),
        BotCommand(command="db_search", description="Поиск по базе (админ)"),
        BotCommand(command="message_all", description="Рассылка всем (админ)"),
    ])

    logging.info("Бот запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
