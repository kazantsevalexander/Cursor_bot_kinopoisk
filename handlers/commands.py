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


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    welcome_text = (
        "🎬 Добро пожаловать в бота Кинопоиска!\n\n"
        "Доступные команды:\n"
        "/genres - Получить список жанров\n"
        "/search - Поиск фильмов по жанру\n"
        "/help - Справка"
    )
    await message.answer(welcome_text)


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    help_text = (
        "📖 Справка по использованию бота:\n\n"
        "/genres - Показывает список всех доступных жанров\n"
        "/search - Запускает поиск фильмов по жанру\n\n"
        "После выбора жанра бот покажет список фильмов с рейтингом и описанием."
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


@router.message()
async def echo_handler(message: Message):
    """Обработчик всех остальных сообщений"""
    await message.answer(
        "🤔 Я не понимаю эту команду. Используйте /help для списка доступных команд."
    )

