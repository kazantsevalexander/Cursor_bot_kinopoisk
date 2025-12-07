from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services.kinopoisk_api import KinopoiskAPI
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()
kinopoisk_api = KinopoiskAPI()


class FilmSearchStates(StatesGroup):
    """Состояния для поиска фильмов"""
    waiting_for_genre = State()
    waiting_for_multiple_genres = State()
    waiting_for_year = State()
    waiting_for_actor_name = State()
    waiting_for_director_name = State()


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    welcome_text = (
        "🎬 Добро пожаловать в бота Кинопоиска!\n\n"
        "Доступные команды:\n"
        "/genres - Получить список жанров\n"
        "/search - Поиск фильмов по жанру\n"
        "/search_genres - Поиск по нескольким жанрам\n"
        "/search_year - Поиск фильмов по году\n"
        "/search_actor - Поиск фильмов по актёру\n"
        "/search_director - Поиск фильмов по режиссёру\n"
        "/help - Справка"
    )
    await message.answer(welcome_text)


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    help_text = (
        "📖 Справка по использованию бота:\n\n"
        "🔍 Команды поиска:\n"
        "/genres - Показывает список всех доступных жанров\n"
        "/search - Поиск фильмов по одному жанру\n"
        "/search_genres - Поиск фильмов по нескольким жанрам\n"
        "/search_year - Поиск фильмов по году выпуска\n"
        "/search_actor - Поиск фильмов по актёру\n"
        "/search_director - Поиск фильмов по режиссёру\n\n"
        "После выбора параметров бот покажет список фильмов с рейтингом и описанием."
    )
    await message.answer(help_text)


@router.message(Command("genres"))
async def cmd_genres(message: Message):
    """Обработчик команды /genres - получение списка жанров"""
    await message.answer("⏳ Загружаю список жанров...")
    
    genres = await kinopoisk_api.get_genres()
    
    if not genres:
        await message.answer("❌ Не удалось загрузить список жанров. Попробуйте позже.")
        return
    
    # Формируем клавиатуру с жанрами
    builder = InlineKeyboardBuilder()
    
    for genre in genres[:20]:  # Ограничиваем до 20 жанров для удобства
        genre_id = genre.get('id')
        genre_name = genre.get('genre', 'Неизвестный жанр')
        builder.button(
            text=genre_name,
            callback_data=f"genre_{genre_id}"
        )
    
    builder.adjust(2)  # 2 кнопки в ряд
    
    genres_text = "🎭 Доступные жанры:\n\n"
    genres_text += "\n".join([f"• {g.get('genre', 'Неизвестный')}" for g in genres[:20]])
    
    await message.answer(
        genres_text,
        reply_markup=builder.as_markup()
    )


@router.message(Command("search"))
async def cmd_search(message: Message, state: FSMContext):
    """Обработчик команды /search - начало поиска по жанру"""
    await message.answer(
        "🔍 Для поиска фильмов по жанру используйте команду /genres "
        "и выберите жанр из списка, или отправьте ID жанра."
    )
    await state.set_state(FilmSearchStates.waiting_for_genre)


@router.callback_query(F.data.startswith("genre_"))
async def process_genre_selection(callback: CallbackQuery):
    """Обработчик выбора жанра из списка"""
    await callback.answer()
    
    # Проверяем доступность сообщения
    if not callback.message or not isinstance(callback.message, Message):
        await callback.answer("❌ Сообщение недоступно.", show_alert=True)
        return
    
    if not callback.data:
        await callback.message.answer("❌ Ошибка: данные не получены.")
        return
    
    genre_id = int(callback.data.split("_")[1])
    await callback.message.answer(f"⏳ Ищу фильмы по выбранному жанру...")
    
    # Получаем фильмы по жанру
    result = await kinopoisk_api.search_films_by_genre(genre_id)
    
    if 'error' in result:
        await callback.message.answer(
            f"❌ Ошибка при поиске: {result.get('message', 'Неизвестная ошибка')}"
        )
        return
    
    films = result.get('items', [])
    
    if not films:
        await callback.message.answer("😔 Фильмы по данному жанру не найдены.")
        return
    
    # Отправляем первые 10 фильмов
    response_text = f"🎬 Найдено фильмов: {result.get('total', len(films))}\n\n"
    
    for i, film in enumerate(films[:10], 1):
        name_ru = film.get('nameRu', 'Без названия')
        name_en = film.get('nameEn', '')
        year = film.get('year', '?')
        rating = film.get('rating', 'N/A')
        rating_kinopoisk = film.get('ratingKinopoisk', 'N/A')
        film_id = film.get('kinopoiskId', '')
        
        response_text += f"{i}. {name_ru}"
        if name_en:
            response_text += f" ({name_en})"
        response_text += f"\n   📅 Год: {year}"
        response_text += f"\n   ⭐ Рейтинг: {rating}"
        if rating_kinopoisk and rating_kinopoisk != 'null':
            response_text += f" | Кинопоиск: {rating_kinopoisk}"
        response_text += f"\n   🔗 ID: {film_id}\n\n"
    
    if len(films) > 10:
        response_text += f"\n... и еще {len(films) - 10} фильмов"
    
    await callback.message.answer(response_text)


@router.message(FilmSearchStates.waiting_for_genre)
async def process_genre_id(message: Message, state: FSMContext):
    """Обработчик ввода ID жанра"""
    if not message.text:
        await message.answer("❌ Пожалуйста, введите числовой ID жанра или используйте /genres для выбора из списка.")
        return
    
    try:
        genre_id = int(message.text)
        await message.answer(f"⏳ Ищу фильмы по жанру с ID {genre_id}...")
        
        result = await kinopoisk_api.search_films_by_genre(genre_id)
        
        if 'error' in result:
            await message.answer(
                f"❌ Ошибка при поиске: {result.get('message', 'Неизвестная ошибка')}"
            )
            await state.clear()
            return
        
        films = result.get('items', [])
        
        if not films:
            await message.answer("😔 Фильмы по данному жанру не найдены.")
            await state.clear()
            return
        
        response_text = f"🎬 Найдено фильмов: {result.get('total', len(films))}\n\n"
        
        for i, film in enumerate(films[:10], 1):
            name_ru = film.get('nameRu', 'Без названия')
            name_en = film.get('nameEn', '')
            year = film.get('year', '?')
            rating = film.get('rating', 'N/A')
            rating_kinopoisk = film.get('ratingKinopoisk', 'N/A')
            
            response_text += f"{i}. {name_ru}"
            if name_en:
                response_text += f" ({name_en})"
            response_text += f"\n   📅 Год: {year}"
            response_text += f"\n   ⭐ Рейтинг: {rating}"
            if rating_kinopoisk and rating_kinopoisk != 'null':
                response_text += f" | Кинопоиск: {rating_kinopoisk}\n\n"
        
        await message.answer(response_text)
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Пожалуйста, введите числовой ID жанра или используйте /genres для выбора из списка.")


@router.message(Command("search_genres"))
async def cmd_search_genres(message: Message, state: FSMContext):
    """Обработчик команды /search_genres - поиск по нескольким жанрам"""
    await message.answer(
        "🎭 Для поиска по нескольким жанрам отправьте ID жанров через запятую.\n"
        "Например: 1,2,3\n\n"
        "Используйте /genres чтобы увидеть список жанров с их ID."
    )
    await state.set_state(FilmSearchStates.waiting_for_multiple_genres)


@router.message(FilmSearchStates.waiting_for_multiple_genres)
async def process_multiple_genres(message: Message, state: FSMContext):
    """Обработчик ввода нескольких ID жанров"""
    if not message.text:
        await message.answer("❌ Пожалуйста, введите числовые ID жанров через запятую (например: 1,2,3)")
        return
    
    try:
        # Парсим список ID жанров
        genre_ids = [int(gid.strip()) for gid in message.text.split(',')]
        
        if not genre_ids:
            await message.answer("❌ Пожалуйста, введите хотя бы один ID жанра.")
            return
        
        if len(genre_ids) > 5:
            await message.answer("❌ Можно указать максимум 5 жанров одновременно.")
            await state.clear()
            return
        
        await message.answer(f"⏳ Ищу фильмы по жанрам: {', '.join(map(str, genre_ids))}...")
        
        result = await kinopoisk_api.search_films_by_multiple_genres(genre_ids)
        
        if 'error' in result:
            await message.answer(
                f"❌ Ошибка при поиске: {result.get('message', 'Неизвестная ошибка')}"
            )
            await state.clear()
            return
        
        films = result.get('items', [])
        
        if not films:
            await message.answer("😔 Фильмы по данным жанрам не найдены.")
            await state.clear()
            return
        
        response_text = f"🎬 Найдено фильмов: {result.get('total', len(films))}\n\n"
        
        for i, film in enumerate(films[:10], 1):
            name_ru = film.get('nameRu', 'Без названия')
            name_en = film.get('nameEn', '')
            year = film.get('year', '?')
            rating = film.get('rating', 'N/A')
            rating_kinopoisk = film.get('ratingKinopoisk', 'N/A')
            film_id = film.get('kinopoiskId', '')
            
            response_text += f"{i}. {name_ru}"
            if name_en:
                response_text += f" ({name_en})"
            response_text += f"\n   📅 Год: {year}"
            response_text += f"\n   ⭐ Рейтинг: {rating}"
            if rating_kinopoisk and rating_kinopoisk != 'null':
                response_text += f" | Кинопоиск: {rating_kinopoisk}"
            response_text += f"\n   🔗 ID: {film_id}\n\n"
        
        if len(films) > 10:
            response_text += f"\n... и еще {len(films) - 10} фильмов"
        
        await message.answer(response_text)
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Пожалуйста, введите числовые ID жанров через запятую (например: 1,2,3)")


@router.message(Command("search_year"))
async def cmd_search_year(message: Message, state: FSMContext):
    """Обработчик команды /search_year - поиск по году"""
    await message.answer(
        "📅 Для поиска фильмов по году отправьте:\n"
        "• Конкретный год (например: 2020)\n"
        "• Диапазон лет через дефис (например: 2010-2020)\n"
        "• Год начала диапазона (например: 2010-)\n"
        "• Год конца диапазона (например: -2020)"
    )
    await state.set_state(FilmSearchStates.waiting_for_year)


@router.message(FilmSearchStates.waiting_for_year)
async def process_year(message: Message, state: FSMContext):
    """Обработчик ввода года"""
    if not message.text:
        await message.answer("❌ Пожалуйста, введите корректный год или диапазон лет (например: 2020 или 2010-2020)")
        return
    
    try:
        text = message.text.strip()
        
        # Проверяем формат диапазона
        if '-' in text:
            parts = text.split('-')
            if len(parts) == 2:
                year_from_str = parts[0].strip()
                year_to_str = parts[1].strip()
                
                year_from = int(year_from_str) if year_from_str else None
                year_to = int(year_to_str) if year_to_str else None
                
                if year_from and year_to and year_from > year_to:
                    await message.answer("❌ Год начала не может быть больше года конца.")
                    await state.clear()
                    return
                
                await message.answer(f"⏳ Ищу фильмы с {year_from or 'начала'} по {year_to or 'конца'}...")
                result = await kinopoisk_api.search_films_by_year(
                    year_from=year_from,
                    year_to=year_to
                )
            else:
                await message.answer("❌ Неверный формат. Используйте: год или год-год")
                return
        else:
            # Конкретный год
            year = int(text)
            if year < 1888 or year > 2100:
                await message.answer("❌ Пожалуйста, введите корректный год (1888-2100).")
                await state.clear()
                return
            
            await message.answer(f"⏳ Ищу фильмы {year} года...")
            result = await kinopoisk_api.search_films_by_year(year=year)
        
        if 'error' in result:
            await message.answer(
                f"❌ Ошибка при поиске: {result.get('message', 'Неизвестная ошибка')}"
            )
            await state.clear()
            return
        
        films = result.get('items', [])
        
        if not films:
            await message.answer("😔 Фильмы за указанный период не найдены.")
            await state.clear()
            return
        
        response_text = f"🎬 Найдено фильмов: {result.get('total', len(films))}\n\n"
        
        for i, film in enumerate(films[:10], 1):
            name_ru = film.get('nameRu', 'Без названия')
            name_en = film.get('nameEn', '')
            year = film.get('year', '?')
            rating = film.get('rating', 'N/A')
            rating_kinopoisk = film.get('ratingKinopoisk', 'N/A')
            film_id = film.get('kinopoiskId', '')
            
            response_text += f"{i}. {name_ru}"
            if name_en:
                response_text += f" ({name_en})"
            response_text += f"\n   📅 Год: {year}"
            response_text += f"\n   ⭐ Рейтинг: {rating}"
            if rating_kinopoisk and rating_kinopoisk != 'null':
                response_text += f" | Кинопоиск: {rating_kinopoisk}"
            response_text += f"\n   🔗 ID: {film_id}\n\n"
        
        if len(films) > 10:
            response_text += f"\n... и еще {len(films) - 10} фильмов"
        
        await message.answer(response_text)
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректный год или диапазон лет (например: 2020 или 2010-2020)")


@router.message(Command("search_actor"))
async def cmd_search_actor(message: Message, state: FSMContext):
    """Обработчик команды /search_actor - поиск по актёру"""
    await message.answer(
        "🎭 Для поиска фильмов по актёру отправьте имя актёра.\n"
        "Например: Леонардо Ди Каприо"
    )
    await state.set_state(FilmSearchStates.waiting_for_actor_name)


@router.message(FilmSearchStates.waiting_for_actor_name)
async def process_actor_name(message: Message, state: FSMContext):
    """Обработчик ввода имени актёра"""
    if not message.text:
        await message.answer("❌ Пожалуйста, введите имя актёра.")
        return
    
    actor_name = message.text.strip()
    
    if not actor_name:
        await message.answer("❌ Пожалуйста, введите имя актёра.")
        return
    
    await message.answer(f"⏳ Ищу актёра '{actor_name}'...")
    
    # Сначала ищем персону по имени
    persons = await kinopoisk_api.search_person_by_name(actor_name)
    
    if not persons:
        await message.answer(f"😔 Актёр '{actor_name}' не найден.")
        await state.clear()
        return
    
    # Берем первую найденную персону
    person = persons[0]
    person_id = person.get('personId') or person.get('kinopoiskId')
    
    if not person_id:
        await message.answer("❌ Не удалось получить ID персоны.")
        await state.clear()
        return
    
    await message.answer(f"⏳ Ищу фильмы с участием '{actor_name}'...")
    
    # Ищем фильмы с участием актёра
    films_result = await kinopoisk_api.search_films_by_person(
        person_id=person_id,
        profession='ACTOR'
    )
    
    if 'error' in films_result:
        await message.answer(
            f"❌ Ошибка при поиске фильмов: {films_result.get('message', 'Неизвестная ошибка')}"
        )
        await state.clear()
        return
    
    films = films_result.get('items', [])
    
    if not films:
        await message.answer(f"😔 Фильмы с участием '{actor_name}' не найдены.")
        await state.clear()
        return
    
    response_text = f"🎬 Найдено фильмов с участием '{actor_name}': {films_result.get('total', len(films))}\n\n"
    
    for i, film in enumerate(films[:10], 1):
        # Структура данных может отличаться для фильмов персоны
        # Пробуем разные варианты полей
        film_data = film.get('film', {}) if 'film' in film else film
        
        name_ru = film_data.get('nameRu') or film_data.get('name', 'Без названия')
        name_en = film_data.get('nameEn') or ''
        year = film_data.get('year') or film_data.get('year', '?')
        rating = film_data.get('rating') or film_data.get('rating', 'N/A')
        rating_kinopoisk = film_data.get('ratingKinopoisk') or film_data.get('ratingKinopoisk', 'N/A')
        film_id = film_data.get('filmId') or film_data.get('kinopoiskId') or film.get('filmId', '')
        
        response_text += f"{i}. {name_ru}"
        if name_en:
            response_text += f" ({name_en})"
        response_text += f"\n   📅 Год: {year}"
        response_text += f"\n   ⭐ Рейтинг: {rating}"
        if rating_kinopoisk and str(rating_kinopoisk) != 'null' and str(rating_kinopoisk) != 'None':
            response_text += f" | Кинопоиск: {rating_kinopoisk}"
        response_text += f"\n   🔗 ID: {film_id}\n\n"
    
    if len(films) > 10:
        response_text += f"\n... и еще {len(films) - 10} фильмов"
    
    await message.answer(response_text)
    await state.clear()


@router.message(Command("search_director"))
async def cmd_search_director(message: Message, state: FSMContext):
    """Обработчик команды /search_director - поиск по режиссёру"""
    await message.answer(
        "🎬 Для поиска фильмов по режиссёру отправьте имя режиссёра.\n"
        "Например: Квентин Тарантино"
    )
    await state.set_state(FilmSearchStates.waiting_for_director_name)


@router.message(FilmSearchStates.waiting_for_director_name)
async def process_director_name(message: Message, state: FSMContext):
    """Обработчик ввода имени режиссёра"""
    if not message.text:
        await message.answer("❌ Пожалуйста, введите имя режиссёра.")
        return
    
    director_name = message.text.strip()
    
    if not director_name:
        await message.answer("❌ Пожалуйста, введите имя режиссёра.")
        return
    
    await message.answer(f"⏳ Ищу режиссёра '{director_name}'...")
    
    # Сначала ищем персону по имени
    persons = await kinopoisk_api.search_person_by_name(director_name)
    
    if not persons:
        await message.answer(f"😔 Режиссёр '{director_name}' не найден.")
        await state.clear()
        return
    
    # Берем первую найденную персону
    person = persons[0]
    person_id = person.get('personId') or person.get('kinopoiskId')
    
    if not person_id:
        await message.answer("❌ Не удалось получить ID персоны.")
        await state.clear()
        return
    
    await message.answer(f"⏳ Ищу фильмы режиссёра '{director_name}'...")
    
    # Ищем фильмы режиссёра
    films_result = await kinopoisk_api.search_films_by_person(
        person_id=person_id,
        profession='DIRECTOR'
    )
    
    if 'error' in films_result:
        await message.answer(
            f"❌ Ошибка при поиске фильмов: {films_result.get('message', 'Неизвестная ошибка')}"
        )
        await state.clear()
        return
    
    films = films_result.get('items', [])
    
    if not films:
        await message.answer(f"😔 Фильмы режиссёра '{director_name}' не найдены.")
        await state.clear()
        return
    
    response_text = f"🎬 Найдено фильмов режиссёра '{director_name}': {films_result.get('total', len(films))}\n\n"
    
    for i, film in enumerate(films[:10], 1):
        # Структура данных может отличаться для фильмов персоны
        # Пробуем разные варианты полей
        film_data = film.get('film', {}) if 'film' in film else film
        
        name_ru = film_data.get('nameRu') or film_data.get('name', 'Без названия')
        name_en = film_data.get('nameEn') or ''
        year = film_data.get('year') or film_data.get('year', '?')
        rating = film_data.get('rating') or film_data.get('rating', 'N/A')
        rating_kinopoisk = film_data.get('ratingKinopoisk') or film_data.get('ratingKinopoisk', 'N/A')
        film_id = film_data.get('filmId') or film_data.get('kinopoiskId') or film.get('filmId', '')
        
        response_text += f"{i}. {name_ru}"
        if name_en:
            response_text += f" ({name_en})"
        response_text += f"\n   📅 Год: {year}"
        response_text += f"\n   ⭐ Рейтинг: {rating}"
        if rating_kinopoisk and str(rating_kinopoisk) != 'null' and str(rating_kinopoisk) != 'None':
            response_text += f" | Кинопоиск: {rating_kinopoisk}"
        response_text += f"\n   🔗 ID: {film_id}\n\n"
    
    if len(films) > 10:
        response_text += f"\n... и еще {len(films) - 10} фильмов"
    
    await message.answer(response_text)
    await state.clear()


@router.message()
async def echo_handler(message: Message):
    """Обработчик всех остальных сообщений"""
    await message.answer(
        "🤔 Я не понимаю эту команду. Используйте /help для списка доступных команд."
    )

