# Скрипт для запуска бота с автоматической активацией виртуального окружения

if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "Активация виртуального окружения..." -ForegroundColor Green
    & .\venv\Scripts\Activate.ps1
    
    Write-Host "Запуск бота..." -ForegroundColor Green
    python main.py
} else {
    Write-Host "Ошибка: Виртуальное окружение не найдено." -ForegroundColor Red
    Write-Host "Создайте его командой: python -m venv venv" -ForegroundColor Yellow
    Write-Host "Или используйте скрипт: .\setup_venv.ps1" -ForegroundColor Yellow
    exit 1
}

