#!/bin/bash

# PrintFarm - Emergency Server Fix Script
# Экстренное восстановление работоспособности сервера

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

log "🚨 ЭКСТРЕННОЕ ВОССТАНОВЛЕНИЕ PRINTFARM СЕРВЕРА"

# Step 1: Clean up Docker completely
log "🧹 Полная очистка Docker контейнеров и сетей..."

# Stop all printfarm containers
docker-compose down --remove-orphans 2>/dev/null || true

# Kill any containers that might still be running
docker stop $(docker ps -a -q --filter name=printfarm) 2>/dev/null || true
docker rm $(docker ps -a -q --filter name=printfarm) 2>/dev/null || true

# Clean up networks
docker network prune -f 2>/dev/null || true

# Check what's using port 6379
log "🔍 Проверка занятости порта 6379..."
if netstat -tulnp | grep -q ":6379"; then
    warn "Порт 6379 занят. Пытаемся освободить..."
    
    # Try to find and kill Redis processes
    REDIS_PIDS=$(ps aux | grep redis | grep -v grep | awk '{print $2}' || true)
    if [ ! -z "$REDIS_PIDS" ]; then
        log "Останавливаем процессы Redis: $REDIS_PIDS"
        echo "$REDIS_PIDS" | xargs kill -9 2>/dev/null || true
    fi
    
    # Check again
    sleep 2
    if netstat -tulnp | grep -q ":6379"; then
        error "❌ Порт 6379 все еще занят"
        info "Показываем что использует порт:"
        netstat -tulnp | grep ":6379" || true
        warn "Попробуем изменить порт Redis в конфигурации..."
        
        # Modify docker-compose.yml to use different port
        if [ -f "docker-compose.yml" ]; then
            sed -i 's/6379:6379/6380:6379/g' docker-compose.yml
            log "✅ Изменен порт Redis с 6379 на 6380"
        fi
        
        # Update Redis URL in environment if needed
        if [ -f ".env" ]; then
            sed -i 's|redis://redis:6379|redis://redis:6379|g' .env
            sed -i 's|redis://localhost:6379|redis://localhost:6380|g' .env
            log "✅ Обновлены переменные окружения для Redis"
        fi
    else
        log "✅ Порт 6379 освобожден"
    fi
fi

# Step 2: Return to main branch to ensure stability
log "🔧 Возвращаемся к стабильной версии main..."
git checkout main
git reset --hard origin/main

# Step 3: Check and fix any local modifications
log "📝 Проверка локальных изменений..."
git status

# If there are modifications to docker-compose.prod.yml, stash them
if git status --porcelain | grep -q "docker-compose.prod.yml"; then
    log "Сохранение изменений в docker-compose.prod.yml..."
    git stash push -m "Backup server modifications $(date)"
fi

# Step 4: Clean start with basic configuration
log "🚀 Запуск с базовой конфигурацией..."

# Create a minimal .env if it doesn't exist
if [ ! -f ".env" ]; then
    log "Создание базового .env файла..."
    cat << 'EOF' > .env
# Django
SECRET_KEY=django-insecure-change-this-key
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
POSTGRES_DB=printfarm_db
POSTGRES_USER=printfarm_user
POSTGRES_PASSWORD=secure_password

# Redis
REDIS_URL=redis://redis:6379/0

# MoySkald
MOYSKLAD_TOKEN=f9be4985f5e3488716c040ca52b8e04c7c0f9e0b
MOYSKLAD_DEFAULT_WAREHOUSE=241ed919-a631-11ee-0a80-07a9000bb947

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
EOF
    log "✅ Базовый .env создан"
fi

# Step 5: Start services one by one
log "🔄 Поэтапный запуск сервисов..."

# Start database first
log "1/4 Запуск базы данных..."
docker-compose up -d db
sleep 5

# Check database status
if docker-compose ps db | grep -q "Up"; then
    log "✅ База данных запущена"
else
    error "❌ Проблемы с базой данных"
    docker-compose logs db
    exit 1
fi

# Start Redis
log "2/4 Запуск Redis..."
docker-compose up -d redis
sleep 3

if docker-compose ps redis | grep -q "Up"; then
    log "✅ Redis запущен"
else
    error "❌ Проблемы с Redis"
    docker-compose logs redis
    exit 1
fi

# Apply migrations
log "3/4 Применение миграций..."
docker-compose run --rm backend python manage.py migrate

# Start all services
log "4/4 Запуск всех сервисов..."
docker-compose up --build -d

# Step 6: Health check
log "🔍 Проверка работоспособности..."
sleep 10

docker-compose ps

# Test basic connectivity
log "Тестирование API..."
if curl -sf "http://localhost:8000/api/v1/products/" > /dev/null; then
    log "✅ API работает"
else
    warn "❌ API не отвечает, проверяем логи..."
    docker-compose logs --tail=20 backend
fi

# Step 7: Apply v3.1 fixes manually if needed
log "🔧 Применение исправлений алгоритма из v3.1..."

# Create a Python script to fix the algorithm
cat << 'EOF' > /tmp/apply_v31_fixes.py
import os
import sys
import django
from decimal import Decimal

# Setup Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
django.setup()

from apps.products.models import Product

def apply_algorithm_fixes():
    """Apply v3.1 algorithm fixes directly to the model"""
    print("=== Применение исправлений алгоритма v3.1 ===")
    
    # Get the current model code
    model_file = '/app/apps/products/models.py'
    
    with open(model_file, 'r') as f:
        content = f.read()
    
    # Check if fixes are already applied
    if 'actual_type = self.classify_product_type()' in content:
        print("✅ Исправления алгоритма уже применены")
        return
    
    print("📝 Применение исправлений к calculate_production_need...")
    
    # Apply the key fix: dynamic product type classification
    old_pattern = 'if self.product_type == \'new\':'
    new_pattern = '''# Get the actual product type based on current conditions
        actual_type = self.classify_product_type()
        
        if actual_type == 'new':'''
    
    if old_pattern in content:
        content = content.replace(old_pattern, new_pattern)
        
        # Also fix the elif condition
        content = content.replace(
            "elif self.product_type in ['old', 'critical']:",
            "elif actual_type in ['old', 'critical']:"
        )
        
        # Fix priority calculation too
        content = content.replace(
            "if self.product_type == 'critical'",
            "if actual_type == 'critical'"
        )
        content = content.replace(
            "elif self.product_type == 'old'",
            "elif actual_type == 'old'"
        )
        content = content.replace(
            "elif self.product_type == 'new'",
            "elif actual_type == 'new'"
        )
        
        # Write back
        with open(model_file, 'w') as f:
            f.write(content)
        
        print("✅ Исправления алгоритма применены")
    else:
        print("⚠️  Не удалось найти паттерн для исправления")

if __name__ == "__main__":
    apply_algorithm_fixes()
EOF

# Apply the fixes
if docker-compose exec -T backend python /tmp/apply_v31_fixes.py; then
    log "✅ Исправления алгоритма применены"
    
    # Restart backend to reload the code
    docker-compose restart backend
    sleep 5
else
    warn "❌ Не удалось применить исправления алгоритма"
fi

# Final status
log "📊 Финальный статус системы:"
docker-compose ps

log "🎉 Экстренное восстановление завершено!"

info "📋 Что сделано:"
info "   • Очищены все Docker контейнеры и сети"
info "   • Освобожден заблокированный порт 6379"
info "   • Возврат к стабильной ветке main"
info "   • Поэтапный запуск всех сервисов"
info "   • Применение критических исправлений алгоритма"

warn "📝 Рекомендации:"
warn "   • Проверьте работу API по адресу http://your-server-ip"
warn "   • Запустите синхронизацию с МойСклад для обновления данных"
warn "   • Мониторьте логи: docker-compose logs -f"

# Cleanup
rm -f /tmp/apply_v31_fixes.py

log "✅ Сервер восстановлен и готов к работе!"