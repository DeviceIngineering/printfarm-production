#!/bin/bash

echo "=== PrintFarm Local Development Setup ==="
echo ""

# Check if .env.local exists
if [ ! -f .env ]; then
    echo "1. Setting up environment..."
    cp .env.local .env
    echo "✅ Created .env from .env.local"
else
    echo "1. Environment file exists, checking settings..."
    if grep -q "development" .env; then
        echo "✅ Using development settings"
    else
        echo "⚠️  Updating to development settings..."
        cp .env.local .env
    fi
fi

echo ""
echo "2. Checking Docker containers..."

# Check if containers are running
if docker-compose ps | grep -q "Up"; then
    echo "📦 Some containers are running. Restarting..."
    docker-compose down
fi

echo ""
echo "3. Starting local development environment..."
docker-compose up -d db redis

echo ""
echo "4. Waiting for database to start..."
sleep 5

echo ""
echo "5. Running migrations..."
docker-compose run --rm backend python manage.py migrate

echo ""
echo "6. Starting all services..."
docker-compose up -d

echo ""
echo "7. Collecting static files..."
sleep 5
docker-compose exec backend python manage.py collectstatic --noinput

echo ""
echo "8. Checking status..."
docker-compose ps

echo ""
echo "=== Local Development Ready! ==="
echo ""
echo "🌐 URLs:"
echo "   - Main Interface: http://localhost:3000/"
echo "   - Django Admin: http://localhost:8000/admin/"
echo "   - API: http://localhost:8000/api/v1/"
echo ""
echo "📝 Note: Using SQLite database for local development"
echo "🔧 To view logs: docker-compose logs -f"