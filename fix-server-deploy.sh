#!/bin/bash

# Скрипт для исправления деплоя на сервере
echo "🔧 Fixing PrintFarm deployment..."

# Переход в директорию проекта
cd ~/printfarm-test || exit 1

# Остановка контейнеров
echo "⏹️  Stopping containers..."
docker-compose -f docker-compose.server.yml down

# Очистка старых образов
docker system prune -f

# Получение последних изменений
echo "📦 Pulling latest changes..."
git pull origin test_v1_clean

# Пересоздание .env файла с правильными настройками
SERVER_IP=$(hostname -I | awk '{print $1}')
echo "⚙️  Configuring for IP: $SERVER_IP"

cat > .env.production << EOF
# Django Settings
SECRET_KEY=$(openssl rand -base64 32)
DEBUG=False
ALLOWED_HOSTS=$SERVER_IP,localhost,127.0.0.1,*

# Database
POSTGRES_DB=printfarm_db
POSTGRES_USER=printfarm_user
POSTGRES_PASSWORD=printfarm2024pass
DATABASE_URL=postgresql://printfarm_user:printfarm2024pass@db:5432/printfarm_db

# Redis
REDIS_URL=redis://redis:6379/0

# МойСклад API
MOYSKLAD_TOKEN=f9be4985f5e3488716c040ca52b8e04c7c0f9e0b
MOYSKLAD_DEFAULT_WAREHOUSE=241ed919-a631-11ee-0a80-07a9000bb947

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Frontend
REACT_APP_API_URL=http://$SERVER_IP:8001/api/v1

# CORS Settings
CORS_ALLOWED_ORIGINS=http://$SERVER_IP:8090,http://localhost:8090,http://$SERVER_IP:3000

# Security
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
EOF

# Сборка образов
echo "🐳 Building Docker images..."
docker-compose -f docker-compose.server.yml build --no-cache

# Запуск контейнеров
echo "🚀 Starting containers..."
docker-compose -f docker-compose.server.yml up -d

# Ожидание запуска БД
echo "⏳ Waiting for services to start..."
sleep 20

# Миграции
echo "🗄️  Running migrations..."
docker-compose -f docker-compose.server.yml exec -T backend python manage.py migrate

# Создание админа
echo "👤 Creating admin user..."
docker-compose -f docker-compose.server.yml exec -T backend python manage.py shell << PYTHON
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@test.com', 'admin123')
    print('Admin user created')
else:
    print('Admin already exists')
PYTHON

# Сбор статики
echo "📁 Collecting static files..."
docker-compose -f docker-compose.server.yml exec -T backend python manage.py collectstatic --noinput

# Проверка статуса
echo ""
echo "📊 Container status:"
docker-compose -f docker-compose.server.yml ps

# Проверка логов
echo ""
echo "📝 Recent logs:"
docker-compose -f docker-compose.server.yml logs --tail=20

echo ""
echo "✅ Fix completed!"
echo "================================"
echo "🌐 Access points:"
echo "   Web: http://$SERVER_IP:8090"
echo "   API: http://$SERVER_IP:8001"
echo "   Admin: http://$SERVER_IP:8001/admin (admin/admin123)"
echo ""
echo "🔍 Check logs: docker-compose -f docker-compose.server.yml logs -f"
echo "================================"