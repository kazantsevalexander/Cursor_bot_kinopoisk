import aiohttp
from typing import List, Dict, Optional, Union
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
        """Выполняет запрос к API Кинопоиска"""
        url = f"{self.base_url}/{endpoint}"

        async with aiohttp.ClientSession() as session:
            try:
                # aiohttp автоматически кодирует списки в params как key=val1&key=val2
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        return {
                            'error': True,
                            'status': response.status,
                            'message': f"API Error {response.status}"
                        }
            except aiohttp.ClientError as e:
                return {
                    'error': True,
                    'message': f'Ошибка сети: {str(e)}'
                }

    async def get_genres(self) -> List[Dict]:
        """Получает список всех жанров"""
        endpoint = "v2.2/films/filters"
        response = await self._make_request(endpoint)
        if 'error' in response:
            return []
        return response.get('genres', [])

    async def search_films_by_genre(self, genre_id: int, page: int = 1) -> Dict:
        """Ищет фильмы по одному жанру"""
        endpoint = "v2.2/films"
        params = {
            'genres': genre_id,
            'page': page,
            'order': 'RATING',
            'type': 'FILM'
        }
        return await self._make_request(endpoint, params)

    async def search_films_by_multiple_genres(self, genre_ids: List[int], page: int = 1) -> Dict:
        """Ищет фильмы по нескольким жанрам"""
        endpoint = "v2.2/films"
        # Передаем список напрямую, aiohttp сформирует genres=1&genres=2
        params = {
            'genres': genre_ids,
            'page': page,
            'order': 'RATING',
            'type': 'FILM'
        }
        return await self._make_request(endpoint, params)

    async def search_films_by_year(self, year: Optional[int] = None, year_from: Optional[int] = None,
                                   year_to: Optional[int] = None, page: int = 1) -> Dict:
        """Ищет фильмы по году или диапазону"""
        endpoint = "v2.2/films"
        params = {
            'page': page,
            'order': 'RATING',
            'type': 'FILM'
        }

        if year:
            params['yearFrom'] = year
            params['yearTo'] = year
        else:
            if year_from: params['yearFrom'] = year_from
            if year_to: params['yearTo'] = year_to

        return await self._make_request(endpoint, params)

    async def search_person_by_name(self, name: str) -> List[Dict]:
        """Ищет персону по имени"""
        endpoint = "v1/persons"
        params = {'name': name}

        response = await self._make_request(endpoint, params)

        if 'error' in response:
            return []

        # v1/persons возвращает dict с ключом items
        return response.get('items', [])

    async def search_films_by_person(self, person_id: int, profession_key: str = 'ACTOR') -> Dict:
        """
        Получает фильмы персоны.
        Используем v1/staff/{id}, так как он возвращает детали персоны и список фильмов.
        """
        endpoint = f"v1/staff/{person_id}"
        data = await self._make_request(endpoint)

        if 'error' in data:
            return data

        all_films = data.get('films', [])

        # Фильтруем фильмы по профессии (ACTOR, DIRECTOR и т.д.)
        # и убираем дубликаты (один фильм может быть указан несколько раз для разных ролей)
        seen_ids = set()
        filtered_films = []

        target_prof = profession_key.upper()

        for film in all_films:
            # Проверяем профессию
            p_key = film.get('professionKey', '').upper()
            if p_key == target_prof:
                fid = film.get('filmId')
                if fid and fid not in seen_ids:
                    seen_ids.add(fid)
                    # Нормализуем данные, чтобы они были похожи на ответ v2.2/films
                    # v1/staff возвращает rating как строку, иногда null
                    rating = film.get('rating')
                    if rating == 'null' or rating is None:
                        rating = 'N/A'

                    film['rating'] = rating
                    film['kinopoiskId'] = fid  # Для совместимости
                    filtered_films.append(film)

        # Сортируем по рейтингу (если есть), чтобы показать лучшие сверху
        def sort_key(f):
            try:
                return float(f.get('rating', 0))
            except (ValueError, TypeError):
                return 0

        filtered_films.sort(key=sort_key, reverse=True)

        # Возвращаем в формате, совместимом с другими методами
        return {
            'items': filtered_films,
            'total': len(filtered_films)
        }