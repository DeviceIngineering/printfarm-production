#!/bin/sh

# PrintFarm Production Django Entrypoint Script

set -e

echo "🚀 Starting PrintFarm Production Django..."

# Установка netcat если его нет
which nc > /dev/null || apt-get update && apt-get install -y netcat-openbsd

# Ждем доступности базы данных
echo "⏳ Waiting for PostgreSQL..."
while ! nc -z db 5432 2>/dev/null; do
  echo "   PostgreSQL is not ready yet... waiting..."
  sleep 2
done
echo "✅ PostgreSQL is ready!"

# Применяем миграции
echo "🗄️ Applying database migrations..."
python manage.py migrate --noinput

# Собираем статические файлы (теперь переменные окружения доступны)
echo "📦 Collecting static files..."
python manage.py collectstatic --noinput

# Создаем суперпользователя если его нет (опционально)
python manage.py shell << EOF || true
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    print("ℹ️ No superuser found. Please create one using 'docker-compose exec backend python manage.py createsuperuser'")
else:
    print("✅ Superuser exists")
EOF

echo "✅ Django is ready!"

# Выполняем переданную команду
exec "$@"