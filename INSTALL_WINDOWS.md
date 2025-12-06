# Инструкция по установке для Windows

## Проблема: команда `pip` не распознана

Если вы видите ошибку `pip : Имя "pip" не распознано...`, это означает, что Python не установлен или не добавлен в PATH.

## Решение

### Вариант 1: Установка Python (рекомендуется)

1. **Скачайте Python:**
   - Перейдите на [python.org/downloads](https://www.python.org/downloads/)
   - Скачайте последнюю версию Python 3.x для Windows

2. **Установите Python:**
   - Запустите установщик
   - **ВАЖНО:** Отметьте галочку "Add Python to PATH" внизу окна установки
   - Нажмите "Install Now"

3. **Проверьте установку:**
   ```powershell
   python --version
   ```
   Должна отобразиться версия Python (например, `Python 3.11.5`)

4. **Установите зависимости:**
   ```powershell
   python -m pip install -r requirements.txt
   ```

### Вариант 2: Использование Microsoft Store

1. Откройте Microsoft Store
2. Найдите "Python 3.11" или "Python 3.12"
3. Установите
4. Используйте команду:
   ```powershell
   python -m pip install -r requirements.txt
   ```

### Вариант 3: Использование py launcher

Если Python установлен, но не в PATH, попробуйте:
```powershell
py -m pip install -r requirements.txt
```

## После установки Python

1. **Создайте файл `.env`:**
   - Создайте файл с именем `.env` в корне проекта
   - Добавьте в него:
     ```
     BOT_TOKEN=ваш_токен_бота
     KINOPOISK_API_KEY=ваш_api_ключ
     ```

2. **Запустите бота:**
   ```powershell
   python main.py
   ```

## Получение токенов

- **BOT_TOKEN:** Получите у [@BotFather](https://t.me/BotFather) в Telegram
- **KINOPOISK_API_KEY:** Получите на [kinopoiskapiunofficial.tech](https://kinopoiskapiunofficial.tech/)

