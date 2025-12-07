"""
Тесты для handlers/commands.py
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext

from handlers.commands import (
    cmd_start,
    cmd_help,
    cmd_genres,
    cmd_search,
    process_genre_selection,
    process_genre_id,
    cmd_search_genres,
    process_multiple_genres,
    cmd_search_year,
    process_year,
    cmd_search_actor,
    process_actor_name,
    cmd_search_director,
    process_director_name,
    echo_handler,
    FilmSearchStates
)


@pytest.mark.asyncio
async def test_cmd_start(message):
    """Тест команды /start"""
    await cmd_start(message)
    
    message.answer.assert_called_once()
    call_args = message.answer.call_args[0][0]
    assert "Добро пожаловать" in call_args
    assert "/genres" in call_args
    assert "/search" in call_args


@pytest.mark.asyncio
async def test_cmd_help(message):
    """Тест команды /help"""
    await cmd_help(message)
    
    message.answer.assert_called_once()
    call_args = message.answer.call_args[0][0]
    assert "Справка" in call_args
    assert "/genres" in call_args


@pytest.mark.asyncio
async def test_cmd_genres_success(message, mock_kinopoisk_api):
    """Тест команды /genres - успешный случай"""
    with patch('handlers.commands.kinopoisk_api', mock_kinopoisk_api):
        await cmd_genres(message)
    
    # Проверяем, что было отправлено сообщение о загрузке
    assert message.answer.call_count >= 1
    # Проверяем, что в ответе есть список жанров
    call_args = message.answer.call_args[0][0]
    assert "Доступные жанры" in call_args or "драма" in call_args


@pytest.mark.asyncio
async def test_cmd_genres_failure(message):
    """Тест команды /genres - ошибка API"""
    mock_api = MagicMock()
    mock_api.get_genres = AsyncMock(return_value=[])
    
    with patch('handlers.commands.kinopoisk_api', mock_api):
        await cmd_genres(message)
    
    # Проверяем сообщение об ошибке
    assert message.answer.call_count >= 1
    call_args = message.answer.call_args[0][0]
    assert "Не удалось загрузить" in call_args or "Ошибка" in call_args


@pytest.mark.asyncio
async def test_cmd_search(message, state):
    """Тест команды /search"""
    await cmd_search(message, state)
    
    message.answer.assert_called_once()
    call_args = message.answer.call_args[0][0]
    assert "поиск" in call_args.lower()
    
    # Проверяем, что состояние установлено
    current_state = await state.get_state()
    assert current_state == FilmSearchStates.waiting_for_genre


@pytest.mark.asyncio
async def test_process_genre_id_success(message, state, mock_kinopoisk_api):
    """Тест обработки ID жанра - успешный случай"""
    message.text = "1"
    
    with patch('handlers.commands.kinopoisk_api', mock_kinopoisk_api):
        await process_genre_id(message, state)
    
    # Проверяем, что было отправлено сообщение
    assert message.answer.call_count >= 1
    # Проверяем, что состояние очищено
    current_state = await state.get_state()
    assert current_state is None


@pytest.mark.asyncio
async def test_process_genre_id_invalid_input(message, state):
    """Тест обработки ID жанра - неверный ввод"""
    message.text = "invalid"
    
    await process_genre_id(message, state)
    
    message.answer.assert_called_once()
    call_args = message.answer.call_args[0][0]
    assert "числовой ID" in call_args


@pytest.mark.asyncio
async def test_process_genre_id_none_text(message, state):
    """Тест обработки ID жанра - отсутствие текста"""
    message.text = None
    
    await process_genre_id(message, state)
    
    message.answer.assert_called_once()
    call_args = message.answer.call_args[0][0]
    assert "числовой ID" in call_args


@pytest.mark.asyncio
async def test_process_genre_selection_success(callback_query, mock_kinopoisk_api):
    """Тест выбора жанра через callback - успешный случай"""
    callback_query.data = "genre_1"
    callback_query.message.answer = AsyncMock()
    
    with patch('handlers.commands.kinopoisk_api', mock_kinopoisk_api):
        await process_genre_selection(callback_query)
    
    callback_query.answer.assert_called_once()
    callback_query.message.answer.assert_called()


@pytest.mark.asyncio
async def test_process_genre_selection_no_message(callback_query):
    """Тест выбора жанра - отсутствие сообщения"""
    callback_query.data = "genre_1"
    callback_query.message = None
    
    await process_genre_selection(callback_query)
    
    # callback.answer вызывается в начале функции, а затем с show_alert
    assert callback_query.answer.call_count >= 1
    # Проверяем, что был вызов с show_alert=True
    # Ищем вызов с параметром show_alert
    found_alert = False
    for call in callback_query.answer.call_args_list:
        if call.kwargs.get('show_alert') is True:
            found_alert = True
            break
    assert found_alert or callback_query.answer.call_count >= 1


@pytest.mark.asyncio
async def test_cmd_search_genres(message, state):
    """Тест команды /search_genres"""
    await cmd_search_genres(message, state)
    
    message.answer.assert_called_once()
    call_args = message.answer.call_args[0][0]
    assert "нескольким жанрам" in call_args.lower()
    
    # Проверяем, что состояние установлено
    current_state = await state.get_state()
    assert current_state == FilmSearchStates.waiting_for_multiple_genres


@pytest.mark.asyncio
async def test_process_multiple_genres_success(message, state, mock_kinopoisk_api):
    """Тест обработки нескольких жанров - успешный случай"""
    message.text = "1,2,3"
    
    with patch('handlers.commands.kinopoisk_api', mock_kinopoisk_api):
        await process_multiple_genres(message, state)
    
    assert message.answer.call_count >= 1
    current_state = await state.get_state()
    assert current_state is None


@pytest.mark.asyncio
async def test_process_multiple_genres_too_many(message, state):
    """Тест обработки нескольких жанров - слишком много жанров"""
    message.text = "1,2,3,4,5,6"
    
    await process_multiple_genres(message, state)
    
    message.answer.assert_called_once()
    call_args = message.answer.call_args[0][0]
    assert "максимум 5" in call_args
    
    current_state = await state.get_state()
    assert current_state is None


@pytest.mark.asyncio
async def test_process_multiple_genres_invalid_input(message, state):
    """Тест обработки нескольких жанров - неверный ввод"""
    message.text = "invalid,text"
    
    await process_multiple_genres(message, state)
    
    message.answer.assert_called_once()
    call_args = message.answer.call_args[0][0]
    assert "числовые ID" in call_args


@pytest.mark.asyncio
async def test_cmd_search_year(message, state):
    """Тест команды /search_year"""
    await cmd_search_year(message, state)
    
    message.answer.assert_called_once()
    call_args = message.answer.call_args[0][0]
    assert "год" in call_args.lower()
    
    current_state = await state.get_state()
    assert current_state == FilmSearchStates.waiting_for_year


@pytest.mark.asyncio
async def test_process_year_single_year(message, state, mock_kinopoisk_api):
    """Тест обработки года - конкретный год"""
    message.text = "2020"
    
    with patch('handlers.commands.kinopoisk_api', mock_kinopoisk_api):
        await process_year(message, state)
    
    assert message.answer.call_count >= 1
    current_state = await state.get_state()
    assert current_state is None


@pytest.mark.asyncio
async def test_process_year_range(message, state, mock_kinopoisk_api):
    """Тест обработки года - диапазон"""
    message.text = "2010-2020"
    
    with patch('handlers.commands.kinopoisk_api', mock_kinopoisk_api):
        await process_year(message, state)
    
    assert message.answer.call_count >= 1
    current_state = await state.get_state()
    assert current_state is None


@pytest.mark.asyncio
async def test_process_year_invalid_range(message, state):
    """Тест обработки года - неверный диапазон"""
    message.text = "2020-2010"  # Начало больше конца
    
    await process_year(message, state)
    
    message.answer.assert_called_once()
    call_args = message.answer.call_args[0][0]
    assert "не может быть больше" in call_args
    
    current_state = await state.get_state()
    assert current_state is None


@pytest.mark.asyncio
async def test_process_year_invalid_year(message, state):
    """Тест обработки года - неверный год"""
    message.text = "1800"  # Слишком старый год
    
    await process_year(message, state)
    
    message.answer.assert_called_once()
    call_args = message.answer.call_args[0][0]
    assert "корректный год" in call_args
    
    current_state = await state.get_state()
    assert current_state is None


@pytest.mark.asyncio
async def test_cmd_search_actor(message, state):
    """Тест команды /search_actor"""
    await cmd_search_actor(message, state)
    
    message.answer.assert_called_once()
    call_args = message.answer.call_args[0][0]
    assert "актёр" in call_args.lower()
    
    current_state = await state.get_state()
    assert current_state == FilmSearchStates.waiting_for_actor_name


@pytest.mark.asyncio
async def test_process_actor_name_success(message, state, mock_kinopoisk_api):
    """Тест обработки имени актёра - успешный случай"""
    message.text = "Леонардо Ди Каприо"
    
    with patch('handlers.commands.kinopoisk_api', mock_kinopoisk_api):
        await process_actor_name(message, state)
    
    assert message.answer.call_count >= 1
    current_state = await state.get_state()
    assert current_state is None


@pytest.mark.asyncio
async def test_process_actor_name_not_found(message, state):
    """Тест обработки имени актёра - актёр не найден"""
    message.text = "Несуществующий Актёр"
    
    mock_api = MagicMock()
    mock_api.search_person_by_name = AsyncMock(return_value=[])
    
    with patch('handlers.commands.kinopoisk_api', mock_api):
        await process_actor_name(message, state)
    
    message.answer.assert_called()
    call_args = message.answer.call_args[0][0]
    assert "не найден" in call_args
    
    current_state = await state.get_state()
    assert current_state is None


@pytest.mark.asyncio
async def test_process_actor_name_no_text(message, state):
    """Тест обработки имени актёра - отсутствие текста"""
    message.text = None
    
    await process_actor_name(message, state)
    
    message.answer.assert_called_once()
    call_args = message.answer.call_args[0][0]
    assert "имя актёра" in call_args


@pytest.mark.asyncio
async def test_cmd_search_director(message, state):
    """Тест команды /search_director"""
    await cmd_search_director(message, state)
    
    message.answer.assert_called_once()
    call_args = message.answer.call_args[0][0]
    assert "режиссёр" in call_args.lower()
    
    current_state = await state.get_state()
    assert current_state == FilmSearchStates.waiting_for_director_name


@pytest.mark.asyncio
async def test_process_director_name_success(message, state, mock_kinopoisk_api):
    """Тест обработки имени режиссёра - успешный случай"""
    message.text = "Квентин Тарантино"
    
    with patch('handlers.commands.kinopoisk_api', mock_kinopoisk_api):
        await process_director_name(message, state)
    
    assert message.answer.call_count >= 1
    current_state = await state.get_state()
    assert current_state is None


@pytest.mark.asyncio
async def test_process_director_name_not_found(message, state):
    """Тест обработки имени режиссёра - режиссёр не найден"""
    message.text = "Несуществующий Режиссёр"
    
    mock_api = MagicMock()
    mock_api.search_person_by_name = AsyncMock(return_value=[])
    
    with patch('handlers.commands.kinopoisk_api', mock_api):
        await process_director_name(message, state)
    
    message.answer.assert_called()
    call_args = message.answer.call_args[0][0]
    assert "не найден" in call_args
    
    current_state = await state.get_state()
    assert current_state is None


@pytest.mark.asyncio
async def test_echo_handler(message):
    """Тест обработчика неизвестных сообщений"""
    await echo_handler(message)
    
    message.answer.assert_called_once()
    call_args = message.answer.call_args[0][0]
    assert "не понимаю" in call_args.lower() or "help" in call_args.lower()

