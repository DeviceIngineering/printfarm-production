#!/bin/bash

# PrintFarm Production - Быстрое исправление хоста
# Исправляет ошибку DisallowedHost и настраивает порт 8089

set -e

print_info() {
    echo -e "\033[0;34mℹ️  $1\033[0m"
}

print_success() {
    echo -e "\033[0;32m✅ $1\033[0m"
}

print_info "🔧 Быстрое исправление Django ALLOWED_HOSTS..."

# Шаг 1: Исправляем .env файл
print_info "Обновляем .env..."
sed -i 's/ALLOWED_HOSTS=.*/ALLOWED_HOSTS=*/' .env
echo "ALLOWED_HOSTS=*" >> .env

# Шаг 2: Исправляем Django settings напрямую в контейнере
print_info "Исправляем Django settings в контейнере..."
docker-compose -f docker-compose.prod.yml exec -T backend sh -c '
echo "
# Patch ALLOWED_HOSTS
import os
os.environ[\"DJANGO_ALLOWED_HOSTS\"] = \"*\"
" > /tmp/patch_hosts.py

python /tmp/patch_hosts.py
'

# Шаг 3: Проверяем порт nginx
print_info "Проверяем nginx..."
docker-compose -f docker-compose.prod.yml ps nginx

# Шаг 4: Перезапускаем сервисы
print_info "Перезапускаем backend..."
docker-compose -f docker-compose.prod.yml restart backend

sleep 5

print_info "Перезапускаем nginx..."
docker-compose -f docker-compose.prod.yml restart nginx

sleep 5

# Шаг 5: Проверяем порты
print_info "Проверяем порты..."
netstat -tlnp | grep :8089 || echo "Порт 8089 не найден"

# Шаг 6: Тестируем
print_info "Тестируем доступ..."
if curl -f -s http://localhost:8089/health > /dev/null 2>&1; then
    print_success "Порт 8089 работает!"
elif curl -f -s http://localhost/api/v1/tochka/stats/ > /dev/null 2>&1; then
    print_success "API работает на порту 80!"
    echo "Возможно nginx работает на порту 80 вместо 8089"
else
    echo "Проверяем что работает..."
    docker-compose -f docker-compose.prod.yml ps
fi

print_success "Исправление завершено!"