#!/bin/bash
# ============================================================
# PrintFarm v4.1.8 - Startup Script for Remote Server
# ============================================================
# Автоматический запуск всех компонентов системы
# ============================================================

set -e

# Конфигурация
PROJECT_NAME="printfarm-test"
PROJECT_DIR="/home/printfarm/${PROJECT_NAME}"
LOG_DIR="${PROJECT_DIR}/logs"
PID_DIR="/var/run/printfarm"

# Порты
POSTGRES_PORT="15432"
REDIS_PORT="16379"
BACKEND_PORT="18000"
FRONTEND_PORT="13000"
UNIFIED_PORT="13000"

# Цвета для логирования
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Логирование
log_info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} [INFO] $1" | tee -a ${LOG_DIR}/startup.log
}

log_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} [SUCCESS] $1" | tee -a ${LOG_DIR}/startup.log
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} [WARNING] $1" | tee -a ${LOG_DIR}/startup.log
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} [ERROR] $1" | tee -a ${LOG_DIR}/startup.log
}

# Создание необходимых директорий
create_directories() {
    log_info "Creating necessary directories..."
    mkdir -p ${LOG_DIR}
    mkdir -p ${PID_DIR}
    chmod 755 ${PID_DIR}
}

# Проверка Docker
check_docker() {
    log_info "Checking Docker..."
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed!"
        exit 1
    fi
    
    if ! systemctl is-active --quiet docker; then
        log_warning "Docker service is not running. Starting..."
        sudo systemctl start docker
        sleep 5
    fi
    
    log_success "Docker is ready"
}

# Очистка старых контейнеров
cleanup_old_containers() {
    log_info "Cleaning up old containers..."
    
    # Остановка существующих контейнеров проекта
    docker ps -q --filter "name=printfarm" | xargs -r docker stop 2>/dev/null || true
    docker ps -aq --filter "name=printfarm" | xargs -r docker rm 2>/dev/null || true
    
    log_success "Old containers cleaned"
}

# Запуск PostgreSQL
start_postgresql() {
    log_info "Starting PostgreSQL..."
    
    docker run -d \
        --name printfarm-test-db \
        --restart unless-stopped \
        -e POSTGRES_DB=printfarm_remote \
        -e POSTGRES_USER=printfarm_remote \
        -e POSTGRES_PASSWORD=printfarm_remote_2025 \
        -p ${POSTGRES_PORT}:5432 \
        -v printfarm_postgres_data:/var/lib/postgresql/data \
        --health-cmd="pg_isready -U printfarm_remote" \
        --health-interval=10s \
        --health-timeout=5s \
        --health-retries=5 \
        postgres:15-alpine
    
    # Ждем готовности PostgreSQL
    log_info "Waiting for PostgreSQL to be ready..."
    for i in {1..30}; do
        if docker exec printfarm-test-db pg_isready -U printfarm_remote &>/dev/null; then
            log_success "PostgreSQL is ready"
            return 0
        fi
        sleep 2
    done
    
    log_error "PostgreSQL failed to start"
    return 1
}

# Запуск Redis
start_redis() {
    log_info "Starting Redis..."
    
    docker run -d \
        --name printfarm-test-redis \
        --restart unless-stopped \
        -p ${REDIS_PORT}:6379 \
        -v printfarm_redis_data:/data \
        --health-cmd="redis-cli ping" \
        --health-interval=10s \
        --health-timeout=5s \
        --health-retries=5 \
        redis:7-alpine
    
    # Ждем готовности Redis
    log_info "Waiting for Redis to be ready..."
    for i in {1..20}; do
        if docker exec printfarm-test-redis redis-cli ping &>/dev/null; then
            log_success "Redis is ready"
            return 0
        fi
        sleep 1
    done
    
    log_error "Redis failed to start"
    return 1
}

# Запуск Backend
start_backend() {
    log_info "Starting Backend..."
    
    # Создаем .env файл если его нет
    if [ ! -f "${PROJECT_DIR}/.env.remote" ]; then
        log_warning ".env.remote not found, creating..."
        cat > ${PROJECT_DIR}/.env.remote << 'EOF'
# PrintFarm Remote Environment
DEBUG=False
SECRET_KEY=django-insecure-change-this-in-production-$(date +%s)
ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.98,kemomail3.keenetic.pro,*

# Database
POSTGRES_DB=printfarm_remote
POSTGRES_USER=printfarm_remote
POSTGRES_PASSWORD=printfarm_remote_2025
DB_HOST=localhost
DB_PORT=15432

# Disable file logging
DISABLE_FILE_LOGGING=true

# MoySklad
MOYSKLAD_TOKEN=f9be4985f5e3488716c040ca52b8e04c7c0f9e0b
MOYSKLAD_DEFAULT_WAREHOUSE=241ed919-a631-11ee-0a80-07a9000bb947

# Redis
REDIS_URL=redis://localhost:16379/0
CELERY_BROKER_URL=redis://localhost:16379/0
CELERY_RESULT_BACKEND=redis://localhost:16379/0
EOF
    fi
    
    docker run -d \
        --name printfarm-test-backend \
        --restart unless-stopped \
        --network host \
        -v ${PROJECT_DIR}/backend:/app \
        -v ${PROJECT_DIR}/logs:/app/logs \
        -v ${PROJECT_DIR}/.env.remote:/app/.env \
        -e DJANGO_SETTINGS_MODULE=config.settings.production \
        -e PYTHONUNBUFFERED=1 \
        -w /app \
        python:3.11-slim \
        sh -c "pip install -r requirements.txt && python manage.py migrate --noinput && python manage.py runserver 0.0.0.0:${BACKEND_PORT}"
    
    # Ждем готовности Backend
    log_info "Waiting for Backend to be ready..."
    for i in {1..60}; do
        if curl -f http://localhost:${BACKEND_PORT}/api/v1/health/ &>/dev/null; then
            log_success "Backend is ready"
            
            # Создаем admin пользователя и токен
            log_info "Creating admin user and token..."
            docker exec printfarm-test-backend python manage.py shell << 'EOF' 2>/dev/null || true
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

User = get_user_model()
if not User.objects.filter(username='admin').exists():
    user = User.objects.create_superuser('admin', 'admin@printfarm.test', 'admin123')
    Token.objects.create(user=user, key='0a8fee03bca2b530a15b1df44d38b304e3f57484')
    print('Admin user and token created')
else:
    print('Admin user already exists')
EOF
            return 0
        fi
        sleep 2
    done
    
    log_error "Backend failed to start"
    return 1
}

# Запуск Unified App (Frontend + API proxy)
start_unified_app() {
    log_info "Starting Unified App..."
    
    # Создаем unified proxy конфигурацию
    cat > /tmp/unified-proxy.conf << 'EOF'
server {
    listen 80;
    server_name _;
    
    # API proxy
    location /api/ {
        proxy_pass http://host.docker.internal:18000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # CORS headers
        add_header Access-Control-Allow-Origin * always;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Authorization, Content-Type" always;
        
        if ($request_method = OPTIONS) {
            return 204;
        }
    }
    
    # Admin proxy
    location /admin/ {
        proxy_pass http://host.docker.internal:18000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Static files
    location /static/ {
        alias /usr/share/nginx/html/static/;
        expires 30d;
    }
    
    # Frontend
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }
}
EOF
    
    # Собираем Frontend с относительными URL
    log_info "Building Frontend..."
    cd ${PROJECT_DIR}/frontend
    
    # Создаем production build
    docker run --rm \
        -v ${PROJECT_DIR}/frontend:/app \
        -w /app \
        -e REACT_APP_API_URL=/api/v1 \
        -e REACT_APP_VERSION=4.1.8 \
        node:18-alpine \
        sh -c "npm install && npm run build"
    
    # Запускаем Nginx с unified конфигурацией
    docker run -d \
        --name printfarm-unified-app \
        --restart unless-stopped \
        --add-host=host.docker.internal:host-gateway \
        -p ${UNIFIED_PORT}:80 \
        -v /tmp/unified-proxy.conf:/etc/nginx/conf.d/default.conf:ro \
        -v ${PROJECT_DIR}/frontend/build:/usr/share/nginx/html:ro \
        -v ${PROJECT_DIR}/backend/static:/usr/share/nginx/html/static:ro \
        nginx:alpine
    
    # Ждем готовности
    log_info "Waiting for Unified App to be ready..."
    for i in {1..30}; do
        if curl -f http://localhost:${UNIFIED_PORT}/ &>/dev/null; then
            log_success "Unified App is ready"
            return 0
        fi
        sleep 2
    done
    
    log_error "Unified App failed to start"
    return 1
}

# Проверка статуса всех сервисов
check_services_status() {
    log_info "Checking services status..."
    
    local all_healthy=true
    
    # PostgreSQL
    if docker ps --filter "name=printfarm-test-db" --filter "status=running" -q | grep -q .; then
        log_success "PostgreSQL: Running"
    else
        log_error "PostgreSQL: Not running"
        all_healthy=false
    fi
    
    # Redis
    if docker ps --filter "name=printfarm-test-redis" --filter "status=running" -q | grep -q .; then
        log_success "Redis: Running"
    else
        log_error "Redis: Not running"
        all_healthy=false
    fi
    
    # Backend
    if curl -f http://localhost:${BACKEND_PORT}/api/v1/health/ &>/dev/null; then
        log_success "Backend: Healthy"
    else
        log_error "Backend: Not healthy"
        all_healthy=false
    fi
    
    # Unified App
    if curl -f http://localhost:${UNIFIED_PORT}/ &>/dev/null; then
        log_success "Unified App: Healthy"
    else
        log_error "Unified App: Not healthy"
        all_healthy=false
    fi
    
    if [ "$all_healthy" = true ]; then
        log_success "All services are running and healthy!"
        return 0
    else
        log_error "Some services are not healthy"
        return 1
    fi
}

# Основная функция запуска
main() {
    log_info "=========================================="
    log_info "Starting PrintFarm v4.1.8"
    log_info "=========================================="
    
    create_directories
    check_docker
    cleanup_old_containers
    
    start_postgresql || exit 1
    start_redis || exit 1
    start_backend || exit 1
    start_unified_app || exit 1
    
    check_services_status
    
    log_success "=========================================="
    log_success "PrintFarm started successfully!"
    log_success "=========================================="
    log_info "Access URLs:"
    log_info "  - Application: http://localhost:${UNIFIED_PORT}"
    log_info "  - API: http://localhost:${UNIFIED_PORT}/api/v1/"
    log_info "  - Admin: http://localhost:${UNIFIED_PORT}/admin/"
    log_info ""
    log_info "External access:"
    log_info "  - http://kemomail3.keenetic.pro:${UNIFIED_PORT}"
    
    # Сохраняем PID главного процесса
    echo $$ > ${PID_DIR}/printfarm.pid
}

# Функция остановки
stop() {
    log_info "Stopping PrintFarm..."
    
    docker stop printfarm-unified-app 2>/dev/null || true
    docker stop printfarm-test-backend 2>/dev/null || true
    docker stop printfarm-test-redis 2>/dev/null || true
    docker stop printfarm-test-db 2>/dev/null || true
    
    docker rm printfarm-unified-app 2>/dev/null || true
    docker rm printfarm-test-backend 2>/dev/null || true
    docker rm printfarm-test-redis 2>/dev/null || true
    docker rm printfarm-test-db 2>/dev/null || true
    
    rm -f ${PID_DIR}/printfarm.pid
    
    log_success "PrintFarm stopped"
}

# Функция перезапуска
restart() {
    stop
    sleep 5
    main
}

# Функция проверки статуса
status() {
    check_services_status
}

# Обработка аргументов
case "${1:-start}" in
    start)
        main
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    status)
        status
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac