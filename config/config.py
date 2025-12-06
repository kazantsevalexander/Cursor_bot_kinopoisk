import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()


class Config:
    """Класс для хранения конфигурации бота"""
    
    # Telegram Bot Token
    BOT_TOKEN: str = os.getenv('BOT_TOKEN', '')
    
    # Kinopoisk API Key
    KINOPOISK_API_KEY: str = os.getenv('KINOPOISK_API_KEY', '')
    
    # Kinopoisk API Base URL
    KINOPOISK_API_URL: str = 'https://kinopoiskapiunofficial.tech/api'
    
    @classmethod
    def validate(cls) -> bool:
        """Проверяет, что все необходимые токены установлены"""
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN не установлен в .env файле")
        if not cls.KINOPOISK_API_KEY:
            raise ValueError("KINOPOISK_API_KEY не установлен в .env файле")
        return True

