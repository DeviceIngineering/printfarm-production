#!/bin/bash

# PrintFarm Production Update Script v3.3.0
# Автоматическое обновление проекта на удаленном сервере

set -e  # Остановка скрипта при любой ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция логирования
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

# Проверка что скрипт запущен из корневой директории проекта
if [ ! -f "VERSION" ] || [ ! -f "docker-compose.yml" ]; then
    error "Скрипт должен быть запущен из корневой директории проекта PrintFarm"
    error "Убедитесь что файлы VERSION и docker-compose.yml существуют"
    exit 1
fi

log "🚀 Начинаем обновление PrintFarm Production до версии 3.1.4"

# Получаем текущую версию
CURRENT_VERSION=""
if [ -f "VERSION" ]; then
    CURRENT_VERSION=$(cat VERSION)
    log "📋 Текущая версия: $CURRENT_VERSION"
fi

# 1. Создание бэкапа базы данных
log "💾 Создание бэкапа базы данных..."
BACKUP_DIR="backups/$(date +'%Y%m%d_%H%M%S')"
mkdir -p "$BACKUP_DIR"

if docker-compose ps db | grep -q "Up"; then
    log "Создание дампа PostgreSQL..."
    docker-compose exec -T db pg_dump -U printfarm_user printfarm_db > "$BACKUP_DIR/database.sql"
    success "Бэкап базы данных создан: $BACKUP_DIR/database.sql"
else
    warning "Контейнер базы данных не запущен, пропускаем бэкап"
fi

# 2. Остановка сервисов
log "⏹️ Остановка сервисов..."
docker-compose down
success "Сервисы остановлены"

# 3. Получение обновлений из Git
log "📥 Получение обновлений из Git..."
git fetch origin
git pull origin main
success "Код обновлен из репозитория"

# Проверяем новую версию
NEW_VERSION=""
if [ -f "VERSION" ]; then
    NEW_VERSION=$(cat VERSION)
    log "📋 Новая версия: $NEW_VERSION"
fi

# 4. Обновление зависимостей и сборка образов
log "🔧 Обновление зависимостей и сборка образов..."
docker-compose build --no-cache
success "Образы пересобраны"

# 5. Применение миграций
log "🗄️ Применение миграций базы данных..."
docker-compose up -d db redis
sleep 10  # Ждем запуска базы данных

docker-compose run --rm backend python manage.py migrate
success "Миграции применены"

# 6. Сбор статических файлов
log "📦 Сбор статических файлов..."
docker-compose run --rm backend python manage.py collectstatic --noinput
success "Статические файлы собраны"

# 7. Запуск всех сервисов
log "▶️ Запуск всех сервисов..."
docker-compose up -d
success "Все сервисы запущены"

# 8. Проверка здоровья сервисов
log "🏥 Проверка здоровья сервисов..."
sleep 15  # Даем время на запуск

# Проверяем статус контейнеров
log "Проверка статуса контейнеров..."
docker-compose ps

# Проверяем доступность backend API
log "Проверка API backend..."
if curl -f -s http://localhost:8000/api/v1/settings/system-info/ > /dev/null; then
    success "Backend API доступен"
else
    error "Backend API недоступен"
fi

# Проверяем доступность frontend
log "Проверка frontend..."
if curl -f -s http://localhost:3000/ > /dev/null; then
    success "Frontend доступен"
else
    warning "Frontend может быть еще не готов (это нормально для React app)"
fi

# 9. Очистка старых образов и томов
log "🧹 Очистка неиспользуемых образов и томов..."
docker system prune -f
docker volume prune -f
success "Очистка завершена"

# 10. Итоговая информация
log "📊 Информация об обновлении:"
log "  Предыдущая версия: ${CURRENT_VERSION:-"неизвестно"}"
log "  Новая версия: ${NEW_VERSION:-"неизвестно"}"
log "  Время обновления: $(date +'%Y-%m-%d %H:%M:%S')"
log "  Бэкап базы данных: $BACKUP_DIR/database.sql"

success "🎉 Обновление PrintFarm Production завершено успешно!"
log "🌐 Приложение доступно по адресам:"
log "  Frontend: http://localhost:3000"
log "  Backend API: http://localhost:8000"
log "  Admin panel: http://localhost:8000/admin"

# Показываем логи для мониторинга
log "📜 Показываем логи сервисов (нажмите Ctrl+C для выхода):"
sleep 3
docker-compose logs -f --tail=50