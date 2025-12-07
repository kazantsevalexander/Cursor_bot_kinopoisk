import aiosqlite
import logging

DB_NAME = 'bot_database.db'


async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                favorite_genres TEXT
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS user_films (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                film_id INTEGER,
                film_title TEXT,
                list_type TEXT,
                UNIQUE(user_id, film_id)
            )
        ''')
        await db.commit()


async def add_user(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (user_id,))
        await db.commit()


async def update_user_genres(user_id: int, new_genre_id: int):
    """Добавляет жанр к существующим, если его там нет"""
    async with aiosqlite.connect(DB_NAME) as db:
        # 1. Получаем текущие
        async with db.execute('SELECT favorite_genres FROM users WHERE user_id = ?', (user_id,)) as cursor:
            row = await cursor.fetchone()
            current_genres = row[0] if row and row[0] else ""

        # 2. Обновляем список
        if current_genres:
            ids = set(current_genres.split(','))
        else:
            ids = set()

        ids.add(str(new_genre_id))
        new_genres_str = ",".join(ids)

        # 3. Сохраняем
        await db.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (user_id,))
        await db.execute('UPDATE users SET favorite_genres = ? WHERE user_id = ?', (new_genres_str, user_id))
        await db.commit()


async def set_user_genres(user_id: int, genre_ids: str):
    """Перезаписывает жанры (для команды /save_genres)"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (user_id,))
        await db.execute('UPDATE users SET favorite_genres = ? WHERE user_id = ?', (genre_ids, user_id))
        await db.commit()


async def get_user_genres(user_id: int) -> str:
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT favorite_genres FROM users WHERE user_id = ?', (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None


async def add_film_to_list(user_id: int, film_id: int, title: str, list_type: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            INSERT OR REPLACE INTO user_films (user_id, film_id, film_title, list_type)
            VALUES (?, ?, ?, ?)
        ''', (user_id, film_id, title, list_type))
        await db.commit()


async def get_user_excluded_ids(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        query = "SELECT film_id FROM user_films WHERE user_id = ? AND list_type IN ('watched', 'ignored')"
        async with db.execute(query, (user_id,)) as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]


async def get_user_films_full(user_id: int, list_type: str):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT film_title, film_id FROM user_films WHERE user_id = ? AND list_type = ?',
                              (user_id, list_type)) as cursor:
            return await cursor.fetchall()


async def get_random_watched_film(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        query = "SELECT film_id, film_title FROM user_films WHERE user_id = ? AND list_type = 'watched' ORDER BY RANDOM() LIMIT 1"
        async with db.execute(query, (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row if row else None


async def get_user_stats(user_id: int):
    """Возвращает статистику для профиля"""
    async with aiosqlite.connect(DB_NAME) as db:
        watched = await db.execute("SELECT COUNT(*) FROM user_films WHERE user_id = ? AND list_type='watched'",
                                   (user_id,))
        watched_count = (await watched.fetchone())[0]

        plan = await db.execute("SELECT COUNT(*) FROM user_films WHERE user_id = ? AND list_type='plan'", (user_id,))
        plan_count = (await plan.fetchone())[0]

        return watched_count, plan_count