import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand
from config.config import Config
from handlers import commands
from services.db import init_db

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Главная функция для запуска бота"""
    try:
        Config.validate()
    except ValueError as e:
        logger.error(f"Ошибка конфигурации: {e}")
        return

    # Инициализируем БД
    await init_db()
    logger.info("База данных инициализирована")

    bot = Bot(
        token=Config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # --- ИСПРАВЛЕННОЕ МЕНЮ КОМАНД ---
    commands_list = [
        BotCommand(command="start", description="🔄 Главное меню"),
        BotCommand(command="help", description="Помощь"),

        # Поиск
        BotCommand(command="search_film", description="🔎 Поиск по названию"),
        BotCommand(command="genres", description="🎭 Поиск по жанру"),
        BotCommand(command="search_year", description="📅 Поиск по году"),
        BotCommand(command="countries", description="🌍 Поиск по стране"),
        BotCommand(command="search_actor", description="👤 Поиск по актёру"),
        BotCommand(command="search_director", description="🎥 Поиск по режиссёру"),

        # Личное
        BotCommand(command="recommend", description="🎲 Мне повезет (Рекомендация)"),
        BotCommand(command="my_watched", description="👁 Просмотрено"),
        BotCommand(command="my_plan", description="🔖 Буду смотреть"),
        BotCommand(command="save_genres", description="⚙️ Настроить мои вкусы"),
    ]

    await bot.set_my_commands(commands_list)
    logger.info("Меню команд установлено")

    dp.include_router(commands.router)

    logger.info("Бот запущен и готов к работе!")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())