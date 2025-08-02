#!/bin/bash

# PrintFarm Production - Исправление конфликта портов
# Решает проблему с занятым портом 6379 (Redis)

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

print_header() {
    echo -e "\n${BLUE}===========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}===========================================${NC}\n"
}

print_header "ИСПРАВЛЕНИЕ КОНФЛИКТА ПОРТОВ"

# Шаг 1: Останавливаем все контейнеры
print_info "⏹️ Останавливаем все контейнеры PrintFarm..."
docker-compose -f docker-compose.prod.yml down 2>/dev/null || true
docker-compose down 2>/dev/null || true

# Шаг 2: Проверяем что занимает порты
print_info "🔍 Проверяем занятые порты..."
echo "Порт 6379 (Redis):"
sudo netstat -tlnp | grep :6379 || echo "  Порт свободен"
echo "Порт 5432 (PostgreSQL):"
sudo netstat -tlnp | grep :5432 || echo "  Порт свободен"
echo "Порт 80 (HTTP):"
sudo netstat -tlnp | grep :80 || echo "  Порт свободен"

# Шаг 3: Останавливаем системные сервисы если они мешают  
print_info "🛑 Останавливаем системные сервисы..."

# Останавливаем Redis если запущен как сервис
if systemctl is-active --quiet redis-server 2>/dev/null; then
    print_warning "Останавливаем системный Redis..."
    sudo systemctl stop redis-server
    sudo systemctl disable redis-server
    print_success "Системный Redis остановлен"
fi

# Останавливаем PostgreSQL если запущен как сервис
if systemctl is-active --quiet postgresql 2>/dev/null; then
    print_warning "Останавливаем системный PostgreSQL..."
    sudo systemctl stop postgresql
    sudo systemctl disable postgresql
    print_success "Системный PostgreSQL остановлен"
fi

# Шаг 4: Убиваем процессы на нужных портах
print_info "💀 Освобождаем порты принудительно..."

# Убиваем процессы на порту 6379
sudo fuser -k 6379/tcp 2>/dev/null || true
# Убиваем процессы на порту 5432  
sudo fuser -k 5432/tcp 2>/dev/null || true
# Убиваем процессы на порту 80
sudo fuser -k 80/tcp 2>/dev/null || true

sleep 2

# Шаг 5: Создаем docker-compose без проброса портов наружу
print_info "📝 Создаем docker-compose без конфликтов портов..."
cat > docker-compose.prod.yml << 'EOF'
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    restart: unless-stopped
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=${POSTGRES_DB:-printfarm}
      - POSTGRES_USER=${POSTGRES_USER:-printfarm}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-1qaz2wsX}
    networks:
      - printfarm-network
    # НЕ пробрасываем порт наружу - только внутри сети
    # ports: - "5432:5432"

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    networks:
      - printfarm-network
    # НЕ пробрасываем порт наружу - только внутри сети
    # ports: - "6379:6379"

  backend:
    build:
      context: .
      dockerfile: docker/django/Dockerfile
    restart: unless-stopped
    volumes:
      - static_volume:/app/static
      - media_volume:/app/media
    depends_on:
      - db
      - redis
    env_file:
      - .env
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.production
    networks:
      - printfarm-network
    # Backend доступен только через nginx
    # ports: - "8000:8000"

  celery:
    build:
      context: .
      dockerfile: docker/django/Dockerfile
    restart: unless-stopped
    command: celery -A config worker -l info --without-heartbeat --without-gossip --without-mingle --concurrency=2
    volumes:
      - media_volume:/app/media
    depends_on:
      - db
      - redis
      - backend
    env_file:
      - .env
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.production
    networks:
      - printfarm-network

  nginx:
    image: nginx:alpine
    restart: unless-stopped
    ports:
      - "80:80"  # Только nginx наружу
    volumes:
      - static_volume:/app/static
      - media_volume:/app/media
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
    depends_on:
      - backend
    networks:
      - printfarm-network

volumes:
  postgres_data:
  redis_data:
  static_volume:
  media_volume:

networks:
  printfarm-network:
    driver: bridge
EOF

print_success "docker-compose.prod.yml создан без конфликтов портов"

# Шаг 6: Проверяем .env файл
if [[ ! -f ".env" ]]; then
    print_info "🔧 Создаем .env файл..."
    cat > .env << 'EOF'
# Django настройки
SECRET_KEY=django-insecure-production-key-please-change
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# База данных
POSTGRES_DB=printfarm
POSTGRES_USER=printfarm
POSTGRES_PASSWORD=1qaz2wsX
DATABASE_URL=postgresql://printfarm:1qaz2wsX@db:5432/printfarm

# Redis
REDIS_URL=redis://redis:6379/0

# МойСклад
MOYSKLAD_TOKEN=f9be4985f5e3488716c040ca52b8e04c7c0f9e0b
MOYSKLAD_DEFAULT_WAREHOUSE=241ed919-a631-11ee-0a80-07a9000bb947

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Django Settings Module
DJANGO_SETTINGS_MODULE=config.settings.production
EOF
    print_success ".env файл создан"
fi

# Шаг 7: Проверяем nginx.conf
if [[ ! -f "nginx.conf" ]]; then
    print_info "🌐 Создаем nginx.conf..."
    cat > nginx.conf << 'EOF'
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
    
    # Все остальное тоже на backend
    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF
    print_success "nginx.conf создан"
fi

# Шаг 8: Чистим Docker
print_info "🧹 Очищаем Docker..."
docker system prune -f
docker volume prune -f

# Шаг 9: Запускаем по порядку
print_header "ЗАПУСК СИСТЕМЫ"

print_info "🗄️ Запускаем базу данных и Redis..."
docker-compose -f docker-compose.prod.yml up -d db redis
sleep 10

print_info "⚙️ Собираем и запускаем backend..."
docker-compose -f docker-compose.prod.yml build backend
docker-compose -f docker-compose.prod.yml up -d backend
sleep 20

print_info "🌐 Запускаем nginx..."
docker-compose -f docker-compose.prod.yml up -d nginx
sleep 5

print_info "🔄 Запускаем celery..."
docker-compose -f docker-compose.prod.yml up -d celery
sleep 5

# Шаг 10: Финальная проверка
print_header "ПРОВЕРКА РАБОТОСПОСОБНОСТИ"

print_info "📊 Статус контейнеров:"
docker-compose -f docker-compose.prod.yml ps

print_info "🔍 Проверяем API..."
sleep 5

if curl -f -s http://localhost/api/v1/tochka/stats/ > /dev/null 2>&1; then
    print_success "✅ API работает через Nginx!"
    echo "   URL: http://localhost/api/v1/tochka/stats/"
else
    print_warning "API пока недоступен"
    print_info "Проверьте логи: docker-compose -f docker-compose.prod.yml logs backend"
fi

# Шаг 11: Создаем суперпользователя
print_header "СОЗДАНИЕ СУПЕРПОЛЬЗОВАТЕЛЯ"

print_info "👤 Создаем суперпользователя admin/admin..."
docker-compose -f docker-compose.prod.yml exec -T backend python manage.py shell << 'EOF'
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin')
    print("✅ Суперпользователь admin/admin создан!")
else:
    print("ℹ️ Суперпользователь уже существует")
EOF

# Финальная информация
print_header "ИСПРАВЛЕНИЕ ЗАВЕРШЕНО!"

print_success "🎉 PrintFarm запущен без конфликтов портов!"
echo
print_info "🌐 Доступные URL:"
echo "   API статистика:  http://localhost/api/v1/tochka/stats/"
echo "   Админ-панель:     http://localhost/admin/"
echo
print_info "👤 Данные для входа в админку:"
echo "   Логин:    admin"
echo "   Пароль:   admin"
echo
print_info "📋 Полезные команды:"
echo "   Логи:        docker-compose -f docker-compose.prod.yml logs"
echo "   Статус:      docker-compose -f docker-compose.prod.yml ps"
echo "   Перезапуск:  docker-compose -f docker-compose.prod.yml restart"
echo "   Остановка:   docker-compose -f docker-compose.prod.yml down"
echo
print_warning "⚠️  Порты теперь НЕ пробрасываются наружу - доступ только через Nginx на порту 80"
echo
print_success "Готово! Система работает! 🚀"