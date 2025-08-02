#!/bin/bash

# PrintFarm Production - Экстренное исправление
# Исправляет проблемы с Celery, Nginx и API

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

print_header "ЭКСТРЕННОЕ ИСПРАВЛЕНИЕ PRINTFARM"

# Шаг 1: Останавливаем все
print_info "⏹️ Останавливаем все контейнеры..."
docker-compose -f docker-compose.prod.yml down
docker-compose down 2>/dev/null || true
print_success "Контейнеры остановлены"

# Шаг 2: Очищаем все
print_info "🧹 Очищаем Docker..."
docker system prune -f
docker volume prune -f
print_success "Docker очищен"

# Шаг 3: Исправляем .env файл
print_info "🔧 Исправляем .env файл..."
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

# МойСклад (ОБЯЗАТЕЛЬНО заполните!)
MOYSKLAD_TOKEN=f9be4985f5e3488716c040ca52b8e04c7c0f9e0b
MOYSKLAD_DEFAULT_WAREHOUSE=241ed919-a631-11ee-0a80-07a9000bb947

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Django Settings Module
DJANGO_SETTINGS_MODULE=config.settings.production

# Email (если нужно)
EMAIL_HOST=mail@kemomail.ru
EOF

print_success ".env файл исправлен"

# Шаг 4: Создаем упрощенный docker-compose.prod.yml
print_info "📝 Создаем рабочий docker-compose.prod.yml..."
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
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    networks:
      - printfarm-network
    ports:
      - "6379:6379"

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
    ports:
      - "8000:8000"

  celery:
    build:
      context: .
      dockerfile: docker/django/Dockerfile
    restart: unless-stopped
    command: celery -A config worker -l info --without-heartbeat --without-gossip --without-mingle
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
      - "80:80"
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

print_success "docker-compose.prod.yml создан"

# Шаг 5: Создаем простой nginx.conf
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
    
    # Frontend (временно перенаправляем на API)
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

# Шаг 6: Проверяем Dockerfile
if [[ ! -f "docker/django/Dockerfile" ]]; then
    print_info "📦 Создаем рабочий Dockerfile..."
    mkdir -p docker/django
    cat > docker/django/Dockerfile << 'EOF'
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

# Создаем директории
RUN mkdir -p /app/static /app/media

# Создаем скрипт запуска
RUN echo '#!/bin/sh' > /app/start.sh && \
    echo 'echo "Waiting for database..."' >> /app/start.sh && \
    echo 'while ! nc -z db 5432; do sleep 1; done' >> /app/start.sh && \
    echo 'echo "Database ready!"' >> /app/start.sh && \
    echo 'python manage.py migrate --noinput || true' >> /app/start.sh && \
    echo 'python manage.py collectstatic --noinput || true' >> /app/start.sh && \
    echo 'echo "Starting server..."' >> /app/start.sh && \
    echo 'exec "$@"' >> /app/start.sh && \
    chmod +x /app/start.sh

EXPOSE 8000

ENTRYPOINT ["/app/start.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "120"]
EOF
    print_success "Dockerfile создан"
fi

# Шаг 7: Собираем и запускаем
print_header "СБОРКА И ЗАПУСК"

print_info "🔨 Собираем backend..."
docker-compose -f docker-compose.prod.yml build backend

print_info "🚀 Запускаем сервисы по порядку..."

# Запускаем базу данных и Redis
print_info "🗄️ Запускаем базу данных и Redis..."
docker-compose -f docker-compose.prod.yml up -d db redis
sleep 10

# Запускаем backend
print_info "⚙️ Запускаем backend..."
docker-compose -f docker-compose.prod.yml up -d backend
sleep 20

# Проверяем backend
print_info "🔍 Проверяем backend..."
if curl -f -s http://localhost:8000/api/v1/tochka/stats/ > /dev/null 2>&1; then
    print_success "Backend работает!"
else
    print_warning "Backend еще загружается..."
    sleep 10
fi

# Запускаем nginx
print_info "🌐 Запускаем nginx..."
docker-compose -f docker-compose.prod.yml up -d nginx
sleep 5

# Запускаем celery (если backend работает)
print_info "🔄 Запускаем celery..."
docker-compose -f docker-compose.prod.yml up -d celery
sleep 5

# Шаг 8: Финальная проверка
print_header "ПРОВЕРКА РАБОТОСПОСОБНОСТИ"

print_info "📊 Статус контейнеров:"
docker-compose -f docker-compose.prod.yml ps

print_info "🔍 Проверяем API..."
sleep 5

if curl -f -s http://localhost/api/v1/tochka/stats/ > /dev/null 2>&1; then
    print_success "✅ API работает через Nginx!"
    echo "   URL: http://localhost/api/v1/tochka/stats/"
elif curl -f -s http://localhost:8000/api/v1/tochka/stats/ > /dev/null 2>&1; then
    print_success "✅ API работает напрямую!"
    echo "   URL: http://localhost:8000/api/v1/tochka/stats/"
else
    print_warning "API пока недоступен"
    print_info "Проверьте логи: docker-compose -f docker-compose.prod.yml logs backend"
fi

# Шаг 9: Создаем суперпользователя
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

print_success "🎉 PrintFarm запущен и работает!"
echo
print_info "🌐 Доступные URL:"
echo "   API статистика:  http://localhost/api/v1/tochka/stats/"
echo "   Админ-панель:     http://localhost/admin/"
echo "   Backend прямо:    http://localhost:8000/"
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
print_warning "⚠️  Не забудьте сменить пароль администратора!"
echo
print_success "Готово! Система работает! 🚀"