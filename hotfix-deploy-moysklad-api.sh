#!/bin/bash

# PrintFarm v3.3.4 - MoySklad API Hotfix Deployment
# Fixes production issues with warehouses/product groups not loading

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Server configuration
SERVER_HOST="kemomail3.keenetic.pro"
SERVER_USER="printfarm"
SERVER_PORT="2131"
SERVER_IP="192.168.1.98"
COMPOSE_FILE="docker-compose.server.prod.yml"
BRANCH="hotfix/production-moysklad-api-fix"

log() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

show_fixes() {
    cat << 'FIXES_EOF'

🔧 MoySklad API Hotfix v3.3.4 - Исправления:

✅ Исправлен поврежденный .env.prod файл (удален "EOF < /dev/null")
✅ Улучшена обработка ошибок API в frontend (client.ts)
✅ Добавлено автоматическое определение API URL для production
✅ Расширена диагностика синхронизации (sync.ts)
✅ Улучшена обработка ошибок настроек (settings.ts) 
✅ Обновлены CORS настройки для production доступа
✅ Добавлено подробное логирование для отладки

Проблемы которые исправляет этот hotfix:
- 🏭 Пустой список складов в модальном окне синхронизации
- 📂 Отсутствующие группы товаров  
- ⚙️ Ошибки API в разделе настроек
- 🌐 CORS и network connectivity проблемы
- 🔐 Проблемы с авторизацией в production

FIXES_EOF
}

test_local_apis() {
    log "Тестирование локальных API endpoints..."
    
    # Test if backend is running
    if ! curl -s http://localhost:8000/api/v1/settings/system-info/ > /dev/null 2>&1; then
        warning "Backend не запущен локально. Запускаем..."
        cd backend
        python3 manage.py runserver &
        BACKEND_PID=$!
        sleep 5
        cd ..
    fi
    
    # Test critical endpoints
    log "Проверяем критические endpoints..."
    
    if curl -s http://localhost:8000/api/v1/sync/warehouses/ | grep -q '\[\]'; then
        warning "Warehouses API возвращает пустой массив"
    else
        success "Warehouses API работает"
    fi
    
    if curl -s http://localhost:8000/api/v1/sync/product-groups/ | grep -q '\[\]'; then
        warning "Product groups API возвращает пустой массив"  
    else
        success "Product groups API работает"
    fi
    
    if curl -s http://localhost:8000/api/v1/settings/system-info/ | grep -q 'v3.3.4'; then
        success "Settings API работает (v3.3.4)"
    else
        warning "Settings API может работать некорректно"
    fi
}

deploy_to_server() {
    log "Подготовка к развертыванию на сервер..."
    
    # Commit current changes
    if ! git diff --quiet || ! git diff --staged --quiet; then
        log "Сохраняем изменения в git..."
        git add .
        git commit -m "🔥 Hotfix: Fix MoySklad API production issues

- Fix corrupted .env.prod file (EOF < /dev/null)
- Enhance API error handling with detailed logging
- Add production API URL auto-detection
- Improve sync modal diagnostics
- Update CORS settings for production access
- Add comprehensive error fallbacks

Fixes:
- Empty warehouses list in sync modal
- Missing product groups
- Settings tab API errors  
- CORS and connectivity issues"
    fi
    
    # Push to GitHub
    log "Загружаем hotfix на GitHub..."
    git push origin $BRANCH
    
    # Create deployment script for server
    cat > hotfix-server-deploy.sh << 'DEPLOY_EOF'
#!/bin/bash

# MoySklad API Hotfix - Server Deployment

set -e

BRANCH="hotfix/production-moysklad-api-fix"
COMPOSE_FILE="docker-compose.server.prod.yml"

echo "🔥 MoySklad API Hotfix Deployment"
echo "=================================="

# Go to project directory
cd /opt/printfarm-production

# Backup current state
echo "📦 Creating backup..."
cp .env.prod .env.prod.backup.$(date +%Y%m%d_%H%M%S)

# Pull hotfix changes
echo "📥 Pulling hotfix from GitHub..."
git fetch origin
git checkout $BRANCH
git pull origin $BRANCH

# Stop containers
echo "🛑 Stopping containers..."
docker-compose -f $COMPOSE_FILE down

# Rebuild with new fixes
echo "🔨 Rebuilding with hotfix..."
docker-compose -f $COMPOSE_FILE build --no-cache

# Start containers
echo "🚀 Starting fixed containers..."  
docker-compose -f $COMPOSE_FILE up -d

# Wait for startup
echo "⏳ Waiting for services to start..."
sleep 30

# Test critical endpoints
echo "🧪 Testing fixed APIs..."

echo "Testing system info:"
curl -s http://localhost:8001/api/v1/settings/system-info/ || echo "API not ready yet"

echo -e "\nTesting warehouses:"
WAREHOUSES_COUNT=$(curl -s http://localhost:8001/api/v1/sync/warehouses/ | grep -c '"id"' || echo 0)
echo "Found $WAREHOUSES_COUNT warehouses"

echo -e "\nTesting product groups:"
GROUPS_COUNT=$(curl -s http://localhost:8001/api/v1/sync/product-groups/ | grep -c '"id"' || echo 0)  
echo "Found $GROUPS_COUNT product groups"

# Show container status
echo -e "\n📊 Container status:"
docker-compose -f $COMPOSE_FILE ps

# Show recent logs
echo -e "\n📝 Recent logs (last 20 lines):"
docker-compose -f $COMPOSE_FILE logs --tail=20 backend

echo -e "\n✅ Hotfix deployment completed!"
echo -e "\n🌐 Access URLs:"
echo "   Main App: http://192.168.1.98:8080"
echo "   Backend API: http://192.168.1.98:8001/api/v1/"
echo "   Frontend: http://192.168.1.98:3001"

echo -e "\n🔍 To check if issues are fixed:"
echo "   1. Open http://192.168.1.98:8080"
echo "   2. Click sync button - should show warehouses and groups"
echo "   3. Go to Settings tab - should not show API error"
echo "   4. Check browser console for detailed error logs"

DEPLOY_EOF

    chmod +x hotfix-server-deploy.sh
    
    # Upload deployment script
    log "Загружаем скрипт развертывания на сервер..."
    scp -P $SERVER_PORT hotfix-server-deploy.sh $SERVER_USER@$SERVER_HOST:/opt/printfarm-production/
    
    success "Hotfix готов к развертыванию на сервере"
}

show_deployment_commands() {
    cat << 'COMMANDS_EOF'

🚀 Команды для развертывания hotfix на сервере:

1. Подключитесь к серверу:
   ssh -p 2131 printfarm@kemomail3.keenetic.pro
   # Пароль: 1qaz2wsX

2. Перейдите в папку проекта:
   cd /opt/printfarm-production

3. Запустите развертывание hotfix:
   bash hotfix-server-deploy.sh

4. После успешного развертывания проверьте:
   - http://192.168.1.98:8080 - основное приложение
   - Кнопка синхронизации должна показать склады и группы товаров
   - Раздел "Настройки" не должен показывать ошибку API

5. Для отладки смотрите логи:
   docker-compose -f docker-compose.server.prod.yml logs backend
   
6. Для детальной диагностики откройте консоль браузера (F12)
   и посмотрите на подробные логи API запросов.

COMMANDS_EOF
}

main() {
    echo "🔥 PrintFarm MoySklad API Hotfix v3.3.4"
    echo "========================================"
    
    show_fixes
    
    echo -n "Продолжить с развертыванием hotfix? [y/N] "
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        log "Развертывание отменено"
        exit 0
    fi
    
    # Test local APIs first  
    test_local_apis
    
    # Deploy to server
    deploy_to_server
    
    # Show deployment commands
    show_deployment_commands
    
    success "🎉 MoySklad API Hotfix готов к развертыванию!"
    warning "Следуйте командам выше для применения исправлений на production сервере"
}

main "$@"