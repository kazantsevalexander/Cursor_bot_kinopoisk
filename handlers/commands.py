import asyncio
import random
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services.kinopoisk_api import KinopoiskAPI
from services import db
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
    waiting_for_country = State()


# --- ГЛАВНОЕ МЕНЮ (КНОПКИ ВНИЗУ) ---
def get_main_menu():
    kb = [
        [KeyboardButton(text="🔎 Поиск фильма"), KeyboardButton(text="🎲 Рекомендация")],
        [KeyboardButton(text="🎭 Жанры"), KeyboardButton(text="📅 По годам")],
        [KeyboardButton(text="👁 Мои фильмы"), KeyboardButton(text="👤 Мой профиль")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


# --- КНОПКИ ПОД ФИЛЬМОМ ---
def get_film_keyboard(film_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="👁 Просмотрено", callback_data=f"act_watched_{film_id}")
    builder.button(text="🔖 В планы", callback_data=f"act_plan_{film_id}")
    builder.button(text="👎 Скрыть", callback_data=f"act_ignore_{film_id}")
    builder.adjust(2, 1)
    return builder.as_markup()


# --- ОТПРАВКА РЕЗУЛЬТАТОВ ---
async def send_film_results(message: Message, films: list, title: str, user_id: int):
    if not films:
        await message.answer("😔 Ничего не найдено.", reply_markup=get_main_menu())
        return

    excluded_ids = await db.get_user_excluded_ids(user_id)
    filtered_films = [f for f in films if (f.get('kinopoiskId') or f.get('filmId')) not in excluded_ids]

    if not filtered_films:
        await message.answer(f"{title}\n\n🎉 Вы уже видели все фильмы из этого списка!", reply_markup=get_main_menu())
        return

    if title:
        await message.answer(f"{title} (Топ результатов):", reply_markup=get_main_menu())

    top_films = filtered_films[:5]
    director_tasks = [kinopoisk_api.get_directors(f.get('kinopoiskId') or f.get('filmId')) for f in top_films]
    directors_list = await asyncio.gather(*director_tasks)

    for film, director_name in zip(top_films, directors_list):
        name_ru = film.get('nameRu') or film.get('nameOriginal') or 'Без названия'
        year = film.get('year') or ''
        rating = film.get('rating') or film.get('ratingKinopoisk') or 'N/A'
        if rating == 'null': rating = 'N/A'
        film_id = film.get('kinopoiskId') or film.get('filmId')

        genres = ", ".join([g.get('genre', '') for g in film.get('genres', [])[:2]]).capitalize()
        countries = ", ".join([c.get('country', '') for c in film.get('countries', [])[:2]])
        poster = film.get('posterUrlPreview') or film.get('posterUrl')
        kp_link = f"https://www.kinopoisk.ru/film/{film_id}/"

        caption = (
            f"🎬 <b>{name_ru}</b> ({year})\n"
            f"⭐ {rating} | 🎭 {genres}\n"
            f"🎥 {director_name} | 🌍 {countries}\n"
            f"🔗 <a href='{kp_link}'>Кинопоиск</a>"
        )

        try:
            if poster:
                await message.answer_photo(poster, caption=caption, reply_markup=get_film_keyboard(film_id))
            else:
                await message.answer(caption, reply_markup=get_film_keyboard(film_id))
        except Exception:
            await message.answer(caption, reply_markup=get_film_keyboard(film_id))

        await asyncio.sleep(0.3)

    if len(filtered_films) > 5:
        text_list = "<b>⬇️ Ещё варианты (нажмите для карточки):</b>\n\n"
        for i, film in enumerate(filtered_films[5:15], 6):
            name = film.get('nameRu') or film.get('nameOriginal')
            year = film.get('year') or '?'
            fid = film.get('kinopoiskId') or film.get('filmId')
            text_list += f"{i}. /film_{fid} — {name} ({year})\n"
        await message.answer(text_list)


# --- ОБРАБОТКА ТЕКСТОВЫХ КНОПОК МЕНЮ ---
@router.message(F.text == "🔎 Поиск фильма")
async def menu_search(message: Message, state: FSMContext):
    await cmd_search_film(message, state)


@router.message(F.text == "🎲 Рекомендация")
async def menu_recommend(message: Message, state: FSMContext):
    await cmd_recommend(message, state)


@router.message(F.text == "🎭 Жанры")
async def menu_genres(message: Message, state: FSMContext):
    await cmd_genres(message, state)


@router.message(F.text == "📅 По годам")
async def menu_years(message: Message, state: FSMContext):
    await cmd_search_year(message, state)


@router.message(F.text == "👁 Мои фильмы")
async def menu_lists(message: Message, state: FSMContext):
    await cmd_my_watched(message, state)


@router.message(F.text == "👤 Мой профиль")
async def menu_profile(message: Message, state: FSMContext):
    user_id = message.from_user.id
    watched, plan = await db.get_user_stats(user_id)
    genres = await db.get_user_genres(user_id)

    text = (
        f"👤 <b>Ваш профиль</b>\n\n"
        f"👁 Просмотрено: <b>{watched}</b>\n"
        f"🔖 В планах: <b>{plan}</b>\n"
        f"🎭 Любимые жанры (ID): {genres if genres else 'Не выбраны'}\n\n"
        f"<i>Бот обучается, когда вы ищете жанры или отмечаете фильмы.</i>"
    )
    await message.answer(text, reply_markup=get_main_menu())


# --- КОМАНДЫ ---
@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await db.add_user(message.from_user.id)
    await message.answer(
        "👋 Привет! Я помогу найти фильм.\n"
        "Используй кнопки внизу экрана 👇",
        reply_markup=get_main_menu()
    )

@router.message(Command("help"))
async def cmd_help(message: Message, state: FSMContext):
    await state.clear()
    help_text = (
        "📖 <b>Справочник по Кинопоиск Боту</b>\n\n"

        "🔍 <b>ПОИСК ФИЛЬМОВ</b>\n"
        "• /search_film — Поиск по названию (сериалы тоже ищет)\n"
        "• /genres — Выбор жанра (кнопками или по ID)\n"
        "• /search_year — Поиск по году (например: <i>2023</i>) или интервалу (<i>2010-2015</i>)\n"
        "• /countries — Поиск по стране (США, Франция, Корея и др.)\n"
        "• /search_actor — Фильмография актёра\n"
        "• /search_director — Фильмография режиссёра\n\n"

        "🧠 <b>УМНЫЕ РЕКОМЕНДАЦИИ</b>\n"
        "• /recommend — <b>Мне повезет!</b> Бот проанализирует ваш список просмотренного и предложит похожие фильмы. Если список пуст — предложит что-то из ваших любимых жанров.\n"
        "• /save_genres — Настроить любимые жанры (для работы рекомендаций с нуля).\n\n"

        "👤 <b>ЛИЧНАЯ КОЛЛЕКЦИЯ</b>\n"
        "• /my_watched — Список просмотренного\n"
        "• /my_plan — Список «Буду смотреть»\n\n"

        "⚙️ <b>КАК ПОЛЬЗОВАТЬСЯ</b>\n"
        "Под каждым фильмом есть кнопки:\n"
        "👁 <b>Просмотрено</b> — добавляет в список и учитывает в рекомендациях.\n"
        "🔖 <b>Буду смотреть</b> — откладывает на потом.\n"
        "👎 <b>Не интересно</b> — скрывает фильм из ленты и больше никогда его не предложит.\n\n"

        "<i>💡 Совет: Если вы видите в списке команду вида /film_12345, нажмите на неё, чтобы открыть подробную карточку фильма.</i>"
    )
    await message.answer(help_text)
    
@router.message(Command("genres"))
async def cmd_genres(message: Message, state: FSMContext):
    await state.clear()
    genres = await kinopoisk_api.get_genres()
    if not genres: return
    builder = InlineKeyboardBuilder()
    for genre in genres[:20]:
        builder.button(text=genre['genre'], callback_data=f"genre_{genre['id']}")
    builder.adjust(2)
    await message.answer("🎭 Выберите жанр:", reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("genre_"))
async def process_genre_callback(callback: CallbackQuery):
    genre_id = int(callback.data.split("_")[1])
    # АВТОМАТИЧЕСКОЕ ЗАПОМИНАНИЕ ЖАНРА
    await db.update_user_genres(callback.from_user.id, genre_id)

    await callback.message.answer(f"✅ Жанр запомнил! Ищу фильмы...")
    result = await kinopoisk_api.search_films_by_genre(genre_id)
    await send_film_results(callback.message, result.get('items', []), "🎭 Результаты", callback.from_user.id)
    await callback.answer()


@router.message(Command("recommend"))
async def cmd_recommend(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    await message.answer("🤔 Анализирую ваши вкусы...")

    # 1. Похожие на просмотренные
    for _ in range(3):
        watched = await db.get_random_watched_film(user_id)
        if watched:
            similars = await kinopoisk_api.get_similars(watched[0])
            if similars:
                await message.answer(f"💡 Так как вы смотрели <b>«{watched[1]}»</b>:")
                # Подгружаем детали для топ-3
                tasks = [kinopoisk_api.get_film_details(f.get('filmId')) for f in similars[:3]]
                full = await asyncio.gather(*tasks)
                valid = [f for f in full if 'error' not in f]
                await send_film_results(message, valid, "", user_id)
                return

    # 2. По жанрам
    genres_str = await db.get_user_genres(user_id)
    if genres_str:
        g_ids = [int(g) for g in genres_str.split(',')]
        target = random.choice(g_ids)
        res = await kinopoisk_api.search_films_by_genre(target, page=random.randint(1, 3))
        await send_film_results(message, res.get('items', []), "🎲 Рекомендация по вашим жанрам", user_id)
        return

    await message.answer(
        "😔 Я пока мало о вас знаю.\nОтметьте фильмы как «Просмотрено» или просто поищите фильмы по жанрам!",
        reply_markup=get_main_menu())


@router.message(Command("search_film"))
async def cmd_search_film(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🔎 Введите название фильма:")
    await state.set_state(FilmSearchStates.waiting_for_film_name)


@router.message(FilmSearchStates.waiting_for_film_name)
async def process_film_name(message: Message, state: FSMContext):
    name = message.text.strip()
    res = await kinopoisk_api.search_films_by_keyword(name)
    await send_film_results(message, res.get('items', []), f"🔎 Поиск: {name}", message.from_user.id)
    await state.clear()


@router.message(Command("search_year"))
async def cmd_search_year(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("📅 Введите год (например: 2023):")
    await state.set_state(FilmSearchStates.waiting_for_year)


@router.message(FilmSearchStates.waiting_for_year)
async def process_year(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Введите число.")
        return
    res = await kinopoisk_api.search_films_by_year(int(message.text))
    await send_film_results(message, res.get('items', []), f"📅 Фильмы {message.text} года", message.from_user.id)
    await state.clear()


@router.message(Command("my_watched"))
async def cmd_my_watched(message: Message, state: FSMContext):
    await state.clear()
    films = await db.get_user_films_full(message.from_user.id, 'watched')
    if not films:
        await message.answer("Список пуст.", reply_markup=get_main_menu())
        return
    text = "👁 <b>Просмотрено:</b>\n\n" + "\n".join([f"• /film_{fid} — {t}" for t, fid in films])
    await message.answer(text, reply_markup=get_main_menu())


@router.message(F.text.regexp(r"^/film_(\d+)$"))
async def show_one_film(message: Message, state: FSMContext):
    await state.clear()
    fid = int(message.text.split('_')[1])
    film = await kinopoisk_api.get_film_details(fid)
    if 'error' not in film:
        await send_film_results(message, [film], "", message.from_user.id)
    else:
        await message.answer("❌ Ошибка загрузки")


@router.callback_query(F.data.startswith("act_"))
async def process_film_action(callback: CallbackQuery):
    _, action, fid = callback.data.split("_")
    fid = int(fid)
    uid = callback.from_user.id

    # Получаем название
    try:
        det = await kinopoisk_api.get_film_details(fid)
        title = det.get('nameRu') or det.get('nameOriginal') or 'Фильм'
    except:
        title = 'Фильм'

    if action == 'watched':
        await db.add_film_to_list(uid, fid, title, 'watched')
        await callback.answer("✅ В просмотренные")
    elif action == 'plan':
        await db.add_film_to_list(uid, fid, title, 'plan')
        await callback.answer("🔖 В планы")
    elif action == 'ignore':
        await db.add_film_to_list(uid, fid, title, 'ignored')
        await callback.answer()
        try:
            await callback.message.delete()
        except:
            pass