#!/bin/bash
# ============================================================
# PrintFarm v4.1.8 - Quick Remote Update Script
# ============================================================
# Быстрое обновление кода на удаленном сервере без полной пересборки
# ============================================================

set -e

# Конфигурация (должна совпадать с deploy-remote.sh)
REMOTE_HOST="kemomail3.keenetic.pro"
REMOTE_USER="printfarm"
REMOTE_PORT="2132"
PROJECT_NAME="printfarm-test"
REMOTE_DIR="/home/${REMOTE_USER}/${PROJECT_NAME}"

# Цвета
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

echo "============================================================"
echo "   PrintFarm v4.1.8 - Quick Remote Update"
echo "============================================================"
echo ""

log_info "Синхронизация изменений с $REMOTE_HOST..."

# Синхронизируем только измененные файлы
rsync -avz --delete \
    --exclude='.git' \
    --exclude='node_modules' \
    --exclude='__pycache__' \
    --exclude='.env' \
    --exclude='*.pyc' \
    --exclude='*.log' \
    --exclude='backend/media' \
    --exclude='backend/static' \
    --exclude='frontend/build' \
    --exclude='*.xlsx' \
    --exclude='*.tar.gz' \
    --exclude='logs/' \
    -e "ssh -p $REMOTE_PORT" \
    ./ $REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/

log_success "Файлы синхронизированы"

log_info "Перезапуск сервисов..."

# Быстрый перезапуск без пересборки образов
ssh -p $REMOTE_PORT $REMOTE_USER@$REMOTE_HOST "
    cd $REMOTE_DIR
    docker-compose -f docker-compose.remote.yml restart printfarm-remote-backend
    docker-compose -f docker-compose.remote.yml restart printfarm-remote-frontend
    docker-compose -f docker-compose.remote.yml restart printfarm-remote-celery
    docker-compose -f docker-compose.remote.yml restart printfarm-remote-nginx
"

log_success "Сервисы перезапущены"

log_info "Ожидание готовности сервисов..."
sleep 15

# Проверка health check
if ssh -p $REMOTE_PORT $REMOTE_USER@$REMOTE_HOST "curl -f http://localhost:18000/api/v1/health/" >/dev/null 2>&1; then
    log_success "✅ Backend доступен"
else
    echo "❌ Backend недоступен"
fi

if ssh -p $REMOTE_PORT $REMOTE_USER@$REMOTE_HOST "curl -f http://localhost:13000" >/dev/null 2>&1; then
    log_success "✅ Frontend доступен"
else
    echo "❌ Frontend недоступен"
fi

log_success "==================================================="
log_success "Быстрое обновление завершено!"
log_success "==================================================="
echo ""
echo "Проверьте работу: http://$REMOTE_HOST:13000"
echo ""