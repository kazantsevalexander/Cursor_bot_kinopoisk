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


# --- Вспомогательная функция для форматирования ответа ---
def format_film_list(films: list, title: str) -> str:
    if not films:
        return "😔 Фильмы не найдены."

    total = len(films)
    response_text = f"{title} (показано {min(10, total)} из {total}):\n\n"

    for i, film in enumerate(films[:10], 1):
        name_ru = film.get('nameRu') or film.get('nameOriginal') or 'Без названия'
        name_en = film.get('nameEn') or ''
        year = film.get('year')
        # Обработка разных форматов рейтинга
        rating = film.get('rating') or film.get('ratingKinopoisk') or 'N/A'
        if rating == 'null': rating = 'N/A'

        film_id = film.get('kinopoiskId') or film.get('filmId')

        response_text += f"{i}. <b>{name_ru}</b>"
        if name_en:
            response_text += f" ({name_en})"
        if year and year != 'null':
            response_text += f"\n   📅 Год: {year}"
        response_text += f"\n   ⭐ Рейтинг: {rating}"
        response_text += f"\n   🔗 ID: {film_id}\n\n"

    return response_text


@router.message(Command("start"))
async def cmd_start(message: Message):
    welcome_text = (
        "🎬 <b>Бот Кинопоиска</b>\n\n"
        "Команды:\n"
        "/genres - Список жанров\n"
        "/search - Поиск по жанру\n"
        "/search_genres - Поиск по нескольким жанрам\n"
        "/search_year - Поиск по году\n"
        "/search_actor - Поиск по актёру\n"
        "/search_director - Поиск по режиссёру"
    )
    await message.answer(welcome_text)


@router.message(Command("help"))
async def cmd_help(message: Message):
    help_text = (
        "📖 <b>Справка:</b>\n\n"
        "• /search_genres - введите ID жанров через запятую (напр: 1,2)\n"
        "• /search_year - год (2020) или интервал (2010-2015)\n"
        "• /search_actor - имя актера (напр: Брэд Питт)\n"
    )
    await message.answer(help_text)


@router.message(Command("genres"))
async def cmd_genres(message: Message):
    await message.answer("⏳ Загружаю жанры...")
    genres = await kinopoisk_api.get_genres()

    if not genres:
        await message.answer("❌ Ошибка загрузки жанров.")
        return

    builder = InlineKeyboardBuilder()
    # Показываем популярные жанры первыми (обычно они в начале списка)
    for genre in genres[:20]:
        builder.button(text=genre['genre'], callback_data=f"genre_{genre['id']}")
    builder.adjust(2)

    text = "🎭 <b>Выберите жанр</b> или используйте ID для команды /search_genres:\n\n"
    text += "\n".join([f"🆔 <code>{g['id']}</code> - {g['genre']}" for g in genres[:20]])

    await message.answer(text, reply_markup=builder.as_markup())


# --- Поиск по одному жанру ---
@router.message(Command("search"))
async def cmd_search(message: Message, state: FSMContext):
    await message.answer("👇 Выберите жанр через /genres или введите ID жанра:")
    await state.set_state(FilmSearchStates.waiting_for_genre)


@router.callback_query(F.data.startswith("genre_"))
async def process_genre_callback(callback: CallbackQuery):
    genre_id = int(callback.data.split("_")[1])
    await callback.message.answer(f"⏳ Ищу фильмы (ID жанра: {genre_id})...")

    result = await kinopoisk_api.search_films_by_genre(genre_id)
    if 'error' in result:
        await callback.message.answer(f"❌ Ошибка: {result.get('message')}")
        return

    await callback.message.answer(format_film_list(result.get('items', []), "🎬 Результаты поиска"))
    await callback.answer()


@router.message(FilmSearchStates.waiting_for_genre)
async def process_genre_text(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Введите числовой ID.")
        return

    await message.answer(f"⏳ Ищу фильмы...")
    result = await kinopoisk_api.search_films_by_genre(int(message.text))
    await message.answer(format_film_list(result.get('items', []), "🎬 Результаты поиска"))
    await state.clear()


# --- Поиск по нескольким жанрам ---
@router.message(Command("search_genres"))
async def cmd_search_genres(message: Message, state: FSMContext):
    await message.answer("🎭 Введите ID жанров через запятую (например: 1, 6):")
    await state.set_state(FilmSearchStates.waiting_for_multiple_genres)


@router.message(FilmSearchStates.waiting_for_multiple_genres)
async def process_multiple_genres(message: Message, state: FSMContext):
    try:
        ids = [int(x.strip()) for x in message.text.split(',') if x.strip().isdigit()]
        if not ids:
            raise ValueError

        await message.answer(f"⏳ Ищу фильмы по жанрам: {ids}...")
        result = await kinopoisk_api.search_films_by_multiple_genres(ids)

        await message.answer(format_film_list(result.get('items', []), "🎬 Результаты поиска"))
        await state.clear()
    except ValueError:
        await message.answer("❌ Некорректный формат. Введите числа через запятую.")


# --- Поиск по году ---
@router.message(Command("search_year"))
async def cmd_search_year(message: Message, state: FSMContext):
    await message.answer("📅 Введите год (2020) или интервал (2010-2020):")
    await state.set_state(FilmSearchStates.waiting_for_year)


@router.message(FilmSearchStates.waiting_for_year)
async def process_year(message: Message, state: FSMContext):
    text = message.text.strip()
    year, y_from, y_to = None, None, None

    try:
        if '-' in text:
            parts = text.split('-')
            if parts[0]: y_from = int(parts[0])
            if parts[1]: y_to = int(parts[1])
        else:
            year = int(text)

        await message.answer("⏳ Ищу фильмы...")
        result = await kinopoisk_api.search_films_by_year(year, y_from, y_to)

        await message.answer(format_film_list(result.get('items', []), "🎬 Фильмы по году"))
        await state.clear()
    except ValueError:
        await message.answer("❌ Некорректный год.")


# --- Поиск по Актёру / Режиссёру ---
async def process_person_search(message: Message, state: FSMContext, profession: str):
    name = message.text.strip()
    await message.answer(f"⏳ Ищу персону '{name}'...")

    # 1. Ищем ID персоны
    persons = await kinopoisk_api.search_person_by_name(name)
    if not persons:
        await message.answer("❌ Персона не найдена.")
        await state.clear()
        return

    person = persons[0]  # Берем первого совпавшего
    pid = person.get('kinopoiskId') or person.get('personId')
    p_name = person.get('nameRu') or person.get('nameEn')

    await message.answer(f"👤 Найдена персона: <b>{p_name}</b>. Ищу фильмы...")

    # 2. Ищем фильмы персоны
    result = await kinopoisk_api.search_films_by_person(pid, profession)

    if 'error' in result:
        await message.answer(f"❌ Ошибка API: {result.get('message')}")
    else:
        role = "Актёр" if profession == 'ACTOR' else "Режиссёр"
        await message.answer(format_film_list(result.get('items', []), f"🎬 Фильмография ({role})"))

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