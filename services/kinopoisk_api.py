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
    
    async def search_films_by_multiple_genres(
        self,
        genre_ids: List[int],
        page: int = 1,
        order: str = 'RATING',
        type: str = 'FILM'
    ) -> Dict:
        """
        Ищет фильмы по нескольким жанрам
        
        Args:
            genre_ids: Список ID жанров
            page: Номер страницы (по умолчанию 1)
            order: Сортировка (RATING, NUM_VOTE, YEAR)
            type: Тип контента (FILM, TV_SERIES, etc.)
            
        Returns:
            Словарь с результатами поиска
        """
        endpoint = "v2.2/films"
        # API поддерживает несколько жанров через запятую
        params = {
            'genres': ','.join(map(str, genre_ids)),
            'page': page,
            'order': order,
            'type': type
        }
        
        response = await self._make_request(endpoint, params)
        return response
    
    async def search_films_by_year(
        self,
        year: Optional[int] = None,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        page: int = 1,
        order: str = 'RATING',
        type: str = 'FILM'
    ) -> Dict:
        """
        Ищет фильмы по году выпуска
        
        Args:
            year: Конкретный год (если указан, year_from и year_to игнорируются)
            year_from: Год начала диапазона
            year_to: Год конца диапазона
            page: Номер страницы (по умолчанию 1)
            order: Сортировка (RATING, NUM_VOTE, YEAR)
            type: Тип контента (FILM, TV_SERIES, etc.)
            
        Returns:
            Словарь с результатами поиска
        """
        endpoint = "v2.2/films"
        params = {
            'page': page,
            'order': order,
            'type': type
        }
        
        if year:
            params['yearFrom'] = year
            params['yearTo'] = year
        else:
            if year_from:
                params['yearFrom'] = year_from
            if year_to:
                params['yearTo'] = year_to
        
        response = await self._make_request(endpoint, params)
        return response
    
    async def search_person_by_name(self, name: str) -> List[Dict]:
        """
        Ищет персону (актёра/режиссёра) по имени
        
        Args:
            name: Имя персоны
            
        Returns:
            Список словарей с информацией о персонах
        """
        endpoint = "v1/persons"
        params = {
            'name': name
        }
        
        response = await self._make_request(endpoint, params)
        
        if 'error' in response:
            return []
        
        # API может вернуть список или один объект
        if isinstance(response, list):
            return response
        elif isinstance(response, dict):
            # Если это словарь, проверяем есть ли в нем список
            if 'items' in response:
                return response['items']
            elif 'personId' in response or 'kinopoiskId' in response:
                # Это одна персона
                return [response]
        
        return []
    
    async def search_films_by_person(
        self,
        person_id: int,
        profession: str = 'ACTOR',  # ACTOR, DIRECTOR, etc.
        page: int = 1,
        order: str = 'RATING',
        type: str = 'FILM'
    ) -> Dict:
        """
        Ищет фильмы по персоне (актёру или режиссёру)
        
        Args:
            person_id: ID персоны
            profession: Профессия (ACTOR, DIRECTOR, PRODUCER, etc.)
            page: Номер страницы (по умолчанию 1)
            order: Сортировка (RATING, NUM_VOTE, YEAR)
            type: Тип контента (FILM, TV_SERIES, etc.)
            
        Returns:
            Словарь с результатами поиска
        """
        endpoint = "v2.2/films"
        params = {
            'page': page,
            'order': order,
            'type': type
        }
        
        # Для поиска по персоне используем параметр personId
        # Но сначала нужно получить фильмы персоны через другой endpoint
        # Используем v1/persons/{id}/films
        person_endpoint = f"v1/persons/{person_id}/films"
        person_films = await self._make_request(person_endpoint)
        
        if 'error' in person_films:
            return person_films
        
        # Фильтруем по профессии если нужно
        films_data = person_films.get('films', [])
        if not films_data:
            # Возможно данные в другом формате
            films_data = person_films.get('items', [])
        
        if profession:
            filtered_films = []
            for f in films_data:
                # Проверяем разные возможные структуры данных
                professions = f.get('profession', [])
                if not professions:
                    # Может быть в другом поле
                    professions = f.get('professions', [])
                
                # Проверяем соответствие профессии
                if any(p.get('professionKey', '').upper() == profession.upper() 
                       or p.get('key', '').upper() == profession.upper()
                       for p in professions if isinstance(p, dict)):
                    filtered_films.append(f)
        else:
            filtered_films = films_data
        
        # Форматируем ответ в том же формате, что и другие методы
        return {
            'items': filtered_films[:20],  # Ограничиваем до 20
            'total': len(filtered_films),
            'totalPages': 1
        }
    
    async def search_films_advanced(
        self,
        genre_ids: Optional[List[int]] = None,
        year: Optional[int] = None,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        person_id: Optional[int] = None,
        profession: Optional[str] = None,
        page: int = 1,
        order: str = 'RATING',
        type: str = 'FILM'
    ) -> Dict:
        """
        Расширенный поиск фильмов с несколькими параметрами
        
        Args:
            genre_ids: Список ID жанров
            year: Конкретный год
            year_from: Год начала диапазона
            year_to: Год конца диапазона
            person_id: ID персоны (актёра/режиссёра)
            profession: Профессия персоны (ACTOR, DIRECTOR, etc.)
            page: Номер страницы
            order: Сортировка
            type: Тип контента
            
        Returns:
            Словарь с результатами поиска
        """
        # Если указан person_id, используем специальный метод
        if person_id:
            return await self.search_films_by_person(person_id, profession, page, order, type)
        
        endpoint = "v2.2/films"
        params = {
            'page': page,
            'order': order,
            'type': type
        }
        
        if genre_ids:
            params['genres'] = ','.join(map(str, genre_ids))
        
        if year:
            params['yearFrom'] = year
            params['yearTo'] = year
        else:
            if year_from:
                params['yearFrom'] = year_from
            if year_to:
                params['yearTo'] = year_to
        
        response = await self._make_request(endpoint, params)
        return response

