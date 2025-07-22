#!/bin/bash

# PrintFarm - ИСПРАВЛЕНИЕ ПОРТА 80
# Решаем проблему занятого порта 80 для nginx

echo "🔧 ИСПРАВЛЕНИЕ КОНФЛИКТА ПОРТА 80"
echo "================================="
echo "Nginx не может запуститься - порт 80 занят"
echo ""

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"; }
success() { echo -e "${GREEN}✅${NC} $1"; }
error() { echo -e "${RED}❌${NC} $1"; }
warning() { echo -e "${YELLOW}⚠️${NC} $1"; }

# ========================================================================
# ЭТАП 1: ДИАГНОСТИКА ПОРТА 80
# ========================================================================

log "ЭТАП 1: ДИАГНОСТИКА КОНФЛИКТА ПОРТА 80"

log "1.1 Проверяем что занимает порт 80..."
echo "🔍 ПРОЦЕССЫ НА ПОРТУ 80:"
sudo lsof -i :80 2>/dev/null || echo "   lsof не показывает процессов"

echo ""
echo "🔍 NETSTAT ПОРТ 80:"
sudo netstat -tulpn | grep :80 || echo "   netstat не показывает процессов"

echo ""

# ========================================================================
# ЭТАП 2: ОСВОБОЖДЕНИЕ ПОРТА 80
# ========================================================================

log "ЭТАП 2: ОСВОБОЖДЕНИЕ ПОРТА 80"

log "2.1 Останавливаем все контейнеры..."
docker-compose down --remove-orphans >/dev/null 2>&1

log "2.2 Принудительно освобождаем порт 80..."
# Метод 1: fuser
sudo fuser -k 80/tcp >/dev/null 2>&1 || true

# Метод 2: lsof + kill
PIDS=$(sudo lsof -ti:80 2>/dev/null)
if [ -n "$PIDS" ]; then
    warning "Убиваем процессы на порту 80: $PIDS"
    echo "$PIDS" | xargs sudo kill -9 >/dev/null 2>&1 || true
fi

# Метод 3: остановка веб-серверов
sudo systemctl stop apache2 >/dev/null 2>&1 || true
sudo systemctl stop nginx >/dev/null 2>&1 || true
sudo systemctl stop lighttpd >/dev/null 2>&1 || true

sleep 3

log "2.3 Проверяем освобождение порта 80..."
PORT_80_CHECK=$(sudo netstat -tulpn | grep :80 || echo "free")
if [[ "$PORT_80_CHECK" == "free" ]]; then
    success "Порт 80 освобожден"
    USE_PORT_80=true
else
    warning "Порт 80 всё ещё занят, будем использовать порт 8080"
    echo "Что занимает: $PORT_80_CHECK"
    USE_PORT_80=false
fi

echo ""

# ========================================================================
# ЭТАП 3: ЗАПУСК БЕЗ NGINX (ВРЕМЕННО)
# ========================================================================

log "ЭТАП 3: ЗАПУСК ОСНОВНЫХ СЕРВИСОВ"

log "3.1 Запускаем основные сервисы без nginx..."
docker-compose up -d db redis backend frontend celery celery-beat --force-recreate
sleep 20

log "3.2 Проверяем статус основных сервисов..."
echo "📊 СТАТУС СЕРВИСОВ:"
docker-compose ps

# ========================================================================
# ЭТАП 4: НАСТРОЙКА NGINX
# ========================================================================

log "ЭТАП 4: НАСТРОЙКА И ЗАПУСК NGINX"

if [ "$USE_PORT_80" = true ]; then
    log "4.1 Используем стандартный порт 80..."
    docker-compose up -d nginx --force-recreate
    sleep 10
    
    if docker-compose ps nginx | grep -q "Up"; then
        success "Nginx успешно запущен на порту 80"
        NGINX_URL="http://kemomail3.keenetic.pro"
    else
        error "Nginx не запустился, проверяем логи..."
        docker-compose logs nginx --tail=10
        USE_PORT_80=false
    fi
fi

if [ "$USE_PORT_80" = false ]; then
    log "4.2 Настраиваем nginx на порт 8080..."
    
    # Создаем резервную копию docker-compose.yml
    cp docker-compose.yml docker-compose.yml.backup
    
    # Изменяем порт nginx на 8080
    sed -i 's/"80:80"/"8080:80"/g' docker-compose.yml
    
    log "Запускаем nginx на порту 8080..."
    docker-compose up -d nginx --force-recreate
    sleep 10
    
    if docker-compose ps nginx | grep -q "Up"; then
        success "Nginx запущен на альтернативном порту 8080"
        NGINX_URL="http://kemomail3.keenetic.pro:8080"
    else
        warning "Nginx не удалось запустить, система будет работать без nginx"
        NGINX_URL="http://kemomail3.keenetic.pro:3000"
    fi
fi

# ========================================================================
# ЭТАП 5: ФИНАЛЬНОЕ ТЕСТИРОВАНИЕ
# ========================================================================

log "ЭТАП 5: ТЕСТИРОВАНИЕ ДОСТУПНОСТИ"

log "5.1 Проверяем доступность frontend..."
FRONTEND_TEST=$(curl -s -w "%{http_code}" http://localhost:3000/ -o /tmp/frontend_test.txt 2>&1)
echo "💻 Frontend (прямой): $FRONTEND_TEST"

log "5.2 Проверяем доступность через nginx (если запущен)..."
if docker-compose ps nginx | grep -q "Up"; then
    if [ "$USE_PORT_80" = true ]; then
        NGINX_TEST=$(curl -s -w "%{http_code}" http://localhost/ -o /tmp/nginx_test.txt 2>&1)
        echo "🌐 Nginx (порт 80): $NGINX_TEST"
    else
        NGINX_TEST=$(curl -s -w "%{http_code}" http://localhost:8080/ -o /tmp/nginx_test.txt 2>&1)
        echo "🌐 Nginx (порт 8080): $NGINX_TEST"
    fi
else
    warning "Nginx не запущен"
fi

log "5.3 Проверяем backend API..."
API_TEST=$(curl -s -w "%{http_code}" http://localhost:8000/api/v1/settings/system-info/ -o /tmp/api_test.txt 2>&1)
echo "🔗 Backend API: $API_TEST"

# ========================================================================
# ИТОГОВЫЙ ОТЧЕТ
# ========================================================================

echo ""
echo "🔧 ИСПРАВЛЕНИЕ ПОРТА 80 ЗАВЕРШЕНО"
echo "================================="

echo ""
echo "📊 РЕЗУЛЬТАТЫ:"
echo "   • Порт 80 свободен: $([ "$USE_PORT_80" = true ] && echo "✅ ДА" || echo "❌ НЕТ")"
echo "   • Frontend доступен: $([ "$FRONTEND_TEST" = "200" ] && echo "✅ ОК" || echo "❌ НЕДОСТУПЕН")"
echo "   • Nginx запущен: $(docker-compose ps nginx | grep -q "Up" && echo "✅ ДА" || echo "❌ НЕТ")"
echo "   • Backend API: $([ "$API_TEST" = "200" ] && echo "✅ ОК" || echo "❌ НЕДОСТУПЕН")"

echo ""
echo "🌐 ДОСТУПНЫЕ АДРЕСА:"
if docker-compose ps nginx | grep -q "Up"; then
    success "Основной доступ через Nginx: $NGINX_URL"
else
    warning "Nginx недоступен, используйте прямой доступ:"
fi
echo "   • Frontend: http://kemomail3.keenetic.pro:3000/"
echo "   • Backend: http://kemomail3.keenetic.pro:8000/"

echo ""
echo "📋 СТАТУС ВСЕХ КОНТЕЙНЕРОВ:"
docker-compose ps

echo ""
if [ "$FRONTEND_TEST" = "200" ] && [ "$API_TEST" = "200" ]; then
    success "🎉 СИСТЕМА РАБОТАЕТ!"
    echo ""
    echo "✅ ТЕПЕРЬ МОЖНО:"
    echo "   1. Открыть http://kemomail3.keenetic.pro:3000/"
    echo "   2. Проверить настройки и историю синхронизаций"
    echo "   3. Протестировать доступ второго пользователя"
    echo "   4. Использовать все функции системы"
    
    if [ "$USE_PORT_80" = false ]; then
        echo ""
        warning "📝 ВНИМАНИЕ: Nginx работает на порту 8080"
        echo "   • Основной URL: $NGINX_URL"
        echo "   • Резервная копия: docker-compose.yml.backup"
        echo "   • Для возврата к порту 80: восстановите копию и перезапустите"
    fi
    
else
    error "❌ СИСТЕМА ТРЕБУЕТ ВНИМАНИЯ"
    echo ""
    echo "🆘 ДИАГНОСТИКА:"
    [ "$FRONTEND_TEST" != "200" ] && echo "   • Frontend недоступен - проверьте: docker-compose logs frontend"
    [ "$API_TEST" != "200" ] && echo "   • Backend недоступен - проверьте: docker-compose logs backend"
fi

echo ""
success "Исправление конфликта порта 80 завершено: $(date)"