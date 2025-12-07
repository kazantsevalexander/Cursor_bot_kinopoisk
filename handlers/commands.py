import asyncio
import random
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
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


# --- КЛАВИАТУРА (Единая для всех) ---
def get_film_keyboard(film_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="👁 Просмотрено", callback_data=f"act_watched_{film_id}")
    builder.button(text="🔖 Буду смотреть", callback_data=f"act_plan_{film_id}")
    builder.button(text="👎 Не интересно", callback_data=f"act_ignore_{film_id}")
    builder.adjust(2, 1)
    return builder.as_markup()


# --- УНИВЕРСАЛЬНАЯ ФУНКЦИЯ ОТПРАВКИ ---
async def send_film_results(message: Message, films: list, title: str, user_id: int):
    """
    Эта функция используется ВСЕМИ обработчиками поиска.
    Она гарантирует, что везде будут кнопки и правильные ссылки.
    """
    if not films:
        await message.answer("😔 Фильмы не найдены.")
        return

    # Фильтрация (исключаем скрытые)
    # Если список состоит из 1 фильма (открыли карточку), фильтрацию не делаем
    is_single_view = len(films) == 1

    if not is_single_view:
        excluded_ids = await db.get_user_excluded_ids(user_id)
        filtered_films = []
        for f in films:
            fid = f.get('kinopoiskId') or f.get('filmId')
            if fid and fid not in excluded_ids:
                filtered_films.append(f)
    else:
        filtered_films = films

    if not filtered_films and not is_single_view:
        await message.answer(f"{title}\n\n🎉 Все фильмы из этой выборки вы уже видели или скрыли!")
        return

    if title:
        await message.answer(f"{title} (Топ результатов):")

    top_films = filtered_films[:5]

    # Загружаем режиссеров для топ-5
    director_tasks = []
    for f in top_films:
        fid = f.get('kinopoiskId') or f.get('filmId')
        if fid:
            director_tasks.append(kinopoisk_api.get_directors(fid))
        else:
            # Если вдруг ID нет, добавляем заглушку, чтобы порядок не сбился
            director_tasks.append(asyncio.sleep(0, result="Не указано"))

    directors_list = await asyncio.gather(*director_tasks)

    # --- ЦИКЛ ВЫВОДА КАРТОЧЕК ---
    for film, director_name in zip(top_films, directors_list):
        film_id = film.get('kinopoiskId') or film.get('filmId')

        if not film_id: continue  # Пропускаем битые данные

        name_ru = film.get('nameRu') or film.get('nameOriginal') or 'Без названия'
        name_en = film.get('nameEn') or ''
        year = film.get('year')
        rating = film.get('rating') or film.get('ratingKinopoisk') or 'N/A'
        if rating == 'null': rating = 'N/A'

        # Жанры
        genres_list = film.get('genres', [])
        genres_str = ", ".join(
            [g.get('genre', '') for g in genres_list[:3]]).capitalize() if genres_list else "Не указано"

        # Страны
        countries_list = film.get('countries', [])
        countries_str = ", ".join(
            [c.get('country', '') for c in countries_list[:3]]) if countries_list else "Не указано"

        # Возраст
        age_limit = film.get('ratingAgeLimits')
        age_str = f" | {age_limit.replace('age', '')}+" if age_limit else ""

        kp_link = f"https://www.kinopoisk.ru/film/{film_id}/"
        poster_url = film.get('posterUrlPreview') or film.get('posterUrl')
        en_text = f"🇬🇧 {name_en}\n" if name_en else ""

        caption = (
            f"🎬 <b>{name_ru}</b>{age_str}\n"
            f"{en_text}"
            f"🎭 Жанр: {genres_str}\n"
            f"🎥 Режиссёр: {director_name}\n"
            f"🌍 Страна: {countries_str}\n"
            f"📅 Год: {year}\n"
            f"⭐ Рейтинг: {rating}\n"
            f"🔗 <a href='{kp_link}'>Перейти на Кинопоиск</a>"
        )

        # !!! ГЛАВНОЕ: ДОБАВЛЯЕМ КНОПКИ !!!
        keyboard = get_film_keyboard(film_id)

        try:
            if poster_url:
                await message.answer_photo(photo=poster_url, caption=caption, reply_markup=keyboard)
            else:
                await message.answer(caption, reply_markup=keyboard)
        except Exception:
            await message.answer(caption, reply_markup=keyboard)

        await asyncio.sleep(0.3)

    # --- СПИСОК ОСТАЛЬНЫХ (С КОМАНДАМИ /film_ID) ---
    if len(filtered_films) > 5:
        remaining = filtered_films[5:15]
        text_list = "<b>⬇️ Нажмите на команду, чтобы открыть карточку:</b>\n\n"
        for i, film in enumerate(remaining, 6):
            name = film.get('nameRu') or film.get('nameOriginal')
            year = film.get('year') or '?'
            f_id = film.get('kinopoiskId') or film.get('filmId')

            # !!! ГЛАВНОЕ: ВНУТРЕННЯЯ ССЫЛКА !!!
            text_list += f"{i}. /film_{f_id} — <b>{name}</b> ({year})\n"

        await message.answer(text_list)


# --- ОБРАБОТЧИК ОТКРЫТИЯ КАРТОЧКИ (/film_ID) ---
@router.message(F.text.regexp(r"^/film_(\d+)$"))
async def show_one_film(message: Message, state: FSMContext):
    await state.clear()
    try:
        film_id = int(message.text.split('_')[1])
        await message.answer("⏳ Загружаю информацию...")

        film = await kinopoisk_api.get_film_details(film_id)
        if 'error' in film:
            await message.answer("❌ Не удалось загрузить информацию.")
            return

        # Вызываем ту же функцию, она добавит кнопки!
        await send_film_results(message, [film], "", message.from_user.id)

    except Exception as e:
        print(f"Error showing film: {e}")
        await message.answer("❌ Ошибка.")


# --- ОБРАБОТЧИКИ ДЕЙСТВИЙ (КНОПКИ) ---
@router.callback_query(F.data.startswith("act_"))
async def process_film_action(callback: CallbackQuery):
    try:
        _, action_type, film_id_str = callback.data.split("_")
        film_id = int(film_id_str)
        user_id = callback.from_user.id

        try:
            details = await kinopoisk_api.get_film_details(film_id)
            title = details.get('nameRu') or details.get('nameOriginal') or 'Фильм'
        except:
            title = 'Фильм'

        if action_type == 'watched':
            await db.add_film_to_list(user_id, film_id, title, 'watched')
            await callback.answer(f"✅ Добавлено в просмотренные")
        elif action_type == 'plan':
            await db.add_film_to_list(user_id, film_id, title, 'plan')
            await callback.answer(f"🔖 Добавлено в планы")
        elif action_type == 'ignore':
            await db.add_film_to_list(user_id, film_id, title, 'ignored')
            await callback.answer()
            try:
                await callback.message.delete()
            except:
                await callback.message.edit_reply_markup(reply_markup=None)
    except Exception as e:
        print(f"Error: {e}")
        await callback.answer()


# --- КОМАНДЫ ---

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await db.add_user(message.from_user.id)
    await message.answer(
        "🎬 <b>Кинопоиск Бот: Полная версия</b>\n\n"
        "<b>🔎 Поиск:</b>\n"
        "/search_film - По названию\n"
        "/genres - По жанру\n"
        "/search_year - По году\n"
        "/countries - По стране\n"
        "/search_actor - По актёру\n"
        "/search_director - По режиссёру\n\n"
        "<b>👤 Личное:</b>\n"
        "/recommend - <b>Мне повезет</b>\n"
        "/my_watched - Список просмотренного\n"
        "/my_plan - Буду смотреть\n"
        "/save_genres - Настроить вкусы"
    )


@router.message(Command("help"))
async def cmd_help(message: Message, state: FSMContext):
    await state.clear()
    help_text = (
        "📖 <b>Справочник</b>\n\n"
        "🔍 <b>ПОИСК</b>\n"
        "• /search_film — Поиск по названию\n"
        "• /genres — Выбор жанра\n"
        "• /search_year — Поиск по году\n"
        "• /countries — Поиск по стране\n"
        "• /search_actor — Фильмография актёра\n\n"
        "🧠 <b>РЕКОМЕНДАЦИИ</b>\n"
        "• /recommend — Бот проанализирует просмотренное и предложит похожее.\n"
        "• /save_genres — Настроить любимые жанры.\n\n"
        "⚙️ <b>КНОПКИ</b>\n"
        "👁 <b>Просмотрено</b> — учитывается в рекомендациях.\n"
        "👎 <b>Не интересно</b> — скрывает фильм навсегда.\n\n"
        "<i>Нажмите на команду /film_ID в списке, чтобы открыть карточку фильма.</i>"
    )
    await message.answer(help_text)


# --- ЖАНРЫ ---
@router.message(Command("genres"))
async def cmd_genres(message: Message, state: FSMContext):
    await state.clear()
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
    text_ids = "\n".join([f"{g['genre']}: {g['id']}" for g in genres[:20]])
    await message.answer(f"📋 <b>ID жанров (для /save_genres):</b>\n{text_ids}")


@router.callback_query(F.data.startswith("genre_"))
async def process_genre_callback(callback: CallbackQuery):
    genre_id = int(callback.data.split("_")[1])
    await callback.message.answer(f"⏳ Ищу фильмы...")
    result = await kinopoisk_api.search_films_by_genre(genre_id)
    # ИСПОЛЬЗУЕМ send_film_results
    await send_film_results(callback.message, result.get('items', []), "🎭 Результаты по жанру", callback.from_user.id)
    await callback.answer()


# --- СТРАНЫ ---
@router.message(Command("countries"))
async def cmd_countries(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("⏳ Загружаю список стран...")
    countries = await kinopoisk_api.get_countries()
    if not countries:
        await message.answer("❌ Ошибка API")
        return
    text = "🌍 <b>Популярные страны (ID):</b>\n\n"
    for c in countries[:30]:
        text += f"• {c['country']}: <code>{c['id']}</code>\n"
    text += "\n👇 Введите команду /search_country и ID страны."
    await message.answer(text)


@router.message(Command("search_country"))
async def cmd_search_country(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🌍 Введите ID страны (например, 1 для США, 2 для России):")
    await state.set_state(FilmSearchStates.waiting_for_country)


@router.message(FilmSearchStates.waiting_for_country)
async def process_country(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Введите числовой ID.")
        return
    country_id = int(message.text)
    await message.answer("⏳ Ищу фильмы...")
    result = await kinopoisk_api.search_films_by_country(country_id)
    # ИСПОЛЬЗУЕМ send_film_results
    await send_film_results(message, result.get('items', []), "🌍 Фильмы по стране", message.from_user.id)
    await state.clear()


# --- ГОД ---
@router.message(Command("search_year"))
async def cmd_search_year(message: Message, state: FSMContext):
    await state.clear()
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

        # !!! ВОТ ЗДЕСЬ БЫЛА ОШИБКА В СТАРОЙ ВЕРСИИ, ТЕПЕРЬ ИСПРАВЛЕНО !!!
        # Мы используем ту же функцию send_film_results, что и везде
        await send_film_results(message, result.get('items', []), "📅 Фильмы по году", message.from_user.id)

        await state.clear()
    except ValueError:
        await message.answer("❌ Некорректный формат.")


# --- ПЕРСОНАЛИЗАЦИЯ ---
@router.message(Command("recommend"))
async def cmd_recommend(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    await message.answer("🤔 Анализирую ваши предпочтения...")

    # 1. Ищем похожие на просмотренные
    for _ in range(3):
        watched_film = await db.get_random_watched_film(user_id)
        if watched_film:
            base_id, base_title = watched_film
            similars = await kinopoisk_api.get_similars(base_id)
            if not similars: continue

            excluded_ids = await db.get_user_excluded_ids(user_id)
            clean_similars = [f for f in similars if (f.get('filmId') or f.get('kinopoiskId')) not in excluded_ids]

            if clean_similars:
                await message.answer(f"💡 Вы смотрели <b>«{base_title}»</b>.\nВозможно, вам понравится:")
                top_3 = clean_similars[:3]
                tasks = [kinopoisk_api.get_film_details(f.get('filmId')) for f in top_3]
                full_films = await asyncio.gather(*tasks)
                valid_films = [f for f in full_films if 'error' not in f]
                await send_film_results(message, valid_films, "", user_id)
                return

    # 2. Если нет просмотренных, используем жанры
    genres_str = await db.get_user_genres(user_id)
    if genres_str:
        try:
            genre_ids = [int(g) for g in genres_str.split(',')]
            target_genre = random.choice(genre_ids)
            await message.answer("🎲 Подбираю фильм на основе ваших любимых жанров...")
            random_page = random.randint(1, 5)
            result = await kinopoisk_api.search_films_by_genre(target_genre, page=random_page)
            films = result.get('items', [])
            if not films:
                result = await kinopoisk_api.search_films_by_genre(target_genre, page=1)
                films = result.get('items', [])
            await send_film_results(message, films, "🎲 Рекомендация по жанру", user_id)
            return
        except Exception:
            pass

    await message.answer(
        "😔 Мне не хватает данных. Отметьте фильмы как «Просмотрено» или сохраните жанры через /save_genres.")


@router.message(Command("save_genres"))
async def cmd_save_genres(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("✍️ Введите ID жанров через запятую:")
    await state.set_state(FilmSearchStates.waiting_for_multiple_genres)


@router.message(FilmSearchStates.waiting_for_multiple_genres)
async def process_multiple_genres(message: Message, state: FSMContext):
    try:
        text = message.text.strip()
        ids = [int(x.strip()) for x in text.split(',') if x.strip().isdigit()]
        if not ids: raise ValueError
        await db.set_user_genres(message.from_user.id, text)
        await message.answer("✅ Жанры сохранены!")
        await state.clear()
    except ValueError:
        await message.answer("❌ Введите числа.")


# --- ПОИСК ПО ЛЮДЯМ ---
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
    result = await kinopoisk_api.search_films_by_person(pid, profession)
    if 'error' in result:
        await message.answer("❌ Ошибка API")
        await state.clear()
        return
    films = result.get('items', [])

    await message.answer("⏳ Подгружаю детали...")
    top_5 = films[:5]
    tasks = [kinopoisk_api.get_film_details(f.get('filmId') or f.get('kinopoiskId')) for f in top_5]
    details = await asyncio.gather(*tasks)
    enriched = [d if 'error' not in d else o for d, o in zip(details, top_5)]
    final = enriched + films[5:]

    role = "Актёр" if profession == 'ACTOR' else "Режиссёр"
    # ИСПОЛЬЗУЕМ send_film_results
    await send_film_results(message, final, f"🎬 Фильмография ({role})", message.from_user.id)
    await state.clear()


@router.message(Command("search_actor"))
async def cmd_actor(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🎭 Введите имя актёра:")
    await state.set_state(FilmSearchStates.waiting_for_actor_name)


@router.message(FilmSearchStates.waiting_for_actor_name)
async def process_actor(message: Message, state: FSMContext):
    await process_person_search(message, state, 'ACTOR')


@router.message(Command("search_director"))
async def cmd_director(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🎬 Введите имя режиссёра:")
    await state.set_state(FilmSearchStates.waiting_for_director_name)


@router.message(FilmSearchStates.waiting_for_director_name)
async def process_director(message: Message, state: FSMContext):
    await process_person_search(message, state, 'DIRECTOR')


# --- ПОИСК ПО НАЗВАНИЮ ---
@router.message(Command("search_film"))
async def cmd_search_film(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🔎 Введите название:")
    await state.set_state(FilmSearchStates.waiting_for_film_name)


@router.message(FilmSearchStates.waiting_for_film_name)
async def process_film_name(message: Message, state: FSMContext):
    film_name = message.text.strip()
    await message.answer(f"⏳ Ищу «{film_name}»...")
    result = await kinopoisk_api.search_films_by_keyword(film_name)
    films = result.get('items', [])
    # ИСПОЛЬЗУЕМ send_film_results
    await send_film_results(message, films, f"🔎 Результаты: «{film_name}»", message.from_user.id)
    await state.clear()


# --- СПИСКИ ---
@router.message(Command("my_watched"))
async def cmd_my_watched(message: Message, state: FSMContext):
    await state.clear()
    films = await db.get_user_films_full(message.from_user.id, 'watched')
    if not films:
        await message.answer("Список пуст.")
        return
    text = "👁 <b>Просмотрено:</b>\n\n"
    for title, fid in films:
        # ИСПОЛЬЗУЕМ КОМАНДУ /film_ID
        text += f"• /film_{fid} — {title}\n"
    await message.answer(text)


@router.message(Command("my_plan"))
async def cmd_my_plan(message: Message, state: FSMContext):
    await state.clear()
    films = await db.get_user_films_full(message.from_user.id, 'plan')
    if not films:
        await message.answer("Список пуст.")
        return
    text = "🔖 <b>Буду смотреть:</b>\n\n"
    for title, fid in films:
        # ИСПОЛЬЗУЕМ КОМАНДУ /film_ID
        text += f"• /film_{fid} — {title}\n"
    await message.answer(text)