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
        url = f"{self.base_url}/{endpoint}"
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    return {'error': True, 'message': f"Ошибка API: {response.status}"}
            except aiohttp.ClientError as e:
                return {'error': True, 'message': f'Ошибка сети: {str(e)}'}

    async def get_genres(self) -> List[Dict]:
        response = await self._make_request("v2.2/films/filters")
        return response.get('genres', []) if 'error' not in response else []

    async def search_films_by_genre(self, genre_id: int, page: int = 1) -> Dict:
        params = {'genres': genre_id, 'page': page, 'order': 'RATING', 'type': 'FILM'}
        return await self._make_request("v2.2/films", params)

    async def search_films_by_multiple_genres(self, genre_ids: List[int], page: int = 1) -> Dict:
        params = {'genres': genre_ids, 'page': page, 'order': 'RATING', 'type': 'FILM'}
        return await self._make_request("v2.2/films", params)

    async def search_films_by_year(self, year: Optional[int] = None, year_from: Optional[int] = None,
                                   year_to: Optional[int] = None, page: int = 1) -> Dict:
        params = {'page': page, 'order': 'RATING', 'type': 'FILM'}
        if year:
            params['yearFrom'] = params['yearTo'] = year
        else:
            if year_from: params['yearFrom'] = year_from
            if year_to: params['yearTo'] = year_to
        return await self._make_request("v2.2/films", params)

    async def search_person_by_name(self, name: str) -> List[Dict]:
        response = await self._make_request("v1/persons", {'name': name})
        return response.get('items', []) if 'error' not in response else []

    # --- НОВЫЙ МЕТОД: ПОЛУЧЕНИЕ ДЕТАЛЕЙ ФИЛЬМА (ДЛЯ ПОСТЕРА) ---
    async def get_film_details(self, film_id: int) -> Dict:
        """Получает полную информацию о фильме по ID"""
        return await self._make_request(f"v2.2/films/{film_id}")

    async def search_films_by_person(self, person_id: int, profession_key: str = 'ACTOR') -> Dict:
        data = await self._make_request(f"v1/staff/{person_id}")
        if 'error' in data: return data

        all_films = data.get('films', [])
        filtered_films = []
        seen_ids = set()
        target_prof = profession_key.upper()

        for film in all_films:
            if film.get('professionKey', '').upper() == target_prof:
                fid = film.get('filmId')
                if fid and fid not in seen_ids:
                    seen_ids.add(fid)
                    rating = film.get('rating')
                    if rating == 'null' or rating is None: rating = 'N/A'

                    film['rating'] = rating
                    film['kinopoiskId'] = fid
                    # Постер здесь все еще None, мы загрузим его позже в commands.py
                    film['posterUrlPreview'] = None
                    filtered_films.append(film)

        filtered_films.sort(key=lambda f: float(f.get('rating', 0)) if f.get('rating') != 'N/A' else 0, reverse=True)

        return {'items': filtered_films, 'total': len(filtered_films)}

    async def search_films_by_keyword(self, keyword: str, page: int = 1) -> Dict:
        """Ищет фильмы по ключевому слову (названию)"""
        endpoint = "v2.1/films/search-by-keyword"
        params = {
            'keyword': keyword,
            'page': page
        }

        response = await self._make_request(endpoint, params)

        if 'error' in response:
            return response

        # API v2.1 возвращает список в ключе 'films', а v2.2 в 'items'.
        # Приводим к единому формату для удобства.
        items = response.get('films', [])
        return {
            'items': items,
            'total': response.get('searchFilmsCountResult', len(items))
        }