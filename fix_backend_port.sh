#!/bin/bash

echo "=== ДИАГНОСТИКА И ИСПРАВЛЕНИЕ ПОРТА 8001 ==="
cd /opt/printfarm

echo "1. Проверка запущенных контейнеров..."
docker-compose -f docker-compose.prod.yml ps

echo "2. Проверка портов..."
netstat -tulpn | grep :8001
lsof -i :8001

echo "3. Проверка docker-compose.prod.yml..."
grep -A 5 -B 5 "8001" docker-compose.prod.yml

echo "4. Остановка и полная перезагрузка..."
docker-compose -f docker-compose.prod.yml down
sleep 5

echo "5. Очистка старых контейнеров..."
docker system prune -f

echo "6. Запуск заново..."
docker-compose -f docker-compose.prod.yml up -d

echo "7. Ожидание запуска..."
sleep 30

echo "8. Проверка логов backend..."
docker-compose -f docker-compose.prod.yml logs backend --tail=20

echo "9. Проверка доступности порта 8001..."
curl -I http://192.168.1.98:8001/api/v1/settings/
curl -I http://localhost:8001/api/v1/settings/

echo "10. Если порт 8001 недоступен, пробуем другие порты..."
curl -I http://192.168.1.98:8000/api/v1/settings/
curl -I http://192.168.1.98:8090/api/v1/settings/

echo "=== ДИАГНОСТИКА ЗАВЕРШЕНА ==="