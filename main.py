import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.types import BotCommand
from config.config import Config
from handlers import commands

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)



async def main():
    """Главная функция для запуска бота"""
    # Проверяем конфигурацию
    try:
        Config.validate()
    except ValueError as e:
        logger.error(f"Ошибка конфигурации: {e}")
        return
    
    # Инициализируем бота и диспетчер
    bot = Bot(token=Config.BOT_TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher()
    
    # Настраиваем меню команд
    commands_list = [
        BotCommand(command="start", description="Начать работу с ботом"),
        BotCommand(command="help", description="Справка по использованию"),
        BotCommand(command="genres", description="Получить список жанров"),
        BotCommand(command="search", description="Поиск фильмов по жанру"),
        BotCommand(command="search_genres", description="Поиск по нескольким жанрам"),
        BotCommand(command="search_year", description="Поиск фильмов по году"),
        BotCommand(command="search_actor", description="Поиск фильмов по актёру"),
        BotCommand(command="search_director", description="Поиск фильмов по режиссёру"),
    ]
    await bot.set_my_commands(commands_list)
    logger.info("Меню команд установлено")
    
    # Регистрируем роутеры
    dp.include_router(commands.router)
    
    logger.info("Бот запущен и готов к работе!")
    
    # Запускаем polling
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())

