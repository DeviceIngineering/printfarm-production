#!/bin/bash

echo "=== Запуск PrintFarm в режиме локальной разработки ==="
echo ""

# Переходим в директорию backend
cd backend

# Активируем виртуальное окружение или используем системный Python
if [ -d "../venv" ]; then
    echo "Используем виртуальное окружение..."
    source ../venv/bin/activate
else
    echo "Используем системный Python..."
fi

# Запускаем Django в фоновом режиме
echo "Запуск Django сервера на порту 8000..."
python manage.py runserver 0.0.0.0:8000 &
DJANGO_PID=$!
echo "Django PID: $DJANGO_PID"

# Ждем запуска Django
sleep 3

# Переходим в директорию frontend
cd ../frontend

# Запускаем React
echo ""
echo "Запуск React приложения на порту 3000..."
export BROWSER=none  # Отключаем автоматическое открытие браузера
npm start &
REACT_PID=$!
echo "React PID: $REACT_PID"

echo ""
echo "=== Приложение запущено! ==="
echo ""
echo "📍 Frontend: http://localhost:3000"
echo "📍 Backend API: http://localhost:8000/api/v1/"
echo "📍 Django Admin: http://localhost:8000/admin/"
echo ""
echo "Для остановки нажмите Ctrl+C"
echo ""

# Ждем сигнала прерывания
trap "echo 'Останавливаем приложение...'; kill $DJANGO_PID $REACT_PID; exit" INT

# Ждем бесконечно
while true; do
    sleep 1
done