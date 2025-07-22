#!/bin/bash

# PrintFarm Production - Исправление CORS проблем
# Обновляет настройки для доступа с внешних IP адресов

echo "🔧 ИСПРАВЛЕНИЕ CORS ПРОБЛЕМ PrintFarm Production"
echo "================================================"
echo ""

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

log "Начинаем исправление CORS проблем..."

# Шаг 1: Остановка сервисов
log "1/6 Останавливаем сервисы..."
docker-compose down
success "Сервисы остановлены"

# Шаг 2: Обновление кода из git
log "2/6 Обновляем код..."
git pull origin main
success "Код обновлен"

# Шаг 3: Установка переменной окружения для server production настроек
log "3/6 Настраиваем переменные окружения..."
export DJANGO_SETTINGS_MODULE="config.settings.server_production"
echo "DJANGO_SETTINGS_MODULE=config.settings.server_production" > .env.server
success "Переменные настроены"

# Шаг 4: Пересборка контейнеров
log "4/6 Пересобираем контейнеры..."
docker-compose build --no-cache backend
success "Контейнеры пересобраны"

# Шаг 5: Запуск с новыми настройками
log "5/6 Запускаем сервисы с новыми настройками..."
DJANGO_SETTINGS_MODULE=config.settings.server_production docker-compose up -d --remove-orphans
sleep 10
success "Сервисы запущены"

# Шаг 6: Проверка работоспособности
log "6/6 Проверяем доступность API..."

# Проверка Backend API
if curl -f -s -H "Origin: http://example.com" http://localhost:8000/api/v1/settings/system-info/ >/dev/null 2>&1; then
    success "Backend API доступен с внешних IP"
else
    warning "Backend API может быть недоступен, проверяем подробнее..."
    # Детальная проверка
    curl -v -H "Origin: http://example.com" http://localhost:8000/api/v1/settings/system-info/
fi

echo ""
echo "🎉 CORS ИСПРАВЛЕНИЕ ЗАВЕРШЕНО!"
echo ""
echo "🔍 ТЕСТ ДОСТУПНОСТИ:"
echo "   1. Откройте сайт с другого компьютера: http://kemomail3.keenetic.pro:3000/"
echo "   2. Проверьте доступ к API: http://kemomail3.keenetic.pro:8000/api/v1/settings/system-info/"
echo ""
echo "🔧 ЧТО БЫЛО СДЕЛАНО:"
echo "   • Включен CORS_ALLOW_ALL_ORIGINS=True"
echo "   • Добавлены CORS_ALLOWED_HEADERS и CORS_ALLOWED_METHODS"
echo "   • Отключены строгие SSL настройки"
echo "   • Разрешены запросы с любых хостов"
echo "   • Смягчены настройки CSRF и cookies"
echo ""
echo "📝 Если проблемы остались:"
echo "   1. Проверьте файрвол: sudo ufw status"
echo "   2. Проверьте логи: docker-compose logs backend"
echo "   3. Запустите: ./deploy/status.sh"
echo ""

# Показать последние логи
log "Последние логи backend (нажмите Ctrl+C для выхода):"
sleep 3
docker-compose logs -f backend --tail=20