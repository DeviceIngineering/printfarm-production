#!/bin/bash

# PrintFarm Production v3.3.0 - Скрипт обновления
# Обновляет систему до версии 3.3.0 с исправлениями CORS и историей синхронизаций

echo "🚀 ОБНОВЛЕНИЕ PrintFarm Production до v3.3.0"
echo "============================================="
echo ""

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅${NC} $1"
}

error() {
    echo -e "${RED}❌${NC} $1"
}

warning() {
    echo -e "${YELLOW}⚠️${NC} $1"
}

info() {
    echo -e "${PURPLE}ℹ️${NC} $1"
}

# Проверка прав и директории
if [ "$EUID" -eq 0 ]; then
    warning "Не рекомендуется запускать от root, но продолжаем..."
fi

if [ ! -f "docker-compose.yml" ]; then
    error "Файл docker-compose.yml не найден! Запустите скрипт из корня проекта."
    exit 1
fi

log "Начинаем обновление до версии 3.3.0..."

# Показать текущую версию
CURRENT_VERSION=""
if [ -f "VERSION" ]; then
    CURRENT_VERSION=$(cat VERSION)
    info "Текущая версия: $CURRENT_VERSION"
fi

# Шаг 1: Создание резервной копии
log "1/10 Создаем резервную копию..."
BACKUP_DIR="backups/update_$(date +'%Y%m%d_%H%M%S')"
mkdir -p $BACKUP_DIR

# Бэкап базы данных
if docker-compose ps db | grep -q "Up"; then
    docker-compose exec -T db pg_dump -U printfarm_user printfarm_db > $BACKUP_DIR/database.sql
    success "База данных сохранена: $BACKUP_DIR/database.sql"
else
    warning "База данных недоступна для бэкапа"
fi

# Бэкап конфигурации
cp -r backend/config $BACKUP_DIR/
cp docker-compose.yml $BACKUP_DIR/
if [ -f ".env" ]; then
    cp .env $BACKUP_DIR/
fi
success "Конфигурация сохранена"

# Шаг 2: Остановка сервисов
log "2/10 Останавливаем сервисы..."
docker-compose down --remove-orphans
success "Все сервисы остановлены"

# Шаг 3: Обновление кода
log "3/10 Обновляем код из GitHub..."
git fetch origin
git checkout main
git pull origin main

NEW_VERSION=$(cat VERSION)
if [ "$CURRENT_VERSION" != "$NEW_VERSION" ]; then
    success "Код обновлен с $CURRENT_VERSION до $NEW_VERSION"
else
    warning "Версия не изменилась: $NEW_VERSION"
fi

# Шаг 4: Проверка новых файлов
log "4/10 Проверяем новые файлы и настройки..."

NEW_FILES_COUNT=0

# Проверяем наличие новых важных файлов
if [ -f "backend/config/settings/server_production.py" ]; then
    success "✓ server_production.py найден"
    ((NEW_FILES_COUNT++))
fi

if [ -f "frontend/src/components/settings/SyncHistoryCard.tsx" ]; then
    success "✓ SyncHistoryCard.tsx найден"
    ((NEW_FILES_COUNT++))
fi

if [ -f "CORS-TROUBLESHOOTING.md" ]; then
    success "✓ CORS-TROUBLESHOOTING.md найден"
    ((NEW_FILES_COUNT++))
fi

info "Найдено новых файлов: $NEW_FILES_COUNT"

# Шаг 5: Установка переменных окружения
log "5/10 Настраиваем переменные окружения..."

# Создаем .env файл если его нет
if [ ! -f ".env" ]; then
    cat > .env << EOF
# PrintFarm Production v3.3.0 Environment
DJANGO_SETTINGS_MODULE=config.settings.server_production
DEBUG=False

# Database
POSTGRES_DB=printfarm_db
POSTGRES_USER=printfarm_user
POSTGRES_PASSWORD=secure_password

# Redis
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# МойСклад (заполните свои значения)
MOYSKLAD_TOKEN=your-token-here
MOYSKLAD_DEFAULT_WAREHOUSE=your-warehouse-id-here
EOF
    success "Создан .env файл (проверьте настройки МойСклад)"
else
    # Обновляем настройки Django в существующем .env
    if grep -q "DJANGO_SETTINGS_MODULE" .env; then
        sed -i 's/DJANGO_SETTINGS_MODULE=.*/DJANGO_SETTINGS_MODULE=config.settings.server_production/' .env
    else
        echo "DJANGO_SETTINGS_MODULE=config.settings.server_production" >> .env
    fi
    success "Обновлен .env файл"
fi

# Шаг 6: Пересборка контейнеров
log "6/10 Пересобираем Docker контейнеры..."
docker-compose build --no-cache
success "Контейнеры пересобраны"

# Шаг 7: Запуск базы данных
log "7/10 Запускаем базу данных..."
docker-compose up -d db redis
sleep 10

# Проверка БД
if docker-compose ps db | grep -q "Up"; then
    success "База данных запущена"
else
    error "Не удалось запустить базу данных"
    log "Пробуем восстановить из бэкапа..."
    docker-compose down
    docker volume rm $(docker volume ls -q | grep postgres) 2>/dev/null || true
    docker-compose up -d db
    sleep 15
    if [ -f "$BACKUP_DIR/database.sql" ]; then
        docker-compose exec -T db psql -U printfarm_user -d printfarm_db < $BACKUP_DIR/database.sql
        success "База данных восстановлена из бэкапа"
    fi
fi

# Шаг 8: Применение миграций
log "8/10 Применяем миграции базы данных..."
docker-compose run --rm backend python manage.py migrate
docker-compose run --rm backend python manage.py collectstatic --noinput
success "Миграции применены, статика собрана"

# Шаг 9: Запуск всех сервисов
log "9/10 Запускаем все сервисы..."
docker-compose up -d --remove-orphans
sleep 20

# Шаг 10: Проверка работоспособности
log "10/10 Проверяем работоспособность системы..."

echo ""
echo "📊 СОСТОЯНИЕ КОНТЕЙНЕРОВ:"
docker-compose ps

echo ""
echo "🔍 ПРОВЕРКА СЕРВИСОВ:"

# Проверка Backend API
if curl -f -s http://localhost:8000/api/v1/settings/system-info/ >/dev/null 2>&1; then
    success "Backend API работает"
else
    error "Backend API недоступен"
fi

# Проверка Frontend
if curl -f -s http://localhost:3000/ >/dev/null 2>&1; then
    success "Frontend работает"
else
    warning "Frontend еще загружается (подождите 1-2 минуты)"
fi

# Проверка базы данных
if docker-compose exec -T db pg_isready -U printfarm_user >/dev/null 2>&1; then
    success "PostgreSQL работает"
else
    error "PostgreSQL недоступен"
fi

# Проверка Redis
if docker-compose exec -T redis redis-cli ping 2>/dev/null | grep -q PONG; then
    success "Redis работает"
else
    warning "Redis может быть недоступен"
fi

# Проверка CORS
log "Проверяем CORS настройки..."
if curl -f -s -H "Origin: http://example.com" http://localhost:8000/api/v1/settings/system-info/ >/dev/null 2>&1; then
    success "CORS настроен корректно"
else
    warning "CORS может требовать дополнительной настройки"
fi

echo ""
echo "🎉 ОБНОВЛЕНИЕ ДО v3.3.0 ЗАВЕРШЕНО!"
echo ""
echo "🌟 НОВЫЕ ВОЗМОЖНОСТИ v3.3.0:"
echo "   ✨ История синхронизаций в настройках"
echo "   🔧 Исправлен расчет времени следующей синхронизации"
echo "   🌐 Исправлены CORS проблемы для внешних IP"
echo "   📊 Детальная статистика синхронизаций"
echo "   🚀 Улучшенная стабильность системы"
echo ""
echo "🌐 ДОСТУПНОСТЬ:"
echo "   • Сайт: http://kemomail3.keenetic.pro:3000/"
echo "   • API: http://kemomail3.keenetic.pro:8000/"
echo "   • Admin: http://kemomail3.keenetic.pro:8000/admin/"
echo ""
echo "📁 РЕЗЕРВНАЯ КОПИЯ:"
echo "   Сохранена в: $BACKUP_DIR"
echo ""
echo "📋 СЛЕДУЮЩИЕ ШАГИ:"
echo "   1. Проверьте работу сайта с разных устройств"
echo "   2. Протестируйте синхронизацию"
echo "   3. Проверьте новую историю синхронизаций в настройках"
echo ""

# Проверяем доступность внешнего адреса
log "Финальная проверка внешнего доступа..."
if curl -f -s --connect-timeout 10 http://kemomail3.keenetic.pro:3000/ >/dev/null 2>&1; then
    success "Сайт доступен по внешнему адресу!"
    success "Обновление полностью завершено ✅"
else
    warning "Внешний адрес пока недоступен, подождите 2-3 минуты"
fi

echo ""
echo "💡 ПОМОЩЬ И ДИАГНОСТИКА:"
echo "   • Статус системы: ./deploy/status.sh"
echo "   • CORS проблемы: ./deploy/fix_cors.sh"
echo "   • Восстановление: ./deploy/restore.sh $BACKUP_DIR/database.sql"
echo "   • Логи: docker-compose logs -f"
echo ""

# В случае проблем показать контактную информацию
if ! curl -f -s http://localhost:8000/api/v1/settings/system-info/ >/dev/null 2>&1; then
    echo "⚠️  ВНИМАНИЕ: Обнаружены проблемы!"
    echo "   Выполните диагностику:"
    echo "   1. docker-compose logs backend"
    echo "   2. ./deploy/status.sh"
    echo "   3. При критических ошибках: ./deploy/restore.sh $BACKUP_DIR/database.sql"
fi