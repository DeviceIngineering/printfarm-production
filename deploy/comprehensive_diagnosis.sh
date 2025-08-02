#!/bin/bash

# PrintFarm Production - Комплексная диагностика системы
# Полная диагностика всех компонентов и соединений

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_debug() {
    echo -e "${PURPLE}🔍 $1${NC}"
}

print_header() {
    echo -e "\n${CYAN}===========================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}===========================================${NC}\n"
}

print_section() {
    echo -e "\n${BLUE}--- $1 ---${NC}"
}

# Функция для тестирования URL с детальным выводом
test_url() {
    local url="$1"
    local description="$2"
    
    print_debug "Тестируем: $description"
    echo "URL: $url"
    
    # Тест доступности
    if curl -f -s --max-time 10 "$url" > /dev/null 2>&1; then
        print_success "✓ ДОСТУПЕН"
        # Показываем первые строки ответа
        echo "Ответ:"
        curl -s --max-time 10 "$url" 2>/dev/null | head -3 | sed 's/^/  /'
    else
        print_error "✗ НЕДОСТУПЕН"
        # Детальная диагностика
        echo "Детали ошибки:"
        curl -v --max-time 10 "$url" 2>&1 | head -10 | sed 's/^/  /'
    fi
    echo
}

print_header "КОМПЛЕКСНАЯ ДИАГНОСТИКА PRINTFARM"

# ============================================
# 1. ИНФОРМАЦИЯ О СИСТЕМЕ
# ============================================
print_header "1. СИСТЕМНАЯ ИНФОРМАЦИЯ"

print_section "Операционная система"
uname -a
cat /etc/os-release | head -5

print_section "Текущий пользователь и права"
echo "Пользователь: $(whoami)"
echo "UID: $(id -u)"
echo "Группы: $(groups)"

print_section "Время системы"
date
timedatectl status 2>/dev/null | head -5 || echo "timedatectl недоступен"

# ============================================
# 2. DOCKER И КОНТЕЙНЕРЫ
# ============================================
print_header "2. DOCKER И КОНТЕЙНЕРЫ"

print_section "Версии Docker"
docker --version 2>/dev/null || print_error "Docker недоступен"
docker-compose --version 2>/dev/null || print_error "Docker Compose недоступен"

print_section "Статус Docker сервиса"
systemctl is-active docker 2>/dev/null || echo "Статус Docker неизвестен"

print_section "Статус контейнеров PrintFarm"
if docker-compose -f docker-compose.prod.yml ps 2>/dev/null; then
    print_success "Docker Compose работает"
else
    print_error "Проблемы с Docker Compose"
fi

print_section "Детальная информация о контейнерах"
for container in backend nginx db redis celery; do
    echo "=== $container ==="
    if docker-compose -f docker-compose.prod.yml ps $container 2>/dev/null | grep -q "Up"; then
        print_success "$container: Работает"
        # Показываем порты
        docker-compose -f docker-compose.prod.yml ps $container | grep -E "(PORTS|tcp)" || echo "Нет информации о портах"
    else
        print_warning "$container: Проблемы"
        # Показываем статус
        docker-compose -f docker-compose.prod.yml ps $container 2>/dev/null || echo "Контейнер не найден"
    fi
    echo
done

print_section "Использование ресурсов Docker"
docker stats --no-stream 2>/dev/null | head -10 || echo "Docker stats недоступен"

# ============================================
# 3. СЕТЕВАЯ ДИАГНОСТИКА
# ============================================
print_header "3. СЕТЕВАЯ ДИАГНОСТИКА"

print_section "Открытые порты на хосте"
echo "TCP порты:"
netstat -tlnp 2>/dev/null | grep -E ":(80|8000|8089|5432|6379)" || echo "Целевые порты не найдены"

print_section "Процессы использующие порты"
for port in 80 8000 8089; do
    echo "Порт $port:"
    lsof -i :$port 2>/dev/null || echo "  Порт $port свободен или lsof недоступен"
done

print_section "Docker networks"
docker network ls 2>/dev/null || echo "Docker networks недоступны"

print_section "Внутренние IP адреса контейнеров"
for container in backend nginx; do
    if docker-compose -f docker-compose.prod.yml ps $container 2>/dev/null | grep -q "Up"; then
        container_id=$(docker-compose -f docker-compose.prod.yml ps -q $container 2>/dev/null)
        if [ -n "$container_id" ]; then
            ip=$(docker inspect $container_id 2>/dev/null | grep -E '"IPAddress".*[0-9]' | head -1 | cut -d'"' -f4)
            echo "$container: $ip"
        fi
    fi
done

# ============================================
# 4. КОНФИГУРАЦИОННЫЕ ФАЙЛЫ
# ============================================
print_header "4. КОНФИГУРАЦИОННЫЕ ФАЙЛЫ"

print_section "Содержимое .env"
if [ -f ".env" ]; then
    echo "Файл .env существует ($(wc -l < .env) строк):"
    grep -E "(ALLOWED_HOSTS|DEBUG|SECRET_KEY|POSTGRES|REDIS|MOYSKLAD)" .env 2>/dev/null | sed 's/^/  /' || echo "  Ключевые настройки не найдены"
else
    print_error "Файл .env не найден!"
fi

print_section "Содержимое nginx.conf"
if [ -f "nginx.conf" ]; then
    echo "Файл nginx.conf существует ($(wc -l < nginx.conf) строк):"
    echo "Первые 20 строк:"
    head -20 nginx.conf | sed 's/^/  /'
else
    print_error "Файл nginx.conf не найден!"
fi

print_section "Docker Compose конфигурация"
if [ -f "docker-compose.prod.yml" ]; then
    echo "Порты в docker-compose.prod.yml:"
    grep -A1 -B1 "ports:" docker-compose.prod.yml | sed 's/^/  /'
else
    print_error "Файл docker-compose.prod.yml не найден!"
fi

# ============================================
# 5. ЛОГИ СЕРВИСОВ
# ============================================
print_header "5. ЛОГИ СЕРВИСОВ"

for service in nginx backend celery; do
    print_section "Логи $service (последние 10 строк)"
    if docker-compose -f docker-compose.prod.yml logs --tail=10 $service 2>/dev/null; then
        echo
    else
        print_error "Не удалось получить логи $service"
    fi
done

# ============================================
# 6. DJANGO ДИАГНОСТИКА
# ============================================
print_header "6. DJANGO ДИАГНОСТИКА"

print_section "Django настройки"
if docker-compose -f docker-compose.prod.yml ps backend 2>/dev/null | grep -q "Up"; then
    echo "Проверяем Django настройки в контейнере:"
    docker-compose -f docker-compose.prod.yml exec -T backend python -c "
import os
import sys
try:
    from django.conf import settings
    print('✓ Django загружен успешно')
    print(f'  ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}')
    print(f'  DEBUG: {settings.DEBUG}')
    print(f'  SECRET_KEY установлен: {bool(settings.SECRET_KEY)}')
    
    # Проверяем базу данных
    from django.db import connection
    connection.ensure_connection()
    print('✓ Подключение к базе данных работает')
    
    # Проверяем приложения
    print(f'  Установленные приложения: {len(settings.INSTALLED_APPS)}')
    
except Exception as e:
    print(f'✗ Ошибка Django: {e}')
    sys.exit(1)
" 2>/dev/null || print_error "Не удалось проверить Django настройки"
else
    print_error "Backend контейнер не запущен"
fi

# ============================================
# 7. ТЕСТИРОВАНИЕ ДОСТУПНОСТИ
# ============================================
print_header "7. ТЕСТИРОВАНИЕ ДОСТУПНОСТИ"

# Локальные тесты
print_section "Локальные тесты"
test_url "http://localhost:8089/health" "Health check на порту 8089"
test_url "http://localhost:8089/api/v1/tochka/stats/" "API статистика на порту 8089"
test_url "http://localhost:8089/" "Корневая страница на порту 8089"

test_url "http://localhost:80/api/v1/tochka/stats/" "API на порту 80 (если доступен)"
test_url "http://localhost:8000/api/v1/tochka/stats/" "Прямой доступ к backend на порту 8000"

# Внутренние тесты Docker
print_section "Внутренние тесты Docker"
if docker-compose -f docker-compose.prod.yml ps backend 2>/dev/null | grep -q "Up"; then
    echo "Тестируем соединение nginx → backend изнутри:"
    docker-compose -f docker-compose.prod.yml exec -T nginx sh -c "
        apk add --no-cache curl 2>/dev/null >/dev/null || true
        echo 'Тест: nginx → backend:8000'
        if curl -f -s --max-time 5 http://backend:8000/api/v1/tochka/stats/ >/dev/null 2>&1; then
            echo '✓ nginx может подключиться к backend'
        else
            echo '✗ nginx НЕ может подключиться к backend'
        fi
    " 2>/dev/null || echo "Не удалось протестировать внутреннее соединение"
fi

# Внешние тесты
print_section "Внешние тесты"
# Получаем локальный IP
LOCAL_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "192.168.1.98")
test_url "http://$LOCAL_IP:8089/api/v1/tochka/stats/" "Внешний доступ по IP ($LOCAL_IP)"
test_url "http://kemomail3.keenetic.pro:8089/api/v1/tochka/stats/" "Внешний доступ по домену"

# ============================================
# 8. ДИАГНОСТИКА РОУТЕРА/СЕТИ
# ============================================
print_header "8. ДИАГНОСТИКА СЕТИ"

print_section "Сетевые интерфейсы"
ip addr show 2>/dev/null | grep -E "(inet |mtu)" | head -10 || ifconfig 2>/dev/null | grep -E "(inet|mtu)" | head -10 || echo "Информация о сети недоступна"

print_section "Маршрутизация"
ip route show 2>/dev/null | head -5 || route -n 2>/dev/null | head -5 || echo "Информация о маршрутах недоступна"

print_section "DNS"
cat /etc/resolv.conf 2>/dev/null | head -5 || echo "DNS настройки недоступны"

print_section "Тест DNS разрешения"
nslookup kemomail3.keenetic.pro 2>/dev/null | head -10 || dig kemomail3.keenetic.pro 2>/dev/null | head -10 || echo "DNS тест недоступен"

# ============================================
# 9. РЕКОМЕНДАЦИИ ПО ИСПРАВЛЕНИЮ
# ============================================
print_header "9. АНАЛИЗ И РЕКОМЕНДАЦИИ"

print_section "Анализ проблем"

# Проверяем основные проблемы
problems=0

# 1. Проверка статуса контейнеров
if ! docker-compose -f docker-compose.prod.yml ps 2>/dev/null | grep -q "Up.*nginx"; then
    print_error "Проблема 1: Nginx контейнер не работает"
    echo "  Решение: docker-compose -f docker-compose.prod.yml restart nginx"
    problems=$((problems + 1))
fi

if ! docker-compose -f docker-compose.prod.yml ps 2>/dev/null | grep -q "Up.*backend"; then
    print_error "Проблема 2: Backend контейнер не работает"
    echo "  Решение: docker-compose -f docker-compose.prod.yml restart backend"
    problems=$((problems + 1))
fi

# 2. Проверка портов
if ! netstat -tlnp 2>/dev/null | grep -q ":8089.*LISTEN"; then
    print_error "Проблема 3: Порт 8089 не слушается"
    echo "  Решение: Проверить docker-compose.prod.yml на наличие '8089:80' в nginx"
    problems=$((problems + 1))
fi

# 3. Проверка nginx конфигурации
if [ ! -f "nginx.conf" ]; then
    print_error "Проблема 4: Отсутствует nginx.conf"
    echo "  Решение: Создать nginx.conf с правильной конфигурацией"
    problems=$((problems + 1))
fi

# 4. Проверка ALLOWED_HOSTS
if ! grep -q "ALLOWED_HOSTS=.*\*" .env 2>/dev/null; then
    print_error "Проблема 5: ALLOWED_HOSTS может быть неправильно настроен"
    echo "  Решение: Убедиться что ALLOWED_HOSTS=* в .env"
    problems=$((problems + 1))
fi

print_section "Сводка"
if [ $problems -eq 0 ]; then
    print_success "Основные компоненты выглядят работоспособными"
    echo "Если внешний доступ не работает, проверьте настройки роутера:"
    echo "  - Проброс порта 8089 → 192.168.1.98:8089"
    echo "  - Правила файрвола"
else
    print_warning "Найдено $problems потенциальных проблем (см. выше)"
fi

print_section "Быстрые команды для исправления"
echo "# Полный перезапуск:"
echo "docker-compose -f docker-compose.prod.yml down && docker-compose -f docker-compose.prod.yml up -d"
echo
echo "# Проверка локального доступа:"
echo "curl http://localhost:8089/api/v1/tochka/stats/"
echo
echo "# Проверка внешнего доступа:"
echo "curl http://kemomail3.keenetic.pro:8089/api/v1/tochka/stats/"
echo
echo "# Просмотр логов:"
echo "docker-compose -f docker-compose.prod.yml logs nginx"
echo "docker-compose -f docker-compose.prod.yml logs backend"

print_header "ДИАГНОСТИКА ЗАВЕРШЕНА"
print_info "Сохраните этот отчет для анализа проблем"
print_success "Дата: $(date)"