#!/bin/bash

# PrintFarm Production Database Restore Script
# Восстановление базы данных из бэкапа

set -e

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
    error "Использование: $0 <path_to_backup.sql>"
    log "Доступные бэкапы:"
    find backups -name "database.sql" -type f | sort -r | head -10
    exit 1
fi

BACKUP_FILE=$1

if [ ! -f "$BACKUP_FILE" ]; then
    error "Файл бэкапа не найден: $BACKUP_FILE"
    exit 1
fi

log "🔄 Начинаем восстановление базы данных из $BACKUP_FILE"

warning "⚠️  ВНИМАНИЕ: Это действие полностью заменит текущую базу данных!"
read -p "Продолжить? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log "Операция отменена пользователем"
    exit 0
fi

# Остановка backend сервисов
log "⏹️ Остановка backend сервисов..."
docker-compose stop backend celery celery-beat

# Убеждаемся что база данных запущена
log "▶️ Запуск сервиса базы данных..."
docker-compose up -d db
sleep 10

# Создание нового бэкапа текущей БД
log "💾 Создание бэкапа текущей БД перед восстановлением..."
SAFETY_BACKUP="backups/before_restore_$(date +'%Y%m%d_%H%M%S')/database.sql"
mkdir -p "$(dirname "$SAFETY_BACKUP")"
docker-compose exec -T db pg_dump -U printfarm_user printfarm_db > "$SAFETY_BACKUP"
success "Текущая БД сохранена в: $SAFETY_BACKUP"

# Очистка базы данных
log "🗑️ Очистка текущей базы данных..."
docker-compose exec -T db psql -U printfarm_user -d printfarm_db -c "DROP SCHEMA IF EXISTS public CASCADE;"
docker-compose exec -T db psql -U printfarm_user -d printfarm_db -c "CREATE SCHEMA public;"
docker-compose exec -T db psql -U printfarm_user -d printfarm_db -c "GRANT ALL ON SCHEMA public TO printfarm_user;"
docker-compose exec -T db psql -U printfarm_user -d printfarm_db -c "GRANT ALL ON SCHEMA public TO public;"

# Восстановление из бэкапа
log "📥 Восстановление из бэкапа..."
docker-compose exec -T db psql -U printfarm_user -d printfarm_db < "$BACKUP_FILE"
success "База данных восстановлена из $BACKUP_FILE"

# Применение миграций (на случай если нужны новые)
log "🗄️ Применение миграций..."
docker-compose run --rm backend python manage.py migrate

# Запуск всех сервисов
log "▶️ Запуск всех сервисов..."
docker-compose up -d

log "🏥 Ожидание запуска сервисов..."
sleep 15

success "🎉 Восстановление базы данных завершено!"
log "📊 Информация о восстановлении:"
log "  Восстановлено из: $BACKUP_FILE"
log "  Бэкап перед восстановлением: $SAFETY_BACKUP"
log "  Время восстановления: $(date +'%Y-%m-%d %H:%M:%S')"

# Проверка работоспособности
if docker-compose exec backend python manage.py check; then
    success "✅ Система работает корректно"
else
    error "❌ Обнаружены проблемы с системой"
fi