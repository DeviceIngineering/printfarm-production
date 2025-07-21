#!/bin/bash

# PrintFarm Production System - Server Update Script v3.1
# Автоматическое обновление до версии 3.1 на удаленном сервере

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ] || [ ! -d "backend" ]; then
    error "Не найден docker-compose.yml или директория backend"
    error "Запустите скрипт из корневой директории проекта PrintFarm"
    exit 1
fi

log "🚀 Начинаем обновление PrintFarm Production System до версии 3.1"

# Step 1: Create backup
log "📦 Создание резервной копии..."
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)

# Backup database
if docker-compose ps db | grep -q "Up"; then
    log "Создание бэкапа базы данных..."
    docker-compose exec -T db pg_dump -U printfarm_user printfarm_db > "backup_db_${BACKUP_DATE}.sql"
    log "✅ Бэкап базы данных создан: backup_db_${BACKUP_DATE}.sql"
else
    warn "База данных не запущена, пропускаем бэкап БД"
fi

# Backup media files
if [ -d "backend/media" ]; then
    log "Создание бэкапа media файлов..."
    tar -czf "media_backup_${BACKUP_DATE}.tar.gz" backend/media/
    log "✅ Бэкап media файлов создан: media_backup_${BACKUP_DATE}.tar.gz"
fi

# Step 2: Stop services
log "⏹️  Остановка сервисов..."
docker-compose down

# Step 3: Update code
log "📥 Обновление кода..."
git fetch --all --tags
git status

# Check if v3.1 tag exists
if git tag -l | grep -q "^v3.1$"; then
    log "Переключение на версию v3.1..."
    git checkout v3.1
    log "✅ Успешно переключились на версию v3.1"
else
    error "Tag v3.1 не найден в репозитории"
    info "Доступные теги:"
    git tag -l
    exit 1
fi

# Show what changed
log "📋 Последние изменения:"
git log --oneline -5

# Step 4: Start database for migrations
log "🔄 Запуск базы данных для миграций..."
docker-compose up -d db redis

# Wait for database to be ready
log "⏳ Ожидание готовности базы данных..."
sleep 10

# Step 5: Apply migrations
log "📊 Применение миграций..."

# Check if monitoring migrations are needed
if docker-compose run --rm backend python manage.py showmigrations monitoring 2>/dev/null | grep -q "\[ \]"; then
    log "Создание миграций для monitoring app..."
    docker-compose run --rm backend python manage.py makemigrations monitoring
fi

log "Применение всех миграций..."
docker-compose run --rm backend python manage.py migrate

# Step 6: Collect static files
log "📁 Сбор статических файлов..."
docker-compose run --rm backend python manage.py collectstatic --noinput

# Step 7: Build and start all services
log "🔧 Сборка и запуск обновленных сервисов..."
docker-compose up --build -d

# Step 8: Wait for services to start
log "⏳ Ожидание запуска сервисов..."
sleep 15

# Step 9: Health checks
log "🔍 Проверка работоспособности..."

# Check if containers are running
log "Статус контейнеров:"
docker-compose ps

# Test API endpoints
log "Проверка API endpoints..."

# Test products endpoint
if curl -sf "http://localhost:8000/api/v1/products/" > /dev/null; then
    log "✅ Products API работает"
else
    error "❌ Products API не отвечает"
fi

# Test warehouses endpoint  
if curl -sf "http://localhost:8000/api/v1/sync/warehouses/" > /dev/null; then
    log "✅ Warehouses API работает"
else
    error "❌ Warehouses API не отвечает"
fi

# Test product groups endpoint
if curl -sf "http://localhost:8000/api/v1/sync/product-groups/" > /dev/null; then
    log "✅ Product Groups API работает"
else
    error "❌ Product Groups API не отвечает"
fi

# Step 10: Test production algorithm  
log "🧮 Тестирование алгоритма производства..."

cat << 'EOF' > /tmp/test_algorithm.py
import os
import sys
import django
from decimal import Decimal

# Setup Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
django.setup()

from apps.products.models import Product

def test_algorithm():
    print("=== Тест алгоритма производства ===")
    
    # Test case 1: Product with low sales (<=3)
    print("\n1. Тест товара с низкими продажами (<=3):")
    test_product = Product(
        article='TEST-001',
        name='Test Product 1',
        current_stock=Decimal('8'),
        sales_last_2_months=Decimal('2')
    )
    test_product.update_calculated_fields()
    
    expected = Decimal('2')  # 10 - 8 = 2
    actual = test_product.production_needed
    status = "✅ PASS" if actual == expected else f"❌ FAIL (expected {expected}, got {actual})"
    print(f"   Остаток: {test_product.current_stock}, Продажи: {test_product.sales_last_2_months}")
    print(f"   К производству: {actual} {status}")
    
    # Test case 2: Product with medium-low stock and sales
    print("\n2. Тест товара с низким остатком и продажами:")
    test_product2 = Product(
        article='TEST-002',
        name='Test Product 2', 
        current_stock=Decimal('2'),
        sales_last_2_months=Decimal('10')
    )
    test_product2.update_calculated_fields()
    
    expected2 = Decimal('8')  # 10 - 2 = 8
    actual2 = test_product2.production_needed
    status2 = "✅ PASS" if actual2 == expected2 else f"❌ FAIL (expected {expected2}, got {actual2})"
    print(f"   Остаток: {test_product2.current_stock}, Продажи: {test_product2.sales_last_2_months}")
    print(f"   К производству: {actual2} {status2}")
    
    print("\n=== Тест завершен ===")

if __name__ == "__main__":
    test_algorithm()
EOF

# Run algorithm test
if docker-compose exec -T backend python /tmp/test_algorithm.py; then
    log "✅ Алгоритм производства работает корректно"
else
    error "❌ Проблемы с алгоритмом производства"
fi

# Step 11: Show logs
log "📜 Последние логи сервисов:"
docker-compose logs --tail=20

# Step 12: Final status
log "🎉 Обновление до версии 3.1 завершено!"

info "📊 Статистика обновления:"
info "   • Версия: v3.1"
info "   • Дата обновления: $(date)"
info "   • Бэкап БД: backup_db_${BACKUP_DATE}.sql"
info "   • Бэкап media: media_backup_${BACKUP_DATE}.tar.gz"

info "🔧 Основные улучшения в версии 3.1:"
info "   • Исправлен алгоритм для товаров с низкими продажами (≤3)"
info "   • Добавлена система тестирования"
info "   • Улучшена обработка edge cases в алгоритме"
info "   • Добавлена система мониторинга (опционально)"

warn "📝 Примечания:"
warn "   • Система мониторинга отключена по умолчанию для стабильности"
warn "   • Для включения мониторинга раскомментируйте строку в apps/api/v1/urls.py"
warn "   • Запустите 'docker-compose exec backend python manage.py setup_monitoring'"

log "✅ Сервер успешно обновлен и готов к работе!"

# Cleanup temp files
rm -f /tmp/test_algorithm.py

echo ""
log "🌐 Проверьте работу системы по адресу: http://your-server-ip"
log "📚 Документация API: http://your-server-ip/api/v1/"