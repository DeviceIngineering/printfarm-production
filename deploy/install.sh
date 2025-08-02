#!/bin/bash

# PrintFarm Production v4.6 - Автоматический установщик
# Поддерживает Ubuntu 20.04/22.04 LTS
# Автор: Claude Code Assistant
# Дата: 31 июля 2025

set -e  # Выход при любой ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции для цветного вывода
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

print_header() {
    echo -e "\n${BLUE}===========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}===========================================${NC}\n"
}

# Проверка прав
check_user() {
    if [[ $EUID -eq 0 ]]; then
        print_error "Не запускайте этот скрипт от пользователя root!"
        print_info "Переключитесь на пользователя printfarm: su - printfarm"
        exit 1
    fi
}

# Проверка ОС
check_os() {
    if [[ ! -f /etc/lsb-release ]]; then
        print_error "Этот скрипт поддерживает только Ubuntu!"
        exit 1
    fi
    
    . /etc/lsb-release
    if [[ "$DISTRIB_ID" != "Ubuntu" ]]; then
        print_error "Поддерживается только Ubuntu!"
        exit 1
    fi
    
    if [[ "$DISTRIB_RELEASE" != "20.04" && "$DISTRIB_RELEASE" != "22.04" ]]; then
        print_warning "Рекомендуется Ubuntu 20.04 или 22.04 LTS"
        read -p "Продолжить? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    print_success "Система: Ubuntu $DISTRIB_RELEASE"
}

# Ввод конфигурации
get_config() {
    print_header "НАСТРОЙКА КОНФИГУРАЦИИ"
    
    # База данных
    read -p "Database Name [printfarm_prod]: " DB_NAME
    DB_NAME=${DB_NAME:-printfarm_prod}
    
    read -p "Database User [printfarm_user]: " DB_USER  
    DB_USER=${DB_USER:-printfarm_user}
    
    while [[ -z "$DB_PASSWORD" ]]; do
        read -s -p "Database Password (обязательно): " DB_PASSWORD
        echo
        if [[ -z "$DB_PASSWORD" ]]; then
            print_error "Пароль базы данных не может быть пустым!"
        fi
    done
    
    # Django
    SECRET_KEY=$(openssl rand -base64 32)
    print_info "Django Secret Key сгенерирован автоматически"
    
    read -p "Allowed Hosts (домен или IP через запятую): " ALLOWED_HOSTS
    while [[ -z "$ALLOWED_HOSTS" ]]; do
        print_warning "Необходимо указать домен или IP адрес!"
        read -p "Allowed Hosts (например: mydomain.com,192.168.1.100): " ALLOWED_HOSTS
    done
    
    # МойСклад
    read -p "MoySklad Token [f9be4985f5e3488716c040ca52b8e04c7c0f9e0b]: " MOYSKLAD_TOKEN
    MOYSKLAD_TOKEN=${MOYSKLAD_TOKEN:-f9be4985f5e3488716c040ca52b8e04c7c0f9e0b}
    
    read -p "MoySklad Warehouse ID [241ed919-a631-11ee-0a80-07a9000bb947]: " MOYSKLAD_WAREHOUSE
    MOYSKLAD_WAREHOUSE=${MOYSKLAD_WAREHOUSE:-241ed919-a631-11ee-0a80-07a9000bb947}
    
    # Email (опционально)
    read -p "Email Host (опционально, для уведомлений): " EMAIL_HOST
    if [[ -n "$EMAIL_HOST" ]]; then
        read -p "Email User: " EMAIL_USER
        read -s -p "Email Password: " EMAIL_PASSWORD
        echo
    fi
    
    print_success "Конфигурация собрана!"
}

# Установка Docker
install_docker() {
    print_header "УСТАНОВКА DOCKER"
    
    if command -v docker &> /dev/null; then
        print_info "Docker уже установлен, проверяем версию..."
        docker --version
    else
        print_info "Устанавливаем Docker..."
        
        # Удаляем старые версии
        sudo apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true
        
        # Обновляем пакеты
        sudo apt-get update
        
        # Устанавливаем зависимости
        sudo apt-get install -y \
            apt-transport-https \
            ca-certificates \
            curl \
            gnupg \
            lsb-release \
            software-properties-common
        
        # Добавляем GPG ключ Docker
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
        
        # Добавляем репозиторий
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
        
        # Устанавливаем Docker
        sudo apt-get update
        sudo apt-get install -y docker-ce docker-ce-cli containerd.io
        
        # Добавляем пользователя в группу docker
        sudo usermod -aG docker $USER
        
        print_success "Docker установлен!"
    fi
    
    # Установка Docker Compose
    if command -v docker-compose &> /dev/null; then
        print_info "Docker Compose уже установлен, проверяем версию..."
        docker-compose --version
    else
        print_info "Устанавливаем Docker Compose..."
        
        sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
        
        print_success "Docker Compose установлен!"
    fi
    
    # Запускаем Docker
    sudo systemctl enable docker
    sudo systemctl start docker
    
    print_success "Docker настроен и запущен!"
}

# Клонирование репозитория
clone_repository() {
    print_header "КЛОНИРОВАНИЕ РЕПОЗИТОРИЯ"
    
    cd ~
    
    if [[ -d "printfarm-production" ]]; then
        print_warning "Папка printfarm-production уже существует"
        read -p "Удалить и клонировать заново? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf printfarm-production
        else
            cd printfarm-production
            git pull origin main
            print_success "Репозиторий обновлен!"
            return
        fi
    fi
    
    print_info "Клонируем репозиторий..."
    git clone https://github.com/DeviceIngineering/printfarm-production.git
    cd printfarm-production
    
    print_success "Репозиторий склонирован!"
}

# Создание .env файла
create_env_file() {
    print_header "СОЗДАНИЕ ФАЙЛА КОНФИГУРАЦИИ"
    
    cat > .env << EOF
# Django настройки
SECRET_KEY=$SECRET_KEY
DEBUG=False
ALLOWED_HOSTS=$ALLOWED_HOSTS

# База данных
POSTGRES_DB=$DB_NAME
POSTGRES_USER=$DB_USER
POSTGRES_PASSWORD=$DB_PASSWORD
DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@db:5432/$DB_NAME

# Redis
REDIS_URL=redis://redis:6379/0

# МойСклад
MOYSKLAD_TOKEN=$MOYSKLAD_TOKEN
MOYSKLAD_DEFAULT_WAREHOUSE=$MOYSKLAD_WAREHOUSE

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Email (если настроен)
EOF

    if [[ -n "$EMAIL_HOST" ]]; then
        cat >> .env << EOF
EMAIL_HOST=$EMAIL_HOST
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=$EMAIL_USER
EMAIL_HOST_PASSWORD=$EMAIL_PASSWORD
DEFAULT_FROM_EMAIL=$EMAIL_USER
EOF
    fi
    
    print_success "Файл конфигурации создан!"
}

# Создание production docker-compose
create_production_compose() {
    print_header "СОЗДАНИЕ PRODUCTION КОНФИГУРАЦИИ"
    
    cat > docker-compose.prod.yml << 'EOF'
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    restart: unless-stopped
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    networks:
      - printfarm-network

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    networks:
      - printfarm-network

  backend:
    build:
      context: .
      dockerfile: docker/django/Dockerfile.prod
    restart: unless-stopped
    volumes:
      - static_volume:/app/static
      - media_volume:/app/media
    depends_on:
      - db
      - redis
    environment:
      - SECRET_KEY=${SECRET_KEY}
      - DEBUG=False
      - ALLOWED_HOSTS=${ALLOWED_HOSTS}
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - MOYSKLAD_TOKEN=${MOYSKLAD_TOKEN}
      - MOYSKLAD_DEFAULT_WAREHOUSE=${MOYSKLAD_DEFAULT_WAREHOUSE}
      - CELERY_BROKER_URL=${CELERY_BROKER_URL}
      - CELERY_RESULT_BACKEND=${CELERY_RESULT_BACKEND}
    networks:
      - printfarm-network

  celery:
    build:
      context: .
      dockerfile: docker/django/Dockerfile.prod
    restart: unless-stopped
    command: celery -A config worker -l info
    volumes:
      - media_volume:/app/media
    depends_on:
      - db
      - redis
    environment:
      - SECRET_KEY=${SECRET_KEY}
      - DEBUG=False
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - MOYSKLAD_TOKEN=${MOYSKLAD_TOKEN}
      - MOYSKLAD_DEFAULT_WAREHOUSE=${MOYSKLAD_DEFAULT_WAREHOUSE}
      - CELERY_BROKER_URL=${CELERY_BROKER_URL}
      - CELERY_RESULT_BACKEND=${CELERY_RESULT_BACKEND}
    networks:
      - printfarm-network

  celery-beat:
    build:
      context: .
      dockerfile: docker/django/Dockerfile.prod
    restart: unless-stopped
    command: celery -A config beat -l info
    depends_on:
      - db
      - redis
    environment:
      - SECRET_KEY=${SECRET_KEY}
      - DEBUG=False
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - MOYSKLAD_TOKEN=${MOYSKLAD_TOKEN}
      - MOYSKLAD_DEFAULT_WAREHOUSE=${MOYSKLAD_DEFAULT_WAREHOUSE}
      - CELERY_BROKER_URL=${CELERY_BROKER_URL}
      - CELERY_RESULT_BACKEND=${CELERY_RESULT_BACKEND}
    networks:
      - printfarm-network

  frontend:
    build:
      context: .
      dockerfile: docker/react/Dockerfile.prod
    restart: unless-stopped
    volumes:
      - frontend_build:/app/build
    networks:
      - printfarm-network

  nginx:
    build:
      context: .
      dockerfile: docker/nginx/Dockerfile.prod
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - static_volume:/app/static
      - media_volume:/app/media
      - frontend_build:/app/frontend
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - backend
      - frontend
    networks:
      - printfarm-network

volumes:
  postgres_data:
  redis_data:
  static_volume:
  media_volume:
  frontend_build:

networks:
  printfarm-network:
    driver: bridge
EOF
    
    print_success "Production конфигурация создана!"
}

# Создание Dockerfile для production
create_production_dockerfiles() {
    print_header "СОЗДАНИЕ PRODUCTION DOCKERFILES"
    
    # Django Production Dockerfile
    mkdir -p docker/django
    cat > docker/django/Dockerfile.prod << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Системные зависимости
RUN apt-get update && apt-get install -y \
    postgresql-client \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Python зависимости
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY backend/ .

# Собираем статику
RUN python manage.py collectstatic --noinput

# Создаем пользователя
RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]
EOF

    # React Production Dockerfile
    mkdir -p docker/react
    cat > docker/react/Dockerfile.prod << 'EOF'
FROM node:18-alpine as build

WORKDIR /app

# Копируем package files
COPY frontend/package*.json ./
RUN npm ci --only=production

# Копируем исходники и собираем
COPY frontend/ .
RUN npm run build

# Production stage
FROM nginx:alpine
COPY --from=build /app/build /app/frontend
EOF

    # Nginx Production Dockerfile
    mkdir -p docker/nginx
    cat > docker/nginx/Dockerfile.prod << 'EOF'
FROM nginx:alpine

# Удаляем конфиг по умолчанию
RUN rm /etc/nginx/conf.d/default.conf

# Копируем наш конфиг
COPY docker/nginx/nginx.prod.conf /etc/nginx/conf.d/

# Создаем папки
RUN mkdir -p /app/static /app/media /app/frontend

EXPOSE 80 443
EOF

    # Nginx конфигурация
    cat > docker/nginx/nginx.prod.conf << 'EOF'
upstream backend {
    server backend:8000;
}

server {
    listen 80;
    server_name _;
    
    client_max_body_size 100M;
    
    # Static files
    location /static/ {
        alias /app/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Media files  
    location /media/ {
        alias /app/media/;
        expires 1y;
        add_header Cache-Control "public";
    }
    
    # API endpoints
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
    
    # Admin
    location /admin/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Frontend
    location / {
        root /app/frontend;
        try_files $uri $uri/ /index.html;
        expires 1h;
        add_header Cache-Control "public";
    }
}
EOF
    
    print_success "Production Dockerfiles созданы!"
}

# Сборка и запуск
build_and_run() {
    print_header "СБОРКА И ЗАПУСК ПРИЛОЖЕНИЯ"
    
    print_info "Собираем образы... (это может занять 10-15 минут)"
    docker-compose -f docker-compose.prod.yml build --no-cache
    
    print_info "Запускаем контейнеры..."
    docker-compose -f docker-compose.prod.yml up -d
    
    print_info "Ждем запуска сервисов..."
    sleep 30
    
    # Миграции применятся автоматически через entrypoint
    print_info "Проверяем статус миграций..."
    docker-compose -f docker-compose.prod.yml logs backend | tail -20
    
    print_success "Приложение запущено!"
}

# Создание суперпользователя
create_superuser() {
    print_header "СОЗДАНИЕ СУПЕРПОЛЬЗОВАТЕЛЯ"
    
    read -p "Логин администратора: " ADMIN_USER
    read -p "Email администратора: " ADMIN_EMAIL
    read -s -p "Пароль администратора: " ADMIN_PASSWORD
    echo
    
    docker-compose -f docker-compose.prod.yml exec backend python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='$ADMIN_USER').exists():
    User.objects.create_superuser('$ADMIN_USER', '$ADMIN_EMAIL', '$ADMIN_PASSWORD')
    print("✅ Суперпользователь создан!")
else:
    print("ℹ️ Пользователь уже существует!")
EOF
    
    print_success "Суперпользователь настроен!"
}

# Настройка автозапуска
setup_autostart() {
    print_header "НАСТРОЙКА АВТОЗАПУСКА"
    
    # Создаем systemd service
    sudo tee /etc/systemd/system/printfarm.service > /dev/null << EOF
[Unit]
Description=PrintFarm Production
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/printfarm/printfarm-production
ExecStart=/usr/local/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker-compose.prod.yml down
User=printfarm
Group=printfarm

[Install]
WantedBy=multi-user.target
EOF

    # Включаем сервис
    sudo systemctl daemon-reload
    sudo systemctl enable printfarm.service
    
    print_success "Автозапуск настроен!"
}

# Создание скриптов управления
create_management_scripts() {
    print_header "СОЗДАНИЕ СКРИПТОВ УПРАВЛЕНИЯ"
    
    # Скрипт обновления
    cat > deploy/update.sh << 'EOF'
#!/bin/bash
set -e

echo "🔄 Обновление PrintFarm Production..."

# Останавливаем сервисы
docker-compose -f docker-compose.prod.yml down

# Получаем обновления
git pull origin main

# Пересобираем образы
docker-compose -f docker-compose.prod.yml build --no-cache

# Запускаем сервисы
docker-compose -f docker-compose.prod.yml up -d

# Применяем миграции
sleep 30
docker-compose -f docker-compose.prod.yml exec -T backend python manage.py migrate

echo "✅ Обновление завершено!"
EOF

    # Скрипт резервного копирования
    cat > deploy/backup.sh << 'EOF'
#!/bin/bash
set -e

BACKUP_DIR="/home/printfarm/backups"
DATE=$(date +%Y-%m-%d_%H-%M)
BACKUP_FILE="backup_$DATE.tar.gz"

mkdir -p $BACKUP_DIR

echo "💾 Создание резервной копии..."

# Бэкап базы данных
docker-compose -f docker-compose.prod.yml exec -T db pg_dump -U $POSTGRES_USER $POSTGRES_DB > $BACKUP_DIR/database_$DATE.sql

# Бэкап файлов
tar -czf $BACKUP_DIR/$BACKUP_FILE \
    --exclude='*.log' \
    --exclude='__pycache__' \
    --exclude='node_modules' \
    .

echo "✅ Резервная копия создана: $BACKUP_FILE"
EOF

    # Скрипт диагностики
    cat > deploy/diagnostics.sh << 'EOF'
#!/bin/bash

echo "🔍 Диагностическая информация PrintFarm"
echo "========================================"
echo
echo "Дата: $(date)"
echo "Пользователь: $(whoami)"
echo "Система: $(lsb_release -d)"
echo
echo "Docker версия:"
docker --version
echo
echo "Docker Compose версия:"
docker-compose --version
echo
echo "Статус контейнеров:"
docker-compose -f docker-compose.prod.yml ps
echo
echo "Использование ресурсов:"
docker stats --no-stream
echo
echo "Место на диске:"
df -h
echo
echo "Логи backend (последние 50 строк):"
docker-compose -f docker-compose.prod.yml logs --tail=50 backend
EOF

    chmod +x deploy/*.sh
    
    print_success "Скрипты управления созданы!"
}

# Основная функция
main() {
    print_header "PRINTFARM PRODUCTION v4.6 - АВТОМАТИЧЕСКИЙ УСТАНОВЩИК"
    
    print_info "Этот скрипт установит и настроит PrintFarm Production на вашем сервере"
    print_warning "Убедитесь, что вы запускаете его от пользователя printfarm (не root!)"
    
    read -p "Продолжить установку? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Установка отменена"
        exit 0
    fi
    
    # Выполняем все этапы
    check_user
    check_os
    get_config
    install_docker
    clone_repository
    create_env_file
    create_production_compose
    create_production_dockerfiles
    build_and_run
    create_superuser
    setup_autostart
    create_management_scripts
    
    # Финальная информация
    print_header "УСТАНОВКА ЗАВЕРШЕНА УСПЕШНО! 🎉"
    print_success "PrintFarm Production v4.6 готов к работе!"
    echo
    print_info "🌐 Откройте в браузере: http://$ALLOWED_HOSTS"
    print_info "👨‍💼 Админ-панель: http://$ALLOWED_HOSTS/admin/"
    print_info "📊 API документация: http://$ALLOWED_HOSTS/api/"
    echo
    print_info "📁 Папка проекта: /home/printfarm/printfarm-production"
    print_info "🔧 Управление: docker-compose -f docker-compose.prod.yml [команда]"
    print_info "📋 Логи: docker-compose -f docker-compose.prod.yml logs [сервис]"
    echo
    print_warning "⚠️  Не забудьте настроить SSL сертификат для HTTPS!"
    print_info "📚 Полная документация: DEPLOYMENT_GUIDE.md"
    echo
    print_success "Спасибо за использование PrintFarm! 🚀"
}

# Запускаем установку
main "$@"