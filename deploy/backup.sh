#!/bin/bash

# PrintFarm Production - Скрипт резервного копирования

set -e

# Цвета для вывода
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Настройки
BACKUP_DIR="/home/printfarm/backups"
DATE=$(date +%Y-%m-%d_%H-%M)
BACKUP_FILE="backup_$DATE.tar.gz"

# Загружаем переменные окружения
if [[ -f ".env" ]]; then
    source .env
fi

# Создаем папку для бэкапов
mkdir -p $BACKUP_DIR

print_info "💾 Создание резервной копии PrintFarm..."

# Бэкап базы данных
print_info "Создаем бэкап базы данных..."
docker-compose -f docker-compose.prod.yml exec -T db pg_dump -U $POSTGRES_USER $POSTGRES_DB > $BACKUP_DIR/database_$DATE.sql

# Бэкап файлов приложения
print_info "Создаем бэкап файлов приложения..."
tar -czf $BACKUP_DIR/$BACKUP_FILE \
    --exclude='*.log' \
    --exclude='__pycache__' \
    --exclude='node_modules' \
    --exclude='.git' \
    .

# Информация о размере
BACKUP_SIZE=$(du -h $BACKUP_DIR/$BACKUP_FILE | cut -f1)

print_success "✅ Резервная копия создана!"
print_info "📁 Файл: $BACKUP_DIR/$BACKUP_FILE"
print_info "📊 Размер: $BACKUP_SIZE"

# Очистка старых бэкапов (сохраняем последние 7)
print_info "🧹 Очистка старых бэкапов..."
cd $BACKUP_DIR
ls -t backup_*.tar.gz | tail -n +8 | xargs -r rm -f
ls -t database_*.sql | tail -n +8 | xargs -r rm -f

print_success "✅ Резервное копирование завершено!"