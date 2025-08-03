#!/bin/bash

# Простой скрипт развертывания PrintFarm на удаленном сервере
# Использование: ./deploy_simple.sh

SERVER="printfarm@szboxz66"
PROJECT_DIR="/home/printfarm/printfarm-production"

echo "🚀 Развертывание PrintFarm на удаленном сервере..."

# Проверка доступности сервера
echo "📡 Проверка подключения к серверу..."
if ! ssh -o ConnectTimeout=10 -o BatchMode=yes $SERVER exit 2>/dev/null; then
    echo "❌ Не удается подключиться к серверу $SERVER"
    echo "Проверьте SSH ключи и доступность сервера"
    exit 1
fi

echo "✅ Подключение к серверу успешно"

# Выполнение развертывания на сервере
ssh $SERVER bash << 'EOF'
    set -e  # Остановить при ошибке
    
    echo "📁 Переход в директорию проекта..."
    cd ~/printfarm-production || { echo "❌ Директория проекта не найдена"; exit 1; }
    
    echo "🔄 Обновление кода из Git..."
    git pull origin main
    
    echo "🛑 Остановка старых контейнеров..."
    docker-compose down
    
    echo "🔧 Создание .env файла (если не существует)..."
    if [ ! -f ".env" ]; then
        cat > .env << 'ENVEOF'
# Django Settings
SECRET_KEY=django-insecure-printfarm-production-key-2025
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,szboxz66,*

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
ENVEOF
        echo "✅ .env файл создан"
    fi
    
    echo "🐳 Сборка и запуск контейнеров..."
    docker-compose up -d --build
    
    echo "⏳ Ожидание запуска сервисов..."
    sleep 45
    
    echo "🗃️ Применение миграций базы данных..."
    docker-compose exec -T backend python manage.py migrate
    
    echo "📦 Сбор статических файлов..."
    docker-compose exec -T backend python manage.py collectstatic --noinput
    
    echo "🔍 Проверка статуса сервисов..."
    docker-compose ps
    
    echo
    echo "✅ Развертывание завершено успешно!"
    echo "🌐 Проверьте доступность:"
    echo "   - Frontend: http://szboxz66"
    echo "   - API: http://szboxz66/api/v1/"
    echo "   - Admin: http://szboxz66/admin/"
EOF

if [ $? -eq 0 ]; then
    echo
    echo "🎉 Развертывание успешно завершено!"
    echo "📊 Для мониторинга используйте:"
    echo "   ssh $SERVER 'cd ~/printfarm-production && docker-compose logs -f'"
else
    echo
    echo "❌ Ошибка при развертывании"
    echo "🔍 Для диагностики подключитесь к серверу:"
    echo "   ssh $SERVER"
    echo "   cd ~/printfarm-production"
    echo "   ./quick_diagnosis.sh"
fi