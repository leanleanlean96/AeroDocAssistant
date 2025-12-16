#!/bin/bash

# Скрипт для запуска FastAPI приложения на Linux/macOS

echo "Проверка Python..."
python3 --version || { echo "Python не установлен"; exit 1; }

echo "Проверка зависимостей..."
pip3 list | grep -i "fastapi" > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "Установка зависимостей..."
    pip3 install -r requirements.txt || { echo "Ошибка при установке зависимостей"; exit 1; }
fi

echo ""
echo "Запуск FastAPI приложения..."
echo "URL: http://localhost:8000"
echo "Документация: http://localhost:8000/docs"
echo ""

cd src
python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
