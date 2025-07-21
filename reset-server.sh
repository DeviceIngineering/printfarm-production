#!/bin/bash

echo "=== PrintFarm Server Reset Script ==="
echo "⚠️  This will delete all data and rebuild everything!"
echo ""

read -p "Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "Cancelled."
    exit 1
fi

echo "1. Pulling latest changes..."
git pull

echo ""
echo "2. Stopping all containers..."
docker-compose -f docker-compose.server.yml down

echo ""
echo "3. Removing old volumes and data..."
docker volume rm printfarm_postgres_data printfarm_redis_data printfarm_static_volume printfarm_media_volume 2>/dev/null || true
docker system prune -f

echo ""
echo "4. Updating environment..."
cp .env.server .env

echo ""
echo "5. Building containers..."
docker-compose -f docker-compose.server.yml build

echo ""
echo "6. Starting services..."
docker-compose -f docker-compose.server.yml up -d

echo ""
echo "7. Waiting for database to initialize..."
sleep 15

echo ""
echo "8. Running migrations..."
docker-compose -f docker-compose.server.yml exec backend python manage.py migrate

echo ""
echo "9. Creating superuser..."
docker-compose -f docker-compose.server.yml exec backend python -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@printfarm.com', 'admin123')
    print('✅ Superuser created: admin/admin123')
else:
    print('ℹ️  Superuser already exists')
"

echo ""
echo "10. Collecting static files..."
docker-compose -f docker-compose.server.yml exec backend python manage.py collectstatic --noinput

echo ""
echo "11. Final status check..."
docker-compose -f docker-compose.server.yml ps

echo ""
echo "=== Reset Complete! ==="
echo ""
echo "🌐 URLs:"
echo "   - Main Interface: http://kemomail3.keenetic.pro:3000/"
echo "   - Django Admin: http://kemomail3.keenetic.pro:3000/django-admin/"
echo "   - API: http://kemomail3.keenetic.pro:3000/api/v1/"
echo ""
echo "👤 Admin credentials: admin / admin123"