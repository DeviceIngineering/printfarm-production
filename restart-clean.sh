#!/bin/bash

echo "=== Полный перезапуск PrintFarm ==="
echo ""

# Очистка localStorage в браузере
echo "⚠️  ВАЖНО: Очистите localStorage в браузере!"
echo "1. Откройте http://localhost:3000"
echo "2. Нажмите F12 для DevTools"
echo "3. Во вкладке Console выполните: localStorage.clear()"
echo "4. Нажмите Enter чтобы продолжить..."
read

# Остановка всех процессов
echo "Остановка всех процессов..."
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:3000 | xargs kill -9 2>/dev/null
sleep 2

# Переход в backend
cd backend

# Запуск Django
echo "Запуск Django сервера..."
python3 manage.py runserver 0.0.0.0:8000 &
DJANGO_PID=$!
echo "Django PID: $DJANGO_PID"

# Ждем запуска Django
sleep 3

# Переход в frontend
cd ../frontend

# Запуск React
echo "Запуск React приложения..."
export BROWSER=none
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
echo "⚠️  Если видите черный экран:"
echo "1. Откройте консоль браузера (F12)"
echo "2. Проверьте ошибки в консоли"
echo "3. Попробуйте: localStorage.clear() и обновите страницу"
echo ""
echo "Для остановки нажмите Ctrl+C"
echo ""

trap "echo 'Останавливаем...'; kill $DJANGO_PID $REACT_PID; exit" INT

while true; do
    sleep 1
done