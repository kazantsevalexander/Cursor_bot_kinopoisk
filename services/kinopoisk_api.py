import aiohttp
from typing import List, Dict, Optional
from config.config import Config


class KinopoiskAPI:
    """Класс для работы с API Кинопоиска"""
    
    def __init__(self):
        self.api_key = Config.KINOPOISK_API_KEY
        self.base_url = Config.KINOPOISK_API_URL
        self.headers = {
            'X-API-KEY': self.api_key,
            'Content-Type': 'application/json'
        }
    
    async def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """
        Выполняет запрос к API Кинопоиска
        
        Args:
            endpoint: Конечная точка API
            params: Параметры запроса
            
        Returns:
            Словарь с данными ответа
        """
        url = f"{self.base_url}/{endpoint}"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        return {
                            'error': True,
                            'status': response.status,
                            'message': error_text
                        }
            except aiohttp.ClientError as e:
                return {
                    'error': True,
                    'message': f'Ошибка при запросе к API: {str(e)}'
                }
    
    async def get_genres(self) -> List[Dict]:
        """
        Получает список всех жанров
        
        Returns:
            Список словарей с информацией о жанрах
        """
        endpoint = "v2.2/films/filters"
        response = await self._make_request(endpoint)
        
        if 'error' in response:
            return []
        
        # API возвращает фильтры, включая жанры
        genres = response.get('genres', [])
        return genres
    
    async def search_films_by_genre(
        self, 
        genre_id: int, 
        page: int = 1,
        order: str = 'RATING',
        type: str = 'FILM'
    ) -> Dict:
        """
        Ищет фильмы по жанру
        
        Args:
            genre_id: ID жанра
            page: Номер страницы (по умолчанию 1)
            order: Сортировка (RATING, NUM_VOTE, YEAR)
            type: Тип контента (FILM, TV_SERIES, etc.)
            
        Returns:
            Словарь с результатами поиска
        """
        endpoint = "v2.2/films"
        params = {
            'genres': genre_id,
            'page': page,
            'order': order,
            'type': type
        }
        
        response = await self._make_request(endpoint, params)
        return response
    
    async def get_film_by_id(self, film_id: int) -> Dict:
        """
        Получает информацию о фильме по ID
        
        Args:
            film_id: ID фильма
            
        Returns:
            Словарь с информацией о фильме
        """
        endpoint = f"v2.2/films/{film_id}"
        response = await self._make_request(endpoint)
        return response

