import asyncio
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
    waiting_for_genre = State()
    waiting_for_multiple_genres = State()
    waiting_for_year = State()
    waiting_for_actor_name = State()
    waiting_for_director_name = State()
    waiting_for_film_name = State()


# --- ФУНКЦИЯ ОТПРАВКИ РЕЗУЛЬТАТОВ (ОБНОВЛЕННАЯ) ---
async def send_film_results(message: Message, films: list, title: str):
    if not films:
        await message.answer("😔 Фильмы не найдены.")
        return

    await message.answer(f"{title} (Топ результатов):")

    top_films = films[:5]

    for film in top_films:
        name_ru = film.get('nameRu') or film.get('nameOriginal') or 'Без названия'
        name_en = film.get('nameEn') or ''
        year = film.get('year')
        rating = film.get('rating') or film.get('ratingKinopoisk') or 'N/A'
        if rating == 'null': rating = 'N/A'
        film_id = film.get('kinopoiskId') or film.get('filmId')

        # --- 1. ОБРАБОТКА СТРАН ---
        countries_list = film.get('countries', [])
        # Собираем названия стран в строку через запятую (берем первые 3, чтобы не было слишком длинно)
        if countries_list:
            countries_str = ", ".join([c.get('country', '') for c in countries_list[:3]])
        else:
            countries_str = "Не указано"

        # --- 2. ФОРМИРОВАНИЕ ССЫЛКИ ---
        kp_link = f"https://www.kinopoisk.ru/film/{film_id}/"

        # Постер
        poster_url = film.get('posterUrlPreview') or film.get('posterUrl')

        en_text = f"🇬🇧 {name_en}\n" if name_en else ""

        # --- ОБНОВЛЕННАЯ ПОДПИСЬ ---
        caption = (
            f"🎬 <b>{name_ru}</b>\n"
            f"{en_text}"
            f"🌍 Страна: {countries_str}\n"
            f"📅 Год: {year}\n"
            f"⭐ Рейтинг: {rating}\n"
            f"🔗 <a href='{kp_link}'>Перейти на Кинопоиск</a>"
        )

        try:
            if poster_url:
                await message.answer_photo(photo=poster_url, caption=caption)
            else:
                await message.answer(caption)
        except Exception:
            await message.answer(caption)

        await asyncio.sleep(0.3)

    # Список остальных фильмов (текстовый)
    if len(films) > 5:
        remaining = films[5:15]
        text_list = "<b>⬇️ Другие фильмы по запросу:</b>\n\n"
        for i, film in enumerate(remaining, 6):
            name = film.get('nameRu') or film.get('nameOriginal')
            year = film.get('year')
            f_id = film.get('kinopoiskId') or film.get('filmId')
            # Добавляем ссылку и в текстовый список
            link = f"https://www.kinopoisk.ru/film/{f_id}/"

            text_list += f"{i}. <a href='{link}'>{name}</a> ({year})\n"

        # Отключаем предпросмотр ссылок, чтобы не спамить мини-картинками в текстовом списке
        await message.answer(text_list, disable_web_page_preview=True)


# --- ОБРАБОТЧИКИ КОМАНД ---

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "🎬 <b>Кинопоиск Бот</b>\n\n"
        "🔍 <b>/search_film - Поиск по названию</b>\n"
        "🎭 /genres - Выбрать жанр\n"
        "📅 /search_year - Поиск по году\n"
        "👤 /search_actor - Поиск по актёру\n"
        "🎥 /search_director - Поиск по режиссёру"
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer("Просто выберите команду из меню и следуйте инструкциям.")


@router.message(Command("genres"))
async def cmd_genres(message: Message):
    await message.answer("⏳ Загружаю жанры...")
    genres = await kinopoisk_api.get_genres()
    if not genres:
        await message.answer("❌ Ошибка API")
        return

    builder = InlineKeyboardBuilder()
    for genre in genres[:20]:
        builder.button(text=genre['genre'], callback_data=f"genre_{genre['id']}")
    builder.adjust(2)

    await message.answer("🎭 Выберите жанр:", reply_markup=builder.as_markup())


@router.message(Command("search"))
async def cmd_search(message: Message, state: FSMContext):
    await message.answer("👇 Выберите жанр через /genres")
    await state.set_state(FilmSearchStates.waiting_for_genre)


@router.callback_query(F.data.startswith("genre_"))
async def process_genre_callback(callback: CallbackQuery):
    genre_id = int(callback.data.split("_")[1])
    await callback.message.answer(f"⏳ Ищу лучшие фильмы этого жанра...")
    result = await kinopoisk_api.search_films_by_genre(genre_id)
    await send_film_results(callback.message, result.get('items', []), "🎭 Результаты по жанру")
    await callback.answer()


@router.message(Command("search_genres"))
async def cmd_search_genres(message: Message, state: FSMContext):
    await message.answer("✍️ Введите ID жанров через запятую (например: 1, 6):")
    await state.set_state(FilmSearchStates.waiting_for_multiple_genres)


@router.message(FilmSearchStates.waiting_for_multiple_genres)
async def process_multiple_genres(message: Message, state: FSMContext):
    try:
        ids = [int(x.strip()) for x in message.text.split(',') if x.strip().isdigit()]
        if not ids: raise ValueError
        await message.answer(f"⏳ Ищу фильмы...")
        result = await kinopoisk_api.search_films_by_multiple_genres(ids)
        await send_film_results(message, result.get('items', []), "🎭 Результаты поиска")
        await state.clear()
    except ValueError:
        await message.answer("❌ Введите числа через запятую.")


@router.message(Command("search_year"))
async def cmd_search_year(message: Message, state: FSMContext):
    await message.answer("📅 Введите год (2023) или интервал (2010-2015):")
    await state.set_state(FilmSearchStates.waiting_for_year)


@router.message(FilmSearchStates.waiting_for_year)
async def process_year(message: Message, state: FSMContext):
    text = message.text.strip()
    year, y_from, y_to = None, None, None
    try:
        if '-' in text:
            parts = text.split('-')
            y_from, y_to = int(parts[0]), int(parts[1])
        else:
            year = int(text)
        await message.answer("⏳ Ищу фильмы...")
        result = await kinopoisk_api.search_films_by_year(year, y_from, y_to)
        await send_film_results(message, result.get('items', []), "📅 Фильмы по году")
        await state.clear()
    except ValueError:
        await message.answer("❌ Некорректный формат.")


# --- ПОИСК ПО ПЕРСОНЕ ---
async def process_person_search(message: Message, state: FSMContext, profession: str):
    name = message.text.strip()
    await message.answer(f"⏳ Ищу: {name}...")

    persons = await kinopoisk_api.search_person_by_name(name)
    if not persons:
        await message.answer("❌ Персона не найдена.")
        await state.clear()
        return

    person = persons[0]
    pid = person.get('kinopoiskId') or person.get('personId')
    p_name = person.get('nameRu') or person.get('nameEn')

    await message.answer(f"👤 Найдена персона: <b>{p_name}</b>. Загружаю фильмографию...")

    # 1. Получаем список фильмов
    result = await kinopoisk_api.search_films_by_person(pid, profession)

    if 'error' in result:
        await message.answer("❌ Ошибка API")
        await state.clear()
        return

    films = result.get('items', [])

    if not films:
        await message.answer("😔 Фильмы не найдены.")
        await state.clear()
        return

    # 2. Берем топ-5 фильмов и подгружаем для них детали (страны, постеры)
    await message.answer("⏳ Подгружаю детали для лучших фильмов...")

    top_5_films = films[:5]
    remaining_films = films[5:]

    tasks = []
    for film in top_5_films:
        fid = film.get('filmId') or film.get('kinopoiskId')
        tasks.append(kinopoisk_api.get_film_details(fid))

    details_results = await asyncio.gather(*tasks)

    enriched_top_5 = []
    for original, details in zip(top_5_films, details_results):
        if 'error' not in details:
            enriched_top_5.append(details)
        else:
            enriched_top_5.append(original)

    final_list = enriched_top_5 + remaining_films

    role = "Актёр" if profession == 'ACTOR' else "Режиссёр"
    await send_film_results(message, final_list, f"🎬 Фильмография ({role})")

    await state.clear()


@router.message(Command("search_actor"))
async def cmd_actor(message: Message, state: FSMContext):
    await message.answer("🎭 Введите имя актёра:")
    await state.set_state(FilmSearchStates.waiting_for_actor_name)


@router.message(FilmSearchStates.waiting_for_actor_name)
async def process_actor(message: Message, state: FSMContext):
    await process_person_search(message, state, 'ACTOR')


@router.message(Command("search_director"))
async def cmd_director(message: Message, state: FSMContext):
    await message.answer("🎬 Введите имя режиссёра:")
    await state.set_state(FilmSearchStates.waiting_for_director_name)


@router.message(FilmSearchStates.waiting_for_director_name)
async def process_director(message: Message, state: FSMContext):
    await process_person_search(message, state, 'DIRECTOR')


@router.message(Command("search_film"))
async def cmd_search_film(message: Message, state: FSMContext):
    await message.answer("🔎 Введите название фильма или сериала:")
    await state.set_state(FilmSearchStates.waiting_for_film_name)


@router.message(FilmSearchStates.waiting_for_film_name)
async def process_film_name(message: Message, state: FSMContext):
    film_name = message.text.strip()

    if not film_name:
        await message.answer("❌ Пожалуйста, введите название.")
        return

    await message.answer(f"⏳ Ищу «{film_name}»...")

    result = await kinopoisk_api.search_films_by_keyword(film_name)

    if 'error' in result:
        await message.answer(f"❌ Ошибка API: {result.get('message')}")
        await state.clear()
        return

    films = result.get('items', [])
    await send_film_results(message, films, f"🔎 Результаты поиска по запросу «{film_name}»")

    await state.clear()