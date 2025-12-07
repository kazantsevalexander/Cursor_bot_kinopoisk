import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    BOT_TOKEN: str = os.getenv('BOT_TOKEN', '')
    KINOPOISK_API_KEY: str = os.getenv('KINOPOISK_API_KEY', '')
    KINOPOISK_API_URL: str = 'https://kinopoiskapiunofficial.tech/api'

    @classmethod
    def validate(cls) -> bool:
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN не установлен в .env")
        if not cls.KINOPOISK_API_KEY:
            raise ValueError("KINOPOISK_API_KEY не установлен в .env")
        return True