#!/bin/bash
# ============================================================
# PrintFarm v4.1.8 - Remote Deployment Script
# ============================================================
# Скрипт для развертывания на удаленном тестовом сервере
# Автоматическая загрузка и запуск с нестандартными портами
# ============================================================

set -e

# Конфигурация для удаленного сервера
REMOTE_HOST="kemomail3.keenetic.pro"
REMOTE_USER="printfarm"
REMOTE_PORT="2132"
PROJECT_NAME="printfarm-test"
REMOTE_DIR="/home/${REMOTE_USER}/${PROJECT_NAME}"

# Уникальные порты для тестовой среды (избежание конфликтов)
POSTGRES_PORT="15432"
REDIS_PORT="16379"
BACKEND_PORT="18000"
FRONTEND_PORT="13000"
NGINX_PORT="18080"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Функции логирования
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

# Проверка SSH доступа
check_ssh_access() {
    log_info "Проверка SSH доступа к $REMOTE_HOST..."
    
    if ssh -o ConnectTimeout=10 -p $REMOTE_PORT $REMOTE_USER@$REMOTE_HOST "echo 'SSH connection successful'" >/dev/null 2>&1; then
        log_success "SSH доступ работает"
    else
        log_error "Не удается подключиться к серверу $REMOTE_HOST"
        log_info "Убедитесь что:"
        log_info "  1. SSH ключи настроены"
        log_info "  2. Сервер доступен"
        log_info "  3. Правильные данные в переменных REMOTE_HOST, REMOTE_USER, REMOTE_PORT"
        exit 1
    fi
}

# Проверка Docker на удаленном сервере
check_remote_docker() {
    log_info "Проверка Docker на удаленном сервере..."
    
    if ssh -p $REMOTE_PORT $REMOTE_USER@$REMOTE_HOST "docker --version && docker-compose --version" >/dev/null 2>&1; then
        log_success "Docker и Docker Compose установлены"
    else
        log_error "Docker не установлен на удаленном сервере"
        log_info "Установите Docker и Docker Compose на сервере:"
        log_info "  curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh"
        log_info "  sudo apt install docker-compose-plugin"
        exit 1
    fi
}

# Проверка портов на удаленном сервере
check_remote_ports() {
    log_info "Проверка доступности портов на удаленном сервере..."
    
    PORTS=($POSTGRES_PORT $REDIS_PORT $BACKEND_PORT $FRONTEND_PORT $NGINX_PORT)
    PORT_NAMES=("PostgreSQL" "Redis" "Backend" "Frontend" "Nginx")
    
    for i in "${!PORTS[@]}"; do
        PORT=${PORTS[$i]}
        NAME=${PORT_NAMES[$i]}
        
        if ssh -p $REMOTE_PORT $REMOTE_USER@$REMOTE_HOST "ss -tlnp | grep :$PORT" >/dev/null 2>&1; then
            log_warning "Порт $PORT ($NAME) занят на удаленном сервере"
        else
            log_success "Порт $PORT ($NAME) свободен"
        fi
    done
}

# Создание удаленной директории
create_remote_directory() {
    log_info "Создание директории проекта на удаленном сервере..."
    
    ssh -p $REMOTE_PORT $REMOTE_USER@$REMOTE_HOST "
        mkdir -p $REMOTE_DIR
        mkdir -p $REMOTE_DIR/logs
        mkdir -p $REMOTE_DIR/docker
    "
    
    log_success "Удаленная директория создана: $REMOTE_DIR"
}

# Синхронизация файлов
sync_files() {
    log_info "Синхронизация файлов проекта..."
    
    # Исключаем ненужные файлы и директории
    rsync -avz --delete \
        --exclude='.git' \
        --exclude='node_modules' \
        --exclude='__pycache__' \
        --exclude='.env' \
        --exclude='*.pyc' \
        --exclude='*.log' \
        --exclude='backend/media' \
        --exclude='backend/static' \
        --exclude='frontend/build' \
        --exclude='*.xlsx' \
        --exclude='*.tar.gz' \
        -e "ssh -p $REMOTE_PORT" \
        ./ $REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/
    
    log_success "Файлы синхронизированы"
}

# Создание .env файла для удаленного сервера
create_remote_env() {
    log_info "Создание .env файла для удаленного сервера..."
    
    ssh -p $REMOTE_PORT $REMOTE_USER@$REMOTE_HOST "cat > $REMOTE_DIR/.env.remote << 'EOF'
# PrintFarm Remote Test Environment v4.1.8
APP_VERSION=4.1.8
ENVIRONMENT=test
DEBUG=False

# Database (уникальный порт)
DB_USER=printfarm_remote
DB_PASSWORD=printfarm_remote_$(date +%Y)
DB_NAME=printfarm_remote
DATABASE_URL=postgresql://printfarm_remote:printfarm_remote_$(date +%Y)@printfarm-remote-db:5432/printfarm_remote

# Redis (уникальный порт)
REDIS_PASSWORD=redis_remote_$(date +%Y)
REDIS_URL=redis://:redis_remote_$(date +%Y)@printfarm-remote-redis:6379/0

# Celery
CELERY_BROKER_URL=redis://:redis_remote_$(date +%Y)@printfarm-remote-redis:6379/0
CELERY_RESULT_BACKEND=redis://:redis_remote_$(date +%Y)@printfarm-remote-redis:6379/0

# Django
SECRET_KEY=remote-secret-key-$(date +%s)-change-in-production
ALLOWED_HOSTS=localhost,127.0.0.1,printfarm-remote-backend,$REMOTE_HOST

# MoySklad (используем реальные токены)
MOYSKLAD_TOKEN=f9be4985f5e3488716c040ca52b8e04c7c0f9e0b
MOYSKLAD_DEFAULT_WAREHOUSE=241ed919-a631-11ee-0a80-07a9000bb947

# Frontend
REACT_APP_API_URL=http://$REMOTE_HOST:$BACKEND_PORT/api/v1
REACT_APP_VERSION=4.1.8
REACT_APP_ENVIRONMENT=remote-test

# Monitoring
LOG_LEVEL=INFO
ENABLE_MONITORING=True
EOF"

    log_success "Remote .env файл создан"
}

# Создание docker-compose для удаленного сервера
create_remote_docker_compose() {
    log_info "Создание docker-compose.remote.yml..."
    
    ssh -p $REMOTE_PORT $REMOTE_USER@$REMOTE_HOST "cat > $REMOTE_DIR/docker-compose.remote.yml << 'EOF'
version: '3.8'

services:
  # PostgreSQL с уникальным именем и портом
  printfarm-remote-db:
    image: postgres:15-alpine
    container_name: printfarm_remote_db
    restart: unless-stopped
    environment:
      POSTGRES_DB: printfarm_remote
      POSTGRES_USER: printfarm_remote
      POSTGRES_PASSWORD: printfarm_remote_$(date +%Y)
      POSTGRES_HOST_AUTH_METHOD: md5
    volumes:
      - printfarm_remote_postgres:/var/lib/postgresql/data
    ports:
      - \"$POSTGRES_PORT:5432\"
    networks:
      - printfarm_remote_net
    healthcheck:
      test: [\"CMD-SHELL\", \"pg_isready -U printfarm_remote\"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis с уникальным именем и портом  
  printfarm-remote-redis:
    image: redis:7-alpine
    container_name: printfarm_remote_redis
    restart: unless-stopped
    command: redis-server --appendonly yes --requirepass redis_remote_$(date +%Y)
    volumes:
      - printfarm_remote_redis:/data
    ports:
      - \"$REDIS_PORT:6379\"
    networks:
      - printfarm_remote_net
    healthcheck:
      test: [\"CMD\", \"redis-cli\", \"--raw\", \"incr\", \"ping\"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Backend Django
  printfarm-remote-backend:
    build:
      context: .
      dockerfile: docker/backend.Dockerfile
      args:
        ENVIRONMENT: test
    container_name: printfarm_remote_backend
    restart: unless-stopped
    env_file: .env.remote
    volumes:
      - ./backend:/app
      - printfarm_remote_static:/app/static
      - printfarm_remote_media:/app/media
      - ./logs:/app/logs
    ports:
      - \"$BACKEND_PORT:8000\"
    depends_on:
      printfarm-remote-db:
        condition: service_healthy
      printfarm-remote-redis:
        condition: service_healthy
    networks:
      - printfarm_remote_net
    healthcheck:
      test: [\"CMD-SHELL\", \"curl -f http://localhost:8000/api/v1/health/ || exit 1\"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Celery Worker
  printfarm-remote-celery:
    build:
      context: .
      dockerfile: docker/backend.Dockerfile
    container_name: printfarm_remote_celery
    restart: unless-stopped
    env_file: .env.remote
    volumes:
      - ./backend:/app
      - ./logs:/app/logs
    depends_on:
      - printfarm-remote-db
      - printfarm-remote-redis
      - printfarm-remote-backend
    networks:
      - printfarm_remote_net
    command: celery -A config worker -l info --logfile=/app/logs/celery.log

  # Celery Beat
  printfarm-remote-celery-beat:
    build:
      context: .
      dockerfile: docker/backend.Dockerfile
    container_name: printfarm_remote_celery_beat
    restart: unless-stopped
    env_file: .env.remote
    volumes:
      - ./backend:/app
      - ./logs:/app/logs
    depends_on:
      - printfarm-remote-db
      - printfarm-remote-redis
      - printfarm-remote-backend
    networks:
      - printfarm_remote_net
    command: celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler --logfile=/app/logs/celery-beat.log

  # Frontend React
  printfarm-remote-frontend:
    build:
      context: .
      dockerfile: docker/frontend.Dockerfile
      args:
        REACT_APP_API_URL: http://$REMOTE_HOST:$BACKEND_PORT/api/v1
        REACT_APP_VERSION: 4.1.8
        REACT_APP_ENVIRONMENT: remote-test
    container_name: printfarm_remote_frontend
    restart: unless-stopped
    ports:
      - \"$FRONTEND_PORT:3000\"
    depends_on:
      - printfarm-remote-backend
    networks:
      - printfarm_remote_net
    healthcheck:
      test: [\"CMD-SHELL\", \"curl -f http://localhost:3000 || exit 1\"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Nginx Load Balancer
  printfarm-remote-nginx:
    image: nginx:alpine
    container_name: printfarm_remote_nginx
    restart: unless-stopped
    ports:
      - \"$NGINX_PORT:80\"
    volumes:
      - ./docker/nginx.remote.conf:/etc/nginx/nginx.conf:ro
      - printfarm_remote_static:/usr/share/nginx/html/static:ro
      - printfarm_remote_media:/usr/share/nginx/html/media:ro
      - ./logs/nginx:/var/log/nginx
    depends_on:
      - printfarm-remote-backend
      - printfarm-remote-frontend
    networks:
      - printfarm_remote_net
    healthcheck:
      test: [\"CMD-SHELL\", \"wget -O /dev/null http://localhost || exit 1\"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  printfarm_remote_postgres:
    name: printfarm_remote_postgres
  printfarm_remote_redis:
    name: printfarm_remote_redis
  printfarm_remote_static:
    name: printfarm_remote_static
  printfarm_remote_media:
    name: printfarm_remote_media

networks:
  printfarm_remote_net:
    name: printfarm_remote_net
    driver: bridge
EOF"

    log_success "docker-compose.remote.yml создан"
}

# Создание Nginx конфигурации для удаленного сервера
create_nginx_config() {
    log_info "Создание Nginx конфигурации для удаленного сервера..."
    
    ssh -p $REMOTE_PORT $REMOTE_USER@$REMOTE_HOST "mkdir -p $REMOTE_DIR/docker"
    
    ssh -p $REMOTE_PORT $REMOTE_USER@$REMOTE_HOST "cat > $REMOTE_DIR/docker/nginx.remote.conf << 'EOF'
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '\$remote_addr - \$remote_user [\$time_local] \"\$request\" '
                    '\$status \$body_bytes_sent \"\$http_referer\" '
                    '\"\$http_user_agent\" \"\$http_x_forwarded_for\"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    client_max_body_size 100M;

    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript 
               application/json application/javascript application/xml+rss;

    upstream backend {
        server printfarm-remote-backend:8000 fail_timeout=0;
        keepalive 32;
    }

    upstream frontend {
        server printfarm-remote-frontend:3000 fail_timeout=0;
        keepalive 32;
    }

    server {
        listen 80 default_server;
        server_name _;

        add_header X-Frame-Options \"SAMEORIGIN\" always;
        add_header X-XSS-Protection \"1; mode=block\" always;
        add_header X-Content-Type-Options \"nosniff\" always;

        location /api/ {
            proxy_pass http://backend;
            proxy_set_header Host \$http_host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
            proxy_redirect off;
            
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        location /admin/ {
            proxy_pass http://backend;
            proxy_set_header Host \$http_host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
            proxy_redirect off;
        }

        location /static/ {
            alias /usr/share/nginx/html/static/;
            expires 30d;
            add_header Cache-Control \"public, immutable\";
        }

        location /media/ {
            alias /usr/share/nginx/html/media/;
            expires 7d;
            add_header Cache-Control \"public\";
        }

        location /health {
            access_log off;
            add_header Content-Type \"text/plain\";
            return 200 \"PrintFarm Remote v4.1.8 - healthy\";
        }

        location / {
            proxy_pass http://frontend;
            proxy_set_header Host \$http_host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
            proxy_redirect off;
        }
    }
}
EOF"

    log_success "Nginx конфигурация создана"
}

# Сборка и запуск на удаленном сервере
deploy_remote() {
    log_info "Запуск развертывания на удаленном сервере..."
    
    ssh -p $REMOTE_PORT $REMOTE_USER@$REMOTE_HOST "
        cd $REMOTE_DIR
        
        # Остановка существующих контейнеров
        docker-compose -f docker-compose.remote.yml down --volumes --remove-orphans 2>/dev/null || true
        
        # Сборка образов
        docker-compose -f docker-compose.remote.yml build --no-cache
        
        # Запуск контейнеров
        docker-compose -f docker-compose.remote.yml up -d
        
        echo 'Waiting for services...'
        sleep 20
        
        # Применение миграций
        docker-compose -f docker-compose.remote.yml exec -T printfarm-remote-backend python manage.py migrate --noinput
        
        # Сбор статики
        docker-compose -f docker-compose.remote.yml exec -T printfarm-remote-backend python manage.py collectstatic --noinput
        
        # Создание суперпользователя
        docker-compose -f docker-compose.remote.yml exec -T printfarm-remote-backend python manage.py shell -c \"
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@printfarm.test', 'admin123')
    print('Superuser created')
\" 2>/dev/null || echo 'Superuser already exists'
    "
    
    log_success "Развертывание завершено"
}

# Проверка состояния удаленного развертывания
check_remote_status() {
    log_info "Проверка состояния удаленного развертывания..."
    
    # Проверка контейнеров
    ssh -p $REMOTE_PORT $REMOTE_USER@$REMOTE_HOST "cd $REMOTE_DIR && docker-compose -f docker-compose.remote.yml ps"
    
    # Проверка health checks
    log_info "Проверка health checks..."
    
    if ssh -p $REMOTE_PORT $REMOTE_USER@$REMOTE_HOST "curl -f http://localhost:$BACKEND_PORT/api/v1/health/" >/dev/null 2>&1; then
        log_success "Backend health check: OK"
    else
        log_warning "Backend health check: FAILED"
    fi
    
    if ssh -p $REMOTE_PORT $REMOTE_USER@$REMOTE_HOST "curl -f http://localhost:$FRONTEND_PORT" >/dev/null 2>&1; then
        log_success "Frontend health check: OK"  
    else
        log_warning "Frontend health check: FAILED"
    fi
    
    log_info ""
    log_success "==================================================="
    log_success "PrintFarm v4.1.8 Remote Deployment Complete!"
    log_success "==================================================="
    log_info ""
    log_info "Remote server access:"
    log_info "  - Frontend:    http://$REMOTE_HOST:$FRONTEND_PORT"
    log_info "  - Backend API: http://$REMOTE_HOST:$BACKEND_PORT/api/v1/"
    log_info "  - Admin Panel: http://$REMOTE_HOST:$BACKEND_PORT/admin/"
    log_info "  - Nginx Proxy: http://$REMOTE_HOST:$NGINX_PORT"
    log_info ""
    log_info "Database access:"
    log_info "  - PostgreSQL:  $REMOTE_HOST:$POSTGRES_PORT"
    log_info "  - Redis:       $REMOTE_HOST:$REDIS_PORT"
    log_info ""
    log_info "SSH commands for management:"
    log_info "  ssh -p $REMOTE_PORT $REMOTE_USER@$REMOTE_HOST \"cd $REMOTE_DIR && docker-compose -f docker-compose.remote.yml logs -f\""
    log_info "  ssh -p $REMOTE_PORT $REMOTE_USER@$REMOTE_HOST \"cd $REMOTE_DIR && docker-compose -f docker-compose.remote.yml restart\""
    log_info ""
}

# Основная функция
main() {
    echo ""
    echo "============================================================"
    echo "   PrintFarm v4.1.8 - Remote Deployment Script"
    echo "============================================================"
    echo ""
    
    log_info "Remote server: $REMOTE_HOST"
    log_info "Unique ports: PostgreSQL=$POSTGRES_PORT, Redis=$REDIS_PORT, Backend=$BACKEND_PORT, Frontend=$FRONTEND_PORT, Nginx=$NGINX_PORT"
    echo ""
    
    check_ssh_access
    check_remote_docker
    check_remote_ports
    create_remote_directory
    sync_files
    create_remote_env
    create_remote_docker_compose
    create_nginx_config
    deploy_remote
    check_remote_status
}

# Обработка аргументов
case "${1:-}" in
    --help|-h)
        echo "Remote Deployment Script for PrintFarm v4.1.8"
        echo ""
        echo "Usage: $0 [OPTION]"
        echo ""
        echo "Options:"
        echo "  --help, -h          Show this help"
        echo "  --config            Configure remote server details"
        echo "  --sync              Sync files only"
        echo "  --status            Check remote deployment status"
        echo "  --stop              Stop remote containers"
        echo "  --logs              Show remote logs"
        echo ""
        echo "Configuration:"
        echo "  Edit variables at the top of this script:"
        echo "  - REMOTE_HOST: your server hostname/IP"
        echo "  - REMOTE_USER: SSH username"
        echo "  - REMOTE_PORT: SSH port (default: 22)"
        echo ""
        ;;
    --config)
        log_info "Current configuration:"
        log_info "  Remote host: $REMOTE_HOST"
        log_info "  Remote user: $REMOTE_USER"
        log_info "  SSH port: $REMOTE_PORT"
        log_info "  Remote directory: $REMOTE_DIR"
        log_info ""
        log_info "Edit the variables at the top of this script to change configuration"
        ;;
    --sync)
        check_ssh_access
        create_remote_directory
        sync_files
        log_success "Files synchronized successfully"
        ;;
    --status)
        check_ssh_access
        check_remote_status
        ;;
    --stop)
        log_info "Stopping remote containers..."
        ssh -p $REMOTE_PORT $REMOTE_USER@$REMOTE_HOST "cd $REMOTE_DIR && docker-compose -f docker-compose.remote.yml down"
        log_success "Remote containers stopped"
        ;;
    --logs)
        ssh -p $REMOTE_PORT $REMOTE_USER@$REMOTE_HOST "cd $REMOTE_DIR && docker-compose -f docker-compose.remote.yml logs -f"
        ;;
    *)
        main
        ;;
esac