# Telegram Bot для Кинопоиска

Telegram-бот для поиска фильмов через API Кинопоиска. Бот позволяет получать список жанров и искать фильмы по выбранному жанру.

## Возможности

- 📋 Получение списка всех доступных жанров
- 🔍 Поиск фильмов по жанру
- ⭐ Отображение рейтингов фильмов
- 🎬 Информация о фильмах (название, год, рейтинг)

## Установка

### Предварительные требования

**Установите Python 3.8 или выше:**
- Скачайте Python с [python.org](https://www.python.org/downloads/)
- При установке **обязательно отметьте** "Add Python to PATH"
- Или используйте установщик из Microsoft Store

### Шаги установки

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd Cursor_bot_kinopoisk
```

2. Установите зависимости:

**Для Windows (PowerShell):**
```powershell
python -m pip install -r requirements.txt
```
или
```powershell
py -m pip install -r requirements.txt
```

**Для Linux/Mac:**
```bash
pip install -r requirements.txt
```

3. Создайте файл `.env`:
   - Скопируйте содержимое из `env.example` (если файл существует)
   - Или создайте файл `.env` вручную со следующим содержимым:
   ```
   BOT_TOKEN=your_telegram_bot_token_here
   KINOPOISK_API_KEY=your_kinopoisk_api_key_here
   ```

4. Заполните `.env` файл:
   - `BOT_TOKEN` - токен вашего Telegram бота (получите у [@BotFather](https://t.me/BotFather))
   - `KINOPOISK_API_KEY` - API ключ Кинопоиска (получите на [kinopoiskapiunofficial.tech](https://kinopoiskapiunofficial.tech/))

## Запуск

**Для Windows:**
```powershell
python main.py
```
или
```powershell
py main.py
```

**Для Linux/Mac:**
```bash
python main.py
```

## Команды бота

- `/start` - Начать работу с ботом
- `/help` - Справка по использованию
- `/genres` - Получить список жанров
- `/search` - Поиск фильмов по жанру

## Структура проекта

```
Cursor_bot_kinopoisk/
├── config/           # Конфигурация
│   ├── __init__.py
│   └── config.py     # Загрузка переменных окружения
├── handlers/         # Обработчики команд
│   ├── __init__.py
│   └── commands.py   # Команды бота
├── services/         # Сервисы
│   ├── __init__.py
│   └── kinopoisk_api.py  # Работа с API Кинопоиска
├── main.py           # Точка входа
├── requirements.txt  # Зависимости
├── .env              # Переменные окружения (создать самостоятельно)
└── env.example       # Пример файла .env
```

## Используемые технологии

- [aiogram](https://docs.aiogram.dev/) - асинхронный фреймворк для Telegram ботов
- [aiohttp](https://docs.aiohttp.org/) - асинхронный HTTP клиент
- [python-dotenv](https://pypi.org/project/python-dotenv/) - загрузка переменных окружения
