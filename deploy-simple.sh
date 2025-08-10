#!/bin/bash

echo "🚀 Simple PrintFarm Deploy"
echo "=========================="

# Остановка старых контейнеров
echo "⏹️  Stopping old containers..."
docker-compose -f docker-compose.simple.yml down 2>/dev/null || true
docker-compose -f docker-compose.server.yml down 2>/dev/null || true

# Очистка
docker system prune -f

# Получение IP
SERVER_IP=$(hostname -I | awk '{print $1}')
echo "📍 Server IP: $SERVER_IP"

# Запуск с простой конфигурацией
echo "🐳 Starting services..."
docker-compose -f docker-compose.simple.yml up -d --build

# Ожидание
echo "⏳ Waiting for services..."
sleep 20

# Миграции
echo "🗄️  Running migrations..."
docker-compose -f docker-compose.simple.yml exec -T backend python manage.py migrate || echo "Migrations skipped"

# Создание админа
echo "👤 Creating admin..."
docker-compose -f docker-compose.simple.yml exec -T backend python manage.py shell << EOF
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@test.com', 'admin123')
    print('Admin created')
EOF

# Проверка статуса
echo ""
echo "📊 Status:"
docker-compose -f docker-compose.simple.yml ps

echo ""
echo "✅ Ready!"
echo "=========================="
echo "🌐 Web: http://$SERVER_IP:8090"
echo "🔌 API: http://$SERVER_IP:8001"
echo "⚙️  Admin: http://$SERVER_IP:8001/admin"
echo "👤 Login: admin / admin123"
echo ""
echo "📝 Logs: docker-compose -f docker-compose.simple.yml logs -f"