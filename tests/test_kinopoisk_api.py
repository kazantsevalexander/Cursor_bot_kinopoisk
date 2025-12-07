"""
Тесты для services/kinopoisk_api.py
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import aiohttp

from services.kinopoisk_api import KinopoiskAPI


@pytest.fixture
def api():
    """Фикстура для создания экземпляра API"""
    with patch('services.kinopoisk_api.Config') as mock_config:
        mock_config.KINOPOISK_API_KEY = "test_api_key"
        mock_config.KINOPOISK_API_URL = "https://test.api.url"
        return KinopoiskAPI()


@pytest.mark.asyncio
async def test_get_genres_success(api):
    """Тест получения жанров - успешный случай"""
    mock_response_data = {
        'genres': [
            {'id': 1, 'genre': 'драма'},
            {'id': 2, 'genre': 'комедия'}
        ]
    }
    
    # Мокируем _make_request напрямую
    with patch.object(api, '_make_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_response_data
        result = await api.get_genres()
    
    assert len(result) == 2
    assert result[0]['genre'] == 'драма'
    assert result[1]['genre'] == 'комедия'


@pytest.mark.asyncio
async def test_get_genres_error(api):
    """Тест получения жанров - ошибка API"""
    # Мокируем _make_request с ошибкой
    with patch.object(api, '_make_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {'error': True, 'status': 500, 'message': 'Internal Server Error'}
        result = await api.get_genres()
    
    assert result == []


@pytest.mark.asyncio
async def test_search_films_by_genre_success(api):
    """Тест поиска фильмов по жанру - успешный случай"""
    mock_response_data = {
        'items': [
            {
                'kinopoiskId': 123,
                'nameRu': 'Тестовый фильм',
                'year': 2020,
                'rating': '8.5'
            }
        ],
        'total': 1
    }
    
    with patch.object(api, '_make_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_response_data
        result = await api.search_films_by_genre(genre_id=1)
    
    assert 'items' in result
    assert len(result['items']) == 1
    assert result['items'][0]['nameRu'] == 'Тестовый фильм'


@pytest.mark.asyncio
async def test_search_films_by_genre_error(api):
    """Тест поиска фильмов по жанру - ошибка API"""
    with patch.object(api, '_make_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {'error': True, 'status': 404, 'message': 'Not Found'}
        result = await api.search_films_by_genre(genre_id=999)
    
    assert 'error' in result
    assert result['status'] == 404


@pytest.mark.asyncio
async def test_search_films_by_multiple_genres_success(api):
    """Тест поиска фильмов по нескольким жанрам - успешный случай"""
    mock_response_data = {
        'items': [
            {
                'kinopoiskId': 123,
                'nameRu': 'Тестовый фильм',
                'year': 2020,
                'rating': '8.5'
            }
        ],
        'total': 1
    }
    
    with patch.object(api, '_make_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_response_data
        result = await api.search_films_by_multiple_genres(genre_ids=[1, 2])
    
    assert 'items' in result
    assert len(result['items']) == 1


@pytest.mark.asyncio
async def test_search_films_by_year_single_year(api):
    """Тест поиска фильмов по году - конкретный год"""
    mock_response_data = {
        'items': [
            {
                'kinopoiskId': 123,
                'nameRu': 'Тестовый фильм',
                'year': 2020,
                'rating': '8.5'
            }
        ],
        'total': 1
    }
    
    with patch.object(api, '_make_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_response_data
        result = await api.search_films_by_year(year=2020)
    
    assert 'items' in result
    assert len(result['items']) == 1


@pytest.mark.asyncio
async def test_search_films_by_year_range(api):
    """Тест поиска фильмов по году - диапазон"""
    mock_response_data = {
        'items': [],
        'total': 0
    }
    
    with patch.object(api, '_make_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_response_data
        result = await api.search_films_by_year(year_from=2010, year_to=2020)
    
    assert 'items' in result


@pytest.mark.asyncio
async def test_search_person_by_name_success(api):
    """Тест поиска персоны по имени - успешный случай"""
    mock_response_data = [
        {
            'personId': 456,
            'nameRu': 'Тестовый актёр',
            'nameEn': 'Test Actor'
        }
    ]
    
    with patch.object(api, '_make_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_response_data
        result = await api.search_person_by_name("Тестовый актёр")
    
    assert len(result) == 1
    assert result[0]['personId'] == 456


@pytest.mark.asyncio
async def test_search_person_by_name_not_found(api):
    """Тест поиска персоны по имени - не найдено"""
    with patch.object(api, '_make_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {'error': True, 'status': 404, 'message': 'Not Found'}
        result = await api.search_person_by_name("Несуществующий")
    
    assert result == []


@pytest.mark.asyncio
async def test_search_films_by_person_success(api):
    """Тест поиска фильмов по персоне - успешный случай"""
    mock_response_data = {
        'films': [
            {
                'filmId': 123,
                'profession': [
                    {'professionKey': 'ACTOR'}
                ]
            }
        ]
    }
    
    with patch.object(api, '_make_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_response_data
        result = await api.search_films_by_person(person_id=456, profession='ACTOR')
    
    assert 'items' in result
    assert 'total' in result


@pytest.mark.asyncio
async def test_search_films_by_person_error(api):
    """Тест поиска фильмов по персоне - ошибка API"""
    with patch.object(api, '_make_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {'error': True, 'status': 500, 'message': 'Internal Server Error'}
        result = await api.search_films_by_person(person_id=999)
    
    assert 'error' in result


@pytest.mark.asyncio
async def test_make_request_connection_error(api):
    """Тест обработки ошибки соединения"""
    # Мокируем ClientSession так, чтобы выбрасывалась ошибка при вызове get()
    with patch('aiohttp.ClientSession') as mock_session_class:
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        # Создаем мок ответа, который выбрасывает ошибку при входе в контекст
        mock_response = MagicMock()
        mock_response.__aenter__ = AsyncMock(side_effect=aiohttp.ClientError("Connection error"))
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        # get() должен возвращать объект, который является контекстным менеджером
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session_class.return_value = mock_session
        
        result = await api._make_request("test/endpoint")
    
    assert 'error' in result
    assert 'Ошибка при запросе к API' in result['message']


@pytest.mark.asyncio
async def test_get_film_by_id_success(api):
    """Тест получения фильма по ID - успешный случай"""
    mock_response_data = {
        'kinopoiskId': 123,
        'nameRu': 'Тестовый фильм',
        'year': 2020,
        'rating': '8.5'
    }
    
    with patch.object(api, '_make_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_response_data
        result = await api.get_film_by_id(film_id=123)
    
    assert result['kinopoiskId'] == 123
    assert result['nameRu'] == 'Тестовый фильм'
