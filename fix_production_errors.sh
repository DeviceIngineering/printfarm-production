#!/bin/bash

# Скрипт для исправления internal errors на production сервере
# PrintFarm Production Fix Script v1.0

echo "🔧 PrintFarm Production Error Fix Script"
echo "========================================="

# Функция логирования
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Проверка что мы в правильной директории
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Ошибка: docker-compose.yml не найден"
    echo "Запустите скрипт из корневой директории проекта"
    exit 1
fi

log "🟡 Начинаем диагностику и исправление..."

# 1. Остановка всех контейнеров
log "1️⃣ Останавливаем все контейнеры..."
docker-compose down
sleep 5

# 2. Очистка старых контейнеров и volumes
log "2️⃣ Очищаем старые контейнеры..."
docker system prune -f
docker volume prune -f

# 3. Проверка и создание .env файла
log "3️⃣ Проверяем конфигурацию .env..."
if [ ! -f ".env" ]; then
    log "📝 Создаем .env файл..."
    cat > .env << 'EOF'
# Django Settings
SECRET_KEY=django-insecure-printfarm-production-key-2025
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,kemomail3.keenetic.pro,*

# Database Configuration
POSTGRES_DB=printfarm_db
POSTGRES_USER=printfarm_user
POSTGRES_PASSWORD=secure_password123!
DB_HOST=db
DB_PORT=5432

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# Celery Configuration
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# МойСклад API Configuration
MOYSKLAD_TOKEN=f9be4985f5e3488716c040ca52b8e04c7c0f9e0b
MOYSKLAD_DEFAULT_WAREHOUSE=241ed919-a631-11ee-0a80-07a9000bb947

# Simple Print API Configuration
SIMPLEPRINT_API_KEY=your-api-key
SIMPLEPRINT_COMPANY_ID=27286
SIMPLEPRINT_USER_ID=31471

# Django Settings Module
DJANGO_SETTINGS_MODULE=config.settings.production
EOF
    log "✅ .env файл создан"
else
    log "✅ .env файл уже существует"
fi

# 4. Создание директорий для логов и медиа
log "4️⃣ Создаем необходимые директории..."
mkdir -p backend/logs
mkdir -p backend/media/products
mkdir -p backend/static

# 5. Проверка docker-compose файла
log "5️⃣ Проверяем docker-compose конфигурацию..."
docker-compose config > /dev/null
if [ $? -eq 0 ]; then
    log "✅ docker-compose.yml корректен"
else
    log "❌ Ошибка в docker-compose.yml"
    exit 1
fi

# 6. Сборка и запуск контейнеров
log "6️⃣ Собираем и запускаем контейнеры..."
docker-compose up --build -d

# Ждем запуска сервисов
log "⏳ Ждем запуска сервисов..."
sleep 30

# 7. Проверка статуса контейнеров
log "7️⃣ Проверяем статус контейнеров..."
docker-compose ps

# 8. Проверка логов backend
log "8️⃣ Проверяем логи backend..."
echo "=== BACKEND LOGS ==="
docker-compose logs backend --tail=20

# 9. Проверка логов nginx
log "9️⃣ Проверяем логи nginx..."
echo "=== NGINX LOGS ==="
docker-compose logs nginx --tail=10

# 10. Применение миграций
log "🔟 Применяем миграции Django..."
docker-compose exec -T backend python manage.py migrate

# 11. Сбор статических файлов
log "1️⃣1️⃣ Собираем статические файлы..."
docker-compose exec -T backend python manage.py collectstatic --noinput

# 12. Проверка доступности API
log "1️⃣2️⃣ Проверяем доступность API..."
sleep 10

# Тест доступности через curl
if command -v curl &> /dev/null; then
    echo "Тестируем HTTP доступность..."
    curl -s -o /dev/null -w "%{http_code}" http://localhost/api/v1/ || echo "Не удалось подключиться"
    echo
fi

# 13. Финальная диагностика
log "1️⃣3️⃣ Финальная диагностика..."

echo
echo "🔍 ТЕКУЩИЙ СТАТУС СЕРВИСОВ:"
docker-compose ps

echo
echo "📊 ИСПОЛЬЗОВАНИЕ РЕСУРСОВ:"
docker stats --no-stream

echo
echo "🌐 ПРОВЕРЬТЕ ДОСТУПНОСТЬ:"
echo "- Frontend: http://localhost"
echo "- API: http://localhost/api/v1/"
echo "- Admin: http://localhost/admin/"

echo
echo "📋 ПОЛЕЗНЫЕ КОМАНДЫ:"
echo "- Просмотр логов: docker-compose logs [service]"
echo "- Перезапуск: docker-compose restart [service]"
echo "- Остановка: docker-compose down"
echo "- Django shell: docker-compose exec backend python manage.py shell"

echo
log "✅ Скрипт исправления завершен!"
echo "🎯 Если проблемы остались, проверьте логи: docker-compose logs backend"