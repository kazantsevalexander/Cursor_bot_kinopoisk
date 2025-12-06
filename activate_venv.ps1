# Скрипт для активации виртуального окружения (Windows PowerShell)

if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "Активация виртуального окружения..." -ForegroundColor Green
    & .\venv\Scripts\Activate.ps1
    Write-Host "Виртуальное окружение активировано!" -ForegroundColor Green
} else {
    Write-Host "Ошибка: Виртуальное окружение не найдено." -ForegroundColor Red
    Write-Host "Создайте его командой: python -m venv venv" -ForegroundColor Yellow
    Write-Host "Или используйте скрипт: .\setup_venv.ps1" -ForegroundColor Yellow
}

