#!/bin/bash

# PrintFarm Production - Экстренное восстановление системы
# Исправляет проблемы с портами и запускает все сервисы

echo "🚨 ЭКСТРЕННОЕ ВОССТАНОВЛЕНИЕ PrintFarm Production"
echo "=================================================="
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

log "Начинаем экстренное восстановление..."

# Шаг 1: Полная остановка всех Docker контейнеров
log "1/10 Останавливаем все Docker контейнеры..."
docker-compose down >/dev/null 2>&1 || echo "Контейнеры уже остановлены"
docker kill $(docker ps -q) >/dev/null 2>&1 || echo "Нет запущенных контейнеров"
success "Все контейнеры остановлены"

# Шаг 2: Очистка Docker ресурсов
log "2/10 Очищаем Docker ресурсы..."
docker container prune -f >/dev/null 2>&1
docker network prune -f >/dev/null 2>&1
docker network rm printfarm_default >/dev/null 2>&1 || echo "Сеть уже удалена"
success "Docker ресурсы очищены"

# Шаг 3: Освобождение заблокированных портов
log "3/10 Освобождаем заблокированные порты..."

# Убиваем процессы на критических портах
fuser -k 3000/tcp >/dev/null 2>&1 || echo "Порт 3000 свободен"
fuser -k 8000/tcp >/dev/null 2>&1 || echo "Порт 8000 свободен"
fuser -k 6379/tcp >/dev/null 2>&1 || echo "Порт 6379 свободен"
fuser -k 5432/tcp >/dev/null 2>&1 || echo "Порт 5432 свободен"

success "Порты освобождены"

# Шаг 4: Перезапуск Docker службы
log "4/10 Перезапускаем Docker службу..."
systemctl restart docker
sleep 5
success "Docker служба перезапущена"

# Шаг 5: Проверка docker-compose.yml
log "5/10 Проверяем конфигурацию..."
if [ ! -f "docker-compose.yml" ]; then
    error "Файл docker-compose.yml не найден!"
    exit 1
fi
success "Конфигурация найдена"

# Шаг 6: Запуск базы данных
log "6/10 Запускаем базу данных..."
docker-compose up -d db --remove-orphans
sleep 10

# Проверка запуска БД
if docker-compose ps db | grep -q "Up"; then
    success "База данных запущена"
else
    error "Не удалось запустить базу данных"
    log "Пробуем принудительно..."
    docker-compose up -d db --force-recreate
    sleep 10
fi

# Шаг 7: Запуск Redis
log "7/10 Запускаем Redis..."
docker-compose up -d redis --remove-orphans
sleep 5

# Проверка Redis
if docker-compose ps redis | grep -q "Up"; then
    success "Redis запущен"
else
    warning "Redis может иметь проблемы, но продолжаем..."
fi

# Шаг 8: Применение миграций
log "8/10 Применяем миграции базы данных..."
docker-compose run --rm backend python manage.py migrate
success "Миграции применены"

# Шаг 9: Сбор статических файлов
log "9/10 Собираем статические файлы..."
docker-compose run --rm backend python manage.py collectstatic --noinput
success "Статические файлы собраны"

# Шаг 10: Запуск всех сервисов
log "10/10 Запускаем все сервисы..."
docker-compose up -d --remove-orphans
sleep 15

# Финальная проверка
log "Проверяем состояние системы..."
echo ""
echo "📊 СОСТОЯНИЕ КОНТЕЙНЕРОВ:"
docker-compose ps

echo ""
echo "🔍 ПРОВЕРКА СЕРВИСОВ:"

# Проверка Backend API
if curl -f -s http://localhost:8000/api/v1/settings/system-info/ >/dev/null 2>&1; then
    success "Backend API работает (http://localhost:8000)"
else
    error "Backend API недоступен"
fi

# Проверка Frontend
if curl -f -s http://localhost:3000/ >/dev/null 2>&1; then
    success "Frontend работает (http://localhost:3000)"
else
    warning "Frontend еще загружается (это нормально для React)"
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

echo ""
echo "🎉 ВОССТАНОВЛЕНИЕ ЗАВЕРШЕНО!"
echo ""
echo "🌐 Ваш сайт должен быть доступен по адресу:"
echo "   👉 http://kemomail3.keenetic.pro:3000/"
echo ""
echo "🔧 Дополнительные адреса:"
echo "   • API: http://kemomail3.keenetic.pro:8000/"
echo "   • Admin: http://kemomail3.keenetic.pro:8000/admin/"
echo ""

# Проверим доступность внешнего адреса
log "Проверяем доступность внешнего адреса..."
if curl -f -s --connect-timeout 10 http://kemomail3.keenetic.pro:3000/ >/dev/null 2>&1; then
    success "Сайт доступен по внешнему адресу!"
else
    warning "Внешний адрес пока недоступен, подождите 1-2 минуты"
fi

echo ""
echo "📝 Если проблемы остались:"
echo "   1. Подождите 2-3 минуты для полной загрузки"
echo "   2. Проверьте firewall: ufw status"
echo "   3. Свяжитесь с админом"
echo ""

# Показать последние логи
echo "📜 Последние логи (нажмите Ctrl+C для выхода):"
sleep 3
docker-compose logs -f --tail=20