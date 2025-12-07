Так как ты уже в консоли, просто выполняй команды по очереди.
Шаг 1. Обновление системы и установка инструментов
Сначала обновим списки пакетов и установим git, python3-venv и pip, если их нет.

sudo apt update
sudo apt install git python3-venv python3-pip -y
Шаг 2. Клонирование репозитория
Скачаем твой код с GitHub. Обрати внимание, мы сразу указываем ветку deploy.

git clone -b deploy https://github.com/kazantsevalexander/Cursor_bot_kinopoisk.git
cd Cursor_bot_kinopoisk
Шаг 3. Создание виртуального окружения
Создаем изолированную среду, чтобы не засорять системный Python.

python3 -m venv venv
Активируем его:

source venv/bin/activate
(После этой команды в начале строки должно появиться (venv)).
Шаг 4. Установка зависимостей
Устанавливаем библиотеки из файла requirements.txt.

Шаг 5. Настройка переменных окружения (.env)
Твои токены не хранятся на GitHub (и это правильно), поэтому их нужно создать на сервере вручную.
Открой редактор nano:

nano .env
Вставь туда свои данные (скопируй их из своего локального файла .env):

BOT_TOKEN=твои_токен_от_botfather
KINOPOISK_API_KEY=твой_ключ_кинопоиска
Сохрани и выйди:
Нажми Ctrl + O, затем Enter (сохранить).
Нажми Ctrl + X (выйти).
Шаг 6. Пробный запуск
Давай проверим, что бот запускается и не падает с ошибками.

python main.py
Если ты увидел:
INFO - Бот запущен и готов к работе!
...значит всё отлично.
Нажми Ctrl + C, чтобы остановить его. Сейчас мы сделаем так, чтобы он работал вечно.
Шаг 7. Настройка автозапуска (Systemd)
Чтобы бот работал в фоне, даже когда ты закроешь терминал, и сам перезапускался при перезагрузке сервера, создадим службу.
Создаем файл службы:

sudo nano /etc/systemd/system/kinopoisk_bot.service
Вставь туда следующий текст (пути я уже подставил под твоего пользователя agra):

Ini
[Unit]
Description=Kinopoisk Telegram Bot
After=network.target

[Service]
User=agra
Group=agra
Type=simple
WorkingDirectory=/home/agra/Cursor_bot_kinopoisk
ExecStart=/home/agra/Cursor_bot_kinopoisk/venv/bin/python /home/agra/Cursor_bot_kinopoisk/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
Сохрани и выйди (Ctrl + O, Enter, Ctrl + X).
Шаг 8. Запуск службы
Теперь активируем и запускаем бота:

# Перечитываем конфигурацию systemd
sudo systemctl daemon-reload

# Включаем автозапуск при старте сервера
sudo systemctl enable kinopoisk_bot

# Запускаем бота прямо сейчас
sudo systemctl start kinopoisk_bot
Шаг 9. Проверка статуса
Проверь, что всё работает:

sudo systemctl status kinopoisk_bot
Если горит зеленый кружок active (running), поздравляю! Твой бот опубликован и работает на сервере.
Полезные команды на будущее:
Посмотреть логи бота: sudo journalctl -u kinopoisk_bot -f
Перезапустить бота (если обновил код): sudo systemctl restart kinopoisk_bot
Остановить бота: sudo systemctl stop kinopoisk_bot