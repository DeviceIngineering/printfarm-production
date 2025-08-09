#!/bin/bash

# Скрипт для проверки и назначения свободных портов

print_info() {
    echo -e "\033[0;36m[INFO]\033[0m $1"
}

print_success() {
    echo -e "\033[0;32m[OK]\033[0m $1"
}

print_warning() {
    echo -e "\033[1;33m[WARN]\033[0m $1"
}

print_error() {
    echo -e "\033[0;31m[ERROR]\033[0m $1"
}

# Функция проверки свободности порта
is_port_free() {
    local port=$1
    ! netstat -tln 2>/dev/null | grep -q ":$port "
}

# Функция поиска свободного порта в диапазоне
find_free_port() {
    local start_port=$1
    local end_port=$2
    
    for port in $(seq $start_port $end_port); do
        if is_port_free $port; then
            echo $port
            return 0
        fi
    done
    
    return 1
}

print_info "Анализ занятых портов на сервере..."

# Показать занятые порты
print_info "Занятые порты:"
netstat -tln 2>/dev/null | grep -E ":(80|443|5432|6379|8000|9000|5000|3000|4000) " | while read line; do
    port=$(echo $line | awk '{print $4}' | cut -d':' -f2)
    process=$(netstat -tlnp 2>/dev/null | grep ":$port " | awk '{print $7}' | head -1)
    print_warning "Порт $port: $process"
done

print_info "Поиск свободных портов для PrintFarm..."

# Найти свободные порты
BACKEND_PORT=$(find_free_port 8001 8010)
WEBHOOK_PORT=$(find_free_port 9001 9010)
POSTGRES_PORT=$(find_free_port 5433 5440)
REDIS_PORT=$(find_free_port 6380 6390)

if [ -z "$BACKEND_PORT" ] || [ -z "$WEBHOOK_PORT" ] || [ -z "$POSTGRES_PORT" ] || [ -z "$REDIS_PORT" ]; then
    print_error "Не удалось найти свободные порты"
    exit 1
fi

print_success "Найдены свободные порты:"
print_success "Backend (Django): $BACKEND_PORT"
print_success "Webhook: $WEBHOOK_PORT"
print_success "PostgreSQL: $POSTGRES_PORT (внутренний)"
print_success "Redis: $REDIS_PORT (внутренний)"
print_success "Nginx: 80, 443 (будут использоваться через Docker)"

# Создание файла с портами для docker-compose
cat > /tmp/printfarm_ports.env << EOF
# Порты для PrintFarm (автоматически назначенные)
BACKEND_PORT=$BACKEND_PORT
WEBHOOK_PORT=$WEBHOOK_PORT
POSTGRES_PORT=$POSTGRES_PORT
REDIS_PORT=$REDIS_PORT

# Внешние порты (через nginx proxy)
HTTP_PORT=80
HTTPS_PORT=443
EOF

print_success "Конфигурация портов сохранена в /tmp/printfarm_ports.env"

# Предложение обновления конфигурации
print_info "Для обновления docker-compose.prod.yml используйте найденные порты:"
echo "  Backend: $BACKEND_PORT"
echo "  Webhook: $WEBHOOK_PORT"
echo ""
print_info "Nginx будет проксировать на backend:$BACKEND_PORT внутри Docker сети"