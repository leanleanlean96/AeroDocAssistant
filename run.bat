@echo off
REM Скрипт для запуска FastAPI приложения на Windows

echo Проверка Python...
python --version > nul 2>&1
if errorlevel 1 (
    echo Ошибка: Python не установлен или не добавлен в PATH
    exit /b 1
)

echo Проверка зависимостей...
pip list | findstr /i "fastapi" > nul 2>&1
if errorlevel 1 (
    echo Установка зависимостей...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo Ошибка при установке зависимостей
        exit /b 1
    )
)

echo.
echo Запуск FastAPI приложения...
echo URL: http://localhost:8000
echo Документация: http://localhost:8000/docs
echo.

cd src
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

pause
