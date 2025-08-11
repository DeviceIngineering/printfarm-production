#!/bin/bash

echo "=== ПЕРЕСБОРКА FRONTEND С ПРАВИЛЬНЫМ API_URL ==="
cd /opt/printfarm

echo "1. Проверка текущего API в backend..."
curl -s http://192.168.1.98:8001/api/v1/settings/summary/ | head -c 200

echo "2. Остановка frontend..."
docker-compose -f docker-compose.prod.yml stop frontend

echo "3. Настройка правильного API_URL..."
cat > frontend/.env << 'EOF'
REACT_APP_API_URL=http://192.168.1.98:8001/api/v1
NODE_ENV=production
GENERATE_SOURCEMAP=false
EOF

cat > frontend/.env.production << 'EOF'
REACT_APP_API_URL=http://192.168.1.98:8001/api/v1
NODE_ENV=production
GENERATE_SOURCEMAP=false
EOF

echo "4. Удаление старого build..."
docker-compose -f docker-compose.prod.yml exec frontend rm -rf /app/build 2>/dev/null || true

echo "5. Пересборка frontend контейнера..."
docker-compose -f docker-compose.prod.yml build frontend --no-cache

echo "6. Запуск нового frontend..."
docker-compose -f docker-compose.prod.yml up -d frontend

echo "7. Ожидание запуска..."
sleep 15

echo "8. Проверка frontend..."
curl -I http://192.168.1.98:8090/

echo "9. Проверка что frontend использует правильный API..."
echo "Откройте http://192.168.1.98:8090/settings"
echo "В консоли браузера (F12) должны быть запросы к 192.168.1.98:8001"

echo "=== FRONTEND ПЕРЕСОБРАН! ==="
echo "Проверьте настройки: http://192.168.1.98:8090/settings"