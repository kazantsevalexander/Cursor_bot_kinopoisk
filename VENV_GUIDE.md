# Руководство по работе с виртуальным окружением

## Что такое виртуальное окружение?

Виртуальное окружение (virtual environment) - это изолированная среда Python, которая позволяет устанавливать пакеты отдельно для каждого проекта, не затрагивая системную установку Python.

## Быстрый старт

### Автоматическая установка (Windows PowerShell)

Используйте готовый скрипт:
```powershell
.\setup_venv.ps1
```

Этот скрипт:
1. Создаст виртуальное окружение
2. Активирует его
3. Установит все зависимости

### Ручная установка

#### Windows (PowerShell)

1. **Создание виртуального окружения:**
   ```powershell
   python -m venv venv
   ```

2. **Активация:**
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```
   
   Если появляется ошибка о политике выполнения скриптов:
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

3. **Установка зависимостей:**
   ```powershell
   pip install -r requirements.txt
   ```

4. **Запуск бота:**
   ```powershell
   python main.py
   ```

#### Windows (CMD)

1. **Создание:**
   ```cmd
   python -m venv venv
   ```

2. **Активация:**
   ```cmd
   venv\Scripts\activate.bat
   ```

3. **Установка зависимостей:**
   ```cmd
   pip install -r requirements.txt
   ```

4. **Запуск:**
   ```cmd
   python main.py
   ```

#### Linux/Mac

1. **Создание:**
   ```bash
   python3 -m venv venv
   ```

2. **Активация:**
   ```bash
   source venv/bin/activate
   ```

3. **Установка зависимостей:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Запуск:**
   ```bash
   python main.py
   ```

## Использование скриптов (Windows)

### setup_venv.ps1
Полная настройка виртуального окружения:
```powershell
.\setup_venv.ps1
```

### activate_venv.ps1
Только активация существующего окружения:
```powershell
.\activate_venv.ps1
```

### run.ps1
Запуск бота с автоматической активацией:
```powershell
.\run.ps1
```

## Проверка активации

После активации виртуального окружения в начале строки терминала появится префикс `(venv)`:
```
(venv) PS C:\Users\User\Documents\GitHub\Cursor_bot_kinopoisk>
```

## Деактивация

Чтобы выйти из виртуального окружения:
```bash
deactivate
```

## Удаление виртуального окружения

Просто удалите папку `venv`:
```powershell
Remove-Item -Recurse -Force venv
```

## Частые проблемы

### Ошибка выполнения скриптов в PowerShell

**Проблема:** `cannot be loaded because running scripts is disabled on this system`

**Решение:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Python не найден

**Проблема:** `python : Имя "python" не распознано`

**Решение:**
1. Установите Python с [python.org](https://www.python.org/downloads/)
2. При установке отметьте "Add Python to PATH"
3. Перезапустите терминал

### Виртуальное окружение не активируется

**Проблема:** Скрипт активации не найден

**Решение:**
Убедитесь, что вы находитесь в корневой папке проекта и виртуальное окружение создано:
```powershell
python -m venv venv
```

## Рекомендации

- ✅ Всегда используйте виртуальное окружение для проектов
- ✅ Не коммитьте папку `venv` в git (она уже в .gitignore)
- ✅ Активируйте виртуальное окружение перед работой с проектом
- ✅ Обновляйте requirements.txt при добавлении новых зависимостей:
  ```bash
  pip freeze > requirements.txt
  ```


