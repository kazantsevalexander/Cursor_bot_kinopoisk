# Скрипт для создания и настройки виртуального окружения (Windows PowerShell)

Write-Host "Создание виртуального окружения..." -ForegroundColor Green

# Проверка наличия Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Найден Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Ошибка: Python не найден. Установите Python и добавьте его в PATH." -ForegroundColor Red
    exit 1
}

# Создание виртуального окружения
python -m venv venv

if ($LASTEXITCODE -eq 0) {
    Write-Host "Виртуальное окружение создано успешно!" -ForegroundColor Green
    
    # Активация виртуального окружения
    Write-Host "Активация виртуального окружения..." -ForegroundColor Green
    & .\venv\Scripts\Activate.ps1
    
    # Обновление pip
    Write-Host "Обновление pip..." -ForegroundColor Green
    python -m pip install --upgrade pip
    
    # Установка зависимостей
    Write-Host "Установка зависимостей из requirements.txt..." -ForegroundColor Green
    pip install -r requirements.txt
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`nУстановка завершена успешно!" -ForegroundColor Green
        Write-Host "Виртуальное окружение активировано." -ForegroundColor Green
        Write-Host "Теперь вы можете запустить бота командой: python main.py" -ForegroundColor Yellow
        Write-Host "`nНе забудьте создать файл .env с токенами!" -ForegroundColor Cyan
    } else {
        Write-Host "Ошибка при установке зависимостей." -ForegroundColor Red
    }
} else {
    Write-Host "Ошибка при создании виртуального окружения." -ForegroundColor Red
    exit 1
}


