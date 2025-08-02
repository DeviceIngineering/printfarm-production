#!/bin/bash

# Быстрая диагностика проблем на сервере
# PrintFarm Quick Diagnosis Script

echo "🚨 PrintFarm Quick Diagnosis"
echo "============================"

# Проверка статуса контейнеров
echo "📦 СТАТУС КОНТЕЙНЕРОВ:"
docker-compose ps

echo
echo "🔍 КРАТКИЕ ЛОГИ BACKEND (последние 10 строк):"
docker-compose logs backend --tail=10

echo
echo "🌐 КРАТКИЕ ЛОГИ NGINX (последние 5 строк):"  
docker-compose logs nginx --tail=5

echo
echo "💾 СТАТУС БАЗЫ ДАННЫХ:"
docker-compose logs db --tail=5

echo
echo "📡 СТАТУС REDIS:"
docker-compose logs redis --tail=3

echo
echo "🔧 БЫСТРЫЕ КОМАНДЫ ДЛЯ ИСПРАВЛЕНИЯ:"
echo "1. Полный перезапуск: ./fix_production_errors.sh"
echo "2. Только backend: docker-compose restart backend"
echo "3. Просмотр всех логов: docker-compose logs"
echo "4. Остановка всего: docker-compose down"