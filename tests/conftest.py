"""
Фикстуры для тестирования бота
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import User, Chat, Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from services.kinopoisk_api import KinopoiskAPI


@pytest.fixture
def bot():
    """Фикстура для создания бота"""
    return Bot(token="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11")


@pytest.fixture
def dispatcher():
    """Фикстура для создания диспетчера"""
    storage = MemoryStorage()
    return Dispatcher(storage=storage)


@pytest.fixture
def user():
    """Фикстура для создания пользователя"""
    return User(
        id=123456789,
        is_bot=False,
        first_name="Test",
        username="test_user"
    )


@pytest.fixture
def chat():
    """Фикстура для создания чата"""
    return Chat(
        id=123456789,
        type="private"
    )


@pytest.fixture
def message(user, chat):
    """Фикстура для создания сообщения"""
    msg = MagicMock(spec=Message)
    msg.from_user = user
    msg.chat = chat
    msg.message_id = 1
    msg.text = None
    msg.answer = AsyncMock()
    msg.reply = AsyncMock()
    return msg


@pytest.fixture
def callback_query(user, chat, message):
    """Фикстура для создания callback query"""
    callback = MagicMock(spec=CallbackQuery)
    callback.from_user = user
    callback.message = message
    callback.data = None
    callback.answer = AsyncMock()
    callback.id = "test_callback_id"
    return callback


@pytest.fixture
def state():
    """Фикстура для создания FSM контекста"""
    storage = MemoryStorage()
    return FSMContext(
        storage=storage,
        key=storage.resolve_key(user_id=123456789, chat_id=123456789)
    )


@pytest.fixture
def mock_kinopoisk_api():
    """Фикстура для мокирования KinopoiskAPI"""
    api = MagicMock(spec=KinopoiskAPI)
    
    # Мокируем методы API
    api.get_genres = AsyncMock(return_value=[
        {'id': 1, 'genre': 'драма'},
        {'id': 2, 'genre': 'комедия'},
        {'id': 3, 'genre': 'боевик'}
    ])
    
    api.search_films_by_genre = AsyncMock(return_value={
        'items': [
            {
                'kinopoiskId': 123,
                'nameRu': 'Тестовый фильм',
                'nameEn': 'Test Film',
                'year': 2020,
                'rating': '8.5',
                'ratingKinopoisk': '8.7'
            }
        ],
        'total': 1
    })
    
    api.search_films_by_multiple_genres = AsyncMock(return_value={
        'items': [
            {
                'kinopoiskId': 123,
                'nameRu': 'Тестовый фильм',
                'nameEn': 'Test Film',
                'year': 2020,
                'rating': '8.5',
                'ratingKinopoisk': '8.7'
            }
        ],
        'total': 1
    })
    
    api.search_films_by_year = AsyncMock(return_value={
        'items': [
            {
                'kinopoiskId': 123,
                'nameRu': 'Тестовый фильм',
                'nameEn': 'Test Film',
                'year': 2020,
                'rating': '8.5',
                'ratingKinopoisk': '8.7'
            }
        ],
        'total': 1
    })
    
    api.search_person_by_name = AsyncMock(return_value=[
        {
            'personId': 456,
            'nameRu': 'Тестовый актёр',
            'nameEn': 'Test Actor'
        }
    ])
    
    api.search_films_by_person = AsyncMock(return_value={
        'items': [
            {
                'film': {
                    'filmId': 123,
                    'nameRu': 'Тестовый фильм',
                    'nameEn': 'Test Film',
                    'year': 2020,
                    'rating': '8.5',
                    'ratingKinopoisk': '8.7'
                }
            }
        ],
        'total': 1
    })
    
    return api


@pytest.fixture
def sample_films():
    """Фикстура с примерными данными фильмов"""
    return [
        {
            'kinopoiskId': 123,
            'nameRu': 'Тестовый фильм 1',
            'nameEn': 'Test Film 1',
            'year': 2020,
            'rating': '8.5',
            'ratingKinopoisk': '8.7'
        },
        {
            'kinopoiskId': 124,
            'nameRu': 'Тестовый фильм 2',
            'nameEn': 'Test Film 2',
            'year': 2021,
            'rating': '7.5',
            'ratingKinopoisk': '7.8'
        }
    ]


@pytest.fixture
def sample_genres():
    """Фикстура с примерными данными жанров"""
    return [
        {'id': 1, 'genre': 'драма'},
        {'id': 2, 'genre': 'комедия'},
        {'id': 3, 'genre': 'боевик'},
        {'id': 4, 'genre': 'триллер'},
        {'id': 5, 'genre': 'фантастика'}
    ]

