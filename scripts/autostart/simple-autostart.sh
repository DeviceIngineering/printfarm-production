#!/bin/bash
# ============================================================
# PrintFarm v4.2.0 - Simple Autostart (No systemd required)
# ============================================================
# Простая установка автозапуска через crontab
# Не требует sudo прав
# ============================================================

set -e

PROJECT_DIR="/home/printfarm/printfarm-test"
LOG_DIR="${PROJECT_DIR}/logs"

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Создание основного скрипта запуска
create_startup_script() {
    log_info "Creating startup script..."
    
    mkdir -p ${PROJECT_DIR}/scripts
    mkdir -p ${LOG_DIR}
    
    cat > ${PROJECT_DIR}/scripts/printfarm-startup.sh << 'EOF'
#!/bin/bash
# PrintFarm Startup Script

LOG_FILE="/home/printfarm/printfarm-test/logs/autostart.log"
exec > >(tee -a $LOG_FILE) 2>&1

echo "========================================"
echo "$(date): PrintFarm startup initiated"
echo "========================================"

# Переход в директорию проекта
cd /home/printfarm/printfarm-test

# Проверка наличия Docker
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker not found!"
    exit 1
fi

# Запуск основного скрипта если он существует
if [ -f "scripts/start-printfarm.sh" ]; then
    echo "Starting PrintFarm using main startup script..."
    bash scripts/start-printfarm.sh start
else
    echo "Main startup script not found, creating minimal startup..."
    
    # Остановка старых контейнеров
    echo "Stopping old containers..."
    docker stop $(docker ps -q --filter "name=printfarm") 2>/dev/null || true
    docker rm $(docker ps -aq --filter "name=printfarm") 2>/dev/null || true
    
    # Запуск PostgreSQL
    echo "Starting PostgreSQL..."
    docker run -d --name printfarm-test-db --restart unless-stopped \
        -e POSTGRES_DB=printfarm_remote \
        -e POSTGRES_USER=printfarm_remote \
        -e POSTGRES_PASSWORD=printfarm_remote_2025 \
        -p 15432:5432 \
        -v printfarm_postgres_data:/var/lib/postgresql/data \
        postgres:15-alpine
    
    # Ждем PostgreSQL
    echo "Waiting for PostgreSQL..."
    sleep 15
    
    # Запуск Redis
    echo "Starting Redis..."
    docker run -d --name printfarm-test-redis --restart unless-stopped \
        -p 16379:6379 \
        -v printfarm_redis_data:/data \
        redis:7-alpine
    
    # Ждем Redis
    echo "Waiting for Redis..."
    sleep 5
    
    # Создание .env если не существует
    if [ ! -f ".env.remote" ]; then
        echo "Creating .env.remote..."
        cat > .env.remote << 'ENV_EOF'
DEBUG=False
SECRET_KEY=django-insecure-auto-generated-$(date +%s)
ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.98,kemomail3.keenetic.pro,*
POSTGRES_DB=printfarm_remote
POSTGRES_USER=printfarm_remote
POSTGRES_PASSWORD=printfarm_remote_2025
DB_HOST=localhost
DB_PORT=15432
DISABLE_FILE_LOGGING=true
MOYSKLAD_TOKEN=f9be4985f5e3488716c040ca52b8e04c7c0f9e0b
MOYSKLAD_DEFAULT_WAREHOUSE=241ed919-a631-11ee-0a80-07a9000bb947
REDIS_URL=redis://localhost:16379/0
CELERY_BROKER_URL=redis://localhost:16379/0
CELERY_RESULT_BACKEND=redis://localhost:16379/0
ENV_EOF
    fi
    
    # Запуск Backend
    echo "Starting Backend..."
    docker run -d --name printfarm-test-backend --restart unless-stopped \
        --network host \
        -v $(pwd)/backend:/app \
        -v $(pwd)/logs:/app/logs \
        -v $(pwd)/.env.remote:/app/.env \
        -e DJANGO_SETTINGS_MODULE=config.settings.production \
        -e PYTHONUNBUFFERED=1 \
        -w /app \
        python:3.11-slim \
        bash -c "apt-get update && apt-get install -y libpq5 curl netcat-traditional && pip install -r requirements.txt && python manage.py migrate --noinput && python manage.py runserver 0.0.0.0:18000"
    
    # Запуск Celery Worker
    echo "Starting Celery Worker..."
    docker run -d --name printfarm-test-celery --restart unless-stopped \
        --network host \
        -v $(pwd)/backend:/app \
        -v $(pwd)/logs:/app/logs \
        -v $(pwd)/.env.remote:/app/.env \
        -e DJANGO_SETTINGS_MODULE=config.settings.production \
        -e PYTHONUNBUFFERED=1 \
        -w /app \
        python:3.11-slim \
        bash -c "apt-get update && apt-get install -y libpq5 && pip install -r requirements.txt && celery -A config worker -l info"
    
    # Запуск Celery Beat  
    echo "Starting Celery Beat..."
    docker run -d --name printfarm-test-celery-beat --restart unless-stopped \
        --network host \
        -v $(pwd)/backend:/app \
        -v $(pwd)/logs:/app/logs \
        -v $(pwd)/.env.remote:/app/.env \
        -e DJANGO_SETTINGS_MODULE=config.settings.production \
        -e PYTHONUNBUFFERED=1 \
        -w /app \
        python:3.11-slim \
        bash -c "apt-get update && apt-get install -y libpq5 && pip install -r requirements.txt && celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler"
    
    # Ждем Backend
    echo "Waiting for Backend..."
    for i in {1..60}; do
        if curl -f http://localhost:18000/api/v1/health/ &>/dev/null; then
            echo "Backend is ready"
            break
        fi
        sleep 5
    done
    
    # Создание токена
    echo "Creating admin user and token..."
    docker exec printfarm-test-backend python manage.py shell << 'PYEOF' || true
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    user = User.objects.create_superuser('admin', 'admin@printfarm.test', 'admin123')
    Token.objects.create(user=user, key='0a8fee03bca2b530a15b1df44d38b304e3f57484')
    print('Admin user and token created')
PYEOF
    
    # Простая страница заглушка
    echo "Creating frontend stub..."
    mkdir -p /tmp/printfarm-frontend
    cat > /tmp/printfarm-frontend/index.html << 'HTML_EOF'
<!DOCTYPE html>
<html>
<head><title>PrintFarm v4.2.0 - Running</title><meta charset="utf-8">
<style>body{font-family:Arial,sans-serif;margin:40px;background:#f0f0f0}.container{background:white;padding:40px;border-radius:8px;box-shadow:0 2px 10px rgba(0,0,0,0.1)}h1{color:#06EAFC;text-shadow:0 0 10px rgba(6,234,252,0.3)}.status{padding:20px;margin:20px 0;background:#e8f5e8;border-radius:4px}.link{display:inline-block;margin:10px 5px;padding:10px 20px;background:#06EAFC;color:white;text-decoration:none;border-radius:4px}</style>
</head>
<body>
<div class="container">
<h1>🏭 PrintFarm v4.2.0</h1>
<div class="status">✅ Система запущена и работает!<br>🚀 Автозапуск настроен</div>
<a href="/api/v1/health/" class="link">Health Check</a>
<a href="/api/v1/" class="link">API</a>
<a href="/admin/" class="link">Admin</a>
<p><b>Внешний доступ:</b> http://kemomail3.keenetic.pro:13000</p>
</div></body></html>
HTML_EOF
    
    # Запуск Nginx
    echo "Starting Nginx..."
    cat > /tmp/nginx.conf << 'NGINX_EOF'
server {
    listen 80;
    server_name _;
    location /api/ {
        proxy_pass http://host.docker.internal:18000;
        proxy_set_header Host $host;
        add_header Access-Control-Allow-Origin * always;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Authorization, Content-Type" always;
        if ($request_method = OPTIONS) { return 204; }
    }
    location /admin/ {
        proxy_pass http://host.docker.internal:18000;
        proxy_set_header Host $host;
    }
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }
}
NGINX_EOF
    
    docker run -d --name printfarm-unified-app --restart unless-stopped \
        --add-host=host.docker.internal:host-gateway \
        -p 13000:80 \
        -v /tmp/nginx.conf:/etc/nginx/conf.d/default.conf:ro \
        -v /tmp/printfarm-frontend:/usr/share/nginx/html:ro \
        nginx:alpine
fi

echo "========================================"
echo "$(date): PrintFarm startup completed"
echo "========================================"

# Проверка статуса
echo "Checking service status..."
curl -f http://localhost:13000/api/v1/health/ && echo "✅ API: OK" || echo "❌ API: Failed"
curl -f http://localhost:13000/ && echo "✅ Frontend: OK" || echo "❌ Frontend: Failed"

echo "PrintFarm is now running on:"
echo "  - http://localhost:13000"
echo "  - http://kemomail3.keenetic.pro:13000"
EOF
    
    chmod +x ${PROJECT_DIR}/scripts/printfarm-startup.sh
    log_success "Startup script created"
}

# Создание скрипта мониторинга
create_monitor_script() {
    log_info "Creating monitor script..."
    
    cat > ${PROJECT_DIR}/scripts/printfarm-monitor.sh << 'EOF'
#!/bin/bash
# PrintFarm Monitor Script

LOG_FILE="/home/printfarm/printfarm-test/logs/monitor.log"
exec >> $LOG_FILE 2>&1

echo "$(date): Monitoring check started"

# Проверка контейнеров
CONTAINERS=("printfarm-test-db" "printfarm-test-redis" "printfarm-test-backend" "printfarm-unified-app")

for container in "${CONTAINERS[@]}"; do
    if ! docker ps --filter "name=$container" --filter "status=running" -q | grep -q .; then
        echo "$(date): Container $container is not running. Restarting PrintFarm..."
        /home/printfarm/printfarm-test/scripts/printfarm-startup.sh
        break
    fi
done

# Проверка API
if ! curl -f http://localhost:13000/api/v1/health/ &>/dev/null; then
    echo "$(date): API health check failed. Restarting PrintFarm..."
    /home/printfarm/printfarm-test/scripts/printfarm-startup.sh
fi

echo "$(date): Monitoring check completed"
EOF
    
    chmod +x ${PROJECT_DIR}/scripts/printfarm-monitor.sh
    log_success "Monitor script created"
}

# Настройка crontab
setup_crontab() {
    log_info "Setting up crontab..."
    
    # Создаем новый crontab
    cat > /tmp/printfarm_cron << 'EOF'
# PrintFarm v4.2.0 Autostart
# Start at boot
@reboot sleep 60 && /home/printfarm/printfarm-test/scripts/printfarm-startup.sh

# Monitor every 5 minutes
*/5 * * * * /home/printfarm/printfarm-test/scripts/printfarm-monitor.sh

# Cleanup logs daily at 2 AM
0 2 * * * find /home/printfarm/printfarm-test/logs -name "*.log" -mtime +7 -delete

# Docker cleanup weekly
0 3 * * 0 docker system prune -f --volumes
EOF
    
    # Устанавливаем crontab
    crontab /tmp/printfarm_cron
    rm -f /tmp/printfarm_cron
    
    log_success "Crontab configured"
    
    # Показываем текущий crontab
    log_info "Current crontab entries:"
    crontab -l | head -20
}

# Тест запуска
test_startup() {
    log_info "Testing startup..."
    
    # Запускаем скрипт
    ${PROJECT_DIR}/scripts/printfarm-startup.sh
    
    # Ждем несколько секунд
    sleep 30
    
    # Проверяем статус
    log_info "Checking startup results..."
    
    if curl -f http://localhost:13000/api/v1/health/ &>/dev/null; then
        log_success "✅ API is responding"
    else
        log_error "❌ API is not responding"
    fi
    
    if curl -f http://localhost:13000/ &>/dev/null; then
        log_success "✅ Frontend is responding"
    else
        log_error "❌ Frontend is not responding"
    fi
    
    # Показываем статус контейнеров
    log_info "Container status:"
    docker ps --filter "name=printfarm" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
}

# Основная функция
main() {
    echo ""
    echo "============================================================"
    echo "   PrintFarm v4.2.0 - Simple Autostart Setup"
    echo "============================================================"
    echo ""
    
    log_info "This will setup PrintFarm autostart using crontab (no sudo required)"
    log_info "Installation directory: $PROJECT_DIR"
    echo ""
    
    if [ "$1" != "--auto" ]; then
        read -p "Continue? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Setup cancelled"
            exit 0
        fi
    fi
    
    # Проверка базовых требований
    if [ ! -d "$PROJECT_DIR" ]; then
        log_error "Project directory $PROJECT_DIR not found!"
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker not found!"
        exit 1
    fi
    
    # Выполнение установки
    create_startup_script
    create_monitor_script
    setup_crontab
    
    log_success "============================================="
    log_success "Simple autostart setup completed!"
    log_success "============================================="
    echo ""
    log_info "Features enabled:"
    log_info "✅ Auto-start at system boot (after 60s delay)"
    log_info "✅ Health monitoring every 5 minutes"
    log_info "✅ Automatic restart if services fail"
    log_info "✅ Log cleanup (7 days retention)"
    log_info "✅ Docker cleanup (weekly)"
    echo ""
    
    if [ "$1" != "--auto" ]; then
        read -p "Test startup now? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            test_startup
        fi
    fi
    
    log_success "🚀 PrintFarm v4.2.0 autostart is ready!"
    log_info "The system will automatically start after reboot"
    log_info "Access: http://kemomail3.keenetic.pro:13000"
}

# Запуск
main "$@"