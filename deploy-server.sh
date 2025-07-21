#!/bin/bash

echo "=== PrintFarm Server Deployment Script ==="
echo "Time: $(date)"
echo ""

# Функция для проверки успешности команды
check_status() {
    if [ $? -eq 0 ]; then
        echo "✅ $1: Success"
    else
        echo "❌ $1: Failed"
        exit 1
    fi
}

echo "1. Pulling latest changes from GitHub..."
git pull
check_status "Git pull"

echo ""
echo "2. Copying environment file..."
if [ ! -f .env ]; then
    cp .env.server .env
    echo "✅ Created .env from .env.server"
else
    echo "⚠️  .env already exists, skipping copy"
fi

echo ""
echo "3. Stopping old containers..."
docker-compose -f docker-compose.prod.yml down 2>/dev/null || true
docker-compose -f docker-compose.server.yml down
check_status "Stop containers"

echo ""
echo "4. Building containers..."
docker-compose -f docker-compose.server.yml build
check_status "Build containers"

echo ""
echo "5. Starting containers..."
docker-compose -f docker-compose.server.yml up -d
check_status "Start containers"

echo ""
echo "6. Waiting for services to start (30 seconds)..."
sleep 30

echo ""
echo "7. Running migrations..."
docker-compose -f docker-compose.server.yml exec -T backend python manage.py migrate
check_status "Database migrations"

echo ""
echo "8. Collecting static files..."
docker-compose -f docker-compose.server.yml exec -T backend python manage.py collectstatic --noinput
check_status "Collect static"

echo ""
echo "9. Checking container status..."
docker-compose -f docker-compose.server.yml ps

echo ""
echo "10. Testing services..."
echo -n "Backend API: "
docker-compose -f docker-compose.server.yml exec -T backend python -c "import requests; print('✅ OK' if requests.get('http://localhost:8000/api/v1/products/stats/').status_code < 500 else '❌ Failed')" 2>/dev/null || echo "❌ Failed"

echo -n "Frontend: "
docker-compose -f docker-compose.server.yml exec -T frontend wget -q -O - http://localhost:3000 > /dev/null 2>&1 && echo "✅ OK" || echo "⚠️  Starting..."

echo ""
echo "11. Service URLs:"
echo "   - Main Interface: http://kemomail3.keenetic.pro:3000/"
echo "   - Django Admin: http://kemomail3.keenetic.pro:3000/django-admin/"
echo "   - API: http://kemomail3.keenetic.pro:3000/api/v1/"

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "If you see any errors, run: ./debug-server.sh"