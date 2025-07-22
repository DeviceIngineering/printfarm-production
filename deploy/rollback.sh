#!/bin/bash

# PrintFarm Production Rollback Script
# Откат к предыдущей версии в случае проблем

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверка аргументов
if [ $# -eq 0 ]; then
    error "Использование: $0 <commit_hash_or_tag>"
    error "Пример: $0 ed9ab7b"
    error "Пример: $0 v3.1.3"
    exit 1
fi

TARGET=$1

log "🔄 Начинаем откат PrintFarm Production к $TARGET"

# Остановка сервисов
log "⏹️ Остановка сервисов..."
docker-compose down

# Откат кода
log "📤 Откат к $TARGET..."
git checkout $TARGET
success "Код откачен к $TARGET"

# Получаем версию после отката
ROLLBACK_VERSION=""
if [ -f "VERSION" ]; then
    ROLLBACK_VERSION=$(cat VERSION)
    log "📋 Версия после отката: $ROLLBACK_VERSION"
fi

# Пересборка образов
log "🔧 Пересборка образов для отката..."
docker-compose build --no-cache

# Запуск сервисов
log "▶️ Запуск сервисов..."
docker-compose up -d db redis
sleep 10

# Применение миграций (если нужно)
log "🗄️ Применение миграций..."
docker-compose run --rm backend python manage.py migrate

# Сбор статических файлов
log "📦 Сбор статических файлов..."
docker-compose run --rm backend python manage.py collectstatic --noinput

# Запуск всех сервисов
docker-compose up -d

log "🏥 Ожидание запуска сервисов..."
sleep 15

success "🎉 Откат к версии $ROLLBACK_VERSION завершен!"
log "🌐 Приложение доступно по адресам:"
log "  Frontend: http://localhost:3000"
log "  Backend API: http://localhost:8000"

# Показываем статус
docker-compose ps