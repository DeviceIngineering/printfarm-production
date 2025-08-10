#!/bin/bash

echo "🔍 Диагностика PrintFarm на сервере"
echo "===================================="

cd ~/printfarm-test 2>/dev/null || { echo "❌ Директория printfarm-test не найдена"; exit 1; }

echo "📊 Статус контейнеров:"
docker-compose -f docker-compose.server.yml ps

echo ""
echo "🔍 Проверка портов:"
echo "Порт 8090 (Web):"
curl -I http://localhost:8090 2>/dev/null | head -n 1 || echo "❌ Порт 8090 не отвечает"
echo "Порт 8001 (API):"
curl -I http://localhost:8001 2>/dev/null | head -n 1 || echo "❌ Порт 8001 не отвечает"

echo ""
echo "📝 Логи Frontend контейнера:"
docker-compose -f docker-compose.server.yml logs --tail=20 frontend

echo ""
echo "📝 Логи Nginx контейнера:"
docker-compose -f docker-compose.server.yml logs --tail=20 nginx

echo ""
echo "📝 Логи Backend контейнера:"
docker-compose -f docker-compose.server.yml logs --tail=20 backend

echo ""
echo "🔍 Проверка образов:"
docker images | grep printfarm

echo ""
echo "🔍 Проверка volumes:"
docker volume ls | grep printfarm

echo ""
echo "💡 Возможные решения:"
echo "1. Пересобрать frontend: docker-compose -f docker-compose.server.yml build --no-cache frontend"
echo "2. Проверить логи подробнее: docker-compose -f docker-compose.server.yml logs -f frontend"
echo "3. Войти в контейнер: docker-compose -f docker-compose.server.yml exec frontend sh"