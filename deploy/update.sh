#!/bin/bash

# PrintFarm Production - Скрипт обновления
# Автоматическое обновление до последней версии

set -e

# Цвета для вывода
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_header() {
    echo -e "\n${BLUE}===========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}===========================================${NC}\n"
}

# Основная функция
main() {
    print_header "PRINTFARM PRODUCTION - ОБНОВЛЕНИЕ"
    
    print_info "🔄 Обновление PrintFarm Production..."

    # Останавливаем сервисы
    docker-compose -f docker-compose.prod.yml down

    # Получаем обновления
    git pull origin main

    # Пересобираем образы
    docker-compose -f docker-compose.prod.yml build --no-cache

    # Запускаем сервисы
    docker-compose -f docker-compose.prod.yml up -d

    # Применяем миграции
    sleep 30
    docker-compose -f docker-compose.prod.yml exec -T backend python manage.py migrate

    print_success "✅ Обновление завершено!"
}

# Запускаем обновление
main "$@"