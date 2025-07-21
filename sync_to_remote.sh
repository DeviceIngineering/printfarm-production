#!/bin/bash

echo "🚀 PrintFarm v3.2 - Синхронизация с удаленным сервером"
echo "================================================"

# Настройки удаленного сервера
REMOTE_HOST="your-server.com"
REMOTE_USER="root"
REMOTE_PATH="/opt/printfarm"
LOCAL_PATH="."

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функция для логирования
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверка подключения к удаленному серверу
check_remote_connection() {
    log "Проверка подключения к удаленному серверу..."
    
    if ssh -o ConnectTimeout=10 ${REMOTE_USER}@${REMOTE_HOST} "echo 'Connection OK'"; then
        log "✅ Подключение к серверу успешно"
        return 0
    else
        error "❌ Не удается подключиться к серверу ${REMOTE_HOST}"
        return 1
    fi
}

# Создание резервной копии на удаленном сервере
create_remote_backup() {
    log "Создание резервной копии на сервере..."
    
    ssh ${REMOTE_USER}@${REMOTE_HOST} "
        cd ${REMOTE_PATH}
        
        # Создаем каталог для бэкапов если не существует
        mkdir -p backups
        
        # Бэкап базы данных
        if [ -f db.sqlite3 ]; then
            cp db.sqlite3 backups/db_backup_\$(date +%Y%m%d_%H%M%S).sqlite3
            log '📦 База данных сохранена'
        fi
        
        # Бэкап медиа файлов
        if [ -d media ]; then
            tar -czf backups/media_backup_\$(date +%Y%m%d_%H%M%S).tar.gz media/
            log '🖼️  Медиа файлы сохранены'
        fi
        
        # Бэкап настроек
        if [ -f .env ]; then
            cp .env backups/env_backup_\$(date +%Y%m%d_%H%M%S).env
            log '⚙️  Настройки сохранены'
        fi
    "
    
    if [ $? -eq 0 ]; then
        log "✅ Резервная копия создана"
        return 0
    else
        error "❌ Ошибка создания резервной копии"
        return 1
    fi
}

# Остановка сервисов на удаленном сервере
stop_remote_services() {
    log "Остановка сервисов на удаленном сервере..."
    
    ssh ${REMOTE_USER}@${REMOTE_HOST} "
        cd ${REMOTE_PATH}
        
        # Остановка Docker контейнеров
        if [ -f docker-compose.yml ]; then
            docker-compose down
            log '🐳 Docker контейнеры остановлены'
        fi
        
        # Остановка systemd сервисов (если используются)
        systemctl stop printfarm-celery 2>/dev/null || true
        systemctl stop printfarm-django 2>/dev/null || true
        systemctl stop nginx 2>/dev/null || true
        
        log '🛑 Сервисы остановлены'
    "
}

# Синхронизация файлов
sync_files() {
    log "Синхронизация файлов с сервером..."
    
    # Исключения для rsync
    EXCLUDE_FILE=$(mktemp)
    cat > ${EXCLUDE_FILE} << EOF
.git/
__pycache__/
*.pyc
.env
node_modules/
.DS_Store
*.log
backups/
db.sqlite3
media/
frontend/build/
frontend/node_modules/
.pytest_cache/
coverage/
*.orig
*.swp
*.swo
EOF

    # Синхронизируем backend
    log "📁 Синхронизация backend..."
    rsync -avz --delete --exclude-from=${EXCLUDE_FILE} \
          backend/ ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/backend/
    
    # Синхронизируем frontend (только исходники)
    log "🎨 Синхронизация frontend..."
    rsync -avz --delete --exclude-from=${EXCLUDE_FILE} \
          frontend/src/ ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/frontend/src/
    rsync -av frontend/package*.json ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/frontend/
    rsync -av frontend/tsconfig.json ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/frontend/
    
    # Синхронизируем Docker файлы и скрипты
    log "🐳 Синхронизация Docker конфигурации..."
    rsync -av docker-compose*.yml ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/
    rsync -av *.sh ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/
    rsync -av README.md CLAUDE.md ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/
    
    # Синхронизируем HTML тестовые файлы
    rsync -av test_*.html ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/ 2>/dev/null || true
    
    rm ${EXCLUDE_FILE}
    
    if [ $? -eq 0 ]; then
        log "✅ Файлы синхронизированы"
        return 0
    else
        error "❌ Ошибка синхронизации файлов"
        return 1
    fi
}

# Обновление зависимостей и сборка на удаленном сервере
update_remote_dependencies() {
    log "Обновление зависимостей на сервере..."
    
    ssh ${REMOTE_USER}@${REMOTE_HOST} "
        cd ${REMOTE_PATH}
        
        # Обновление Python зависимостей
        log '🐍 Обновление Python пакетов...'
        if [ -f backend/requirements.txt ]; then
            docker-compose run --rm backend pip install -r requirements.txt
        fi
        
        # Обновление Node.js зависимостей
        log '📦 Обновление Node.js пакетов...'
        if [ -f frontend/package.json ]; then
            docker-compose run --rm frontend npm install
        fi
        
        # Сборка фронтенда
        log '🏗️  Сборка frontend...'
        docker-compose run --rm frontend npm run build
        
        log '✅ Зависимости обновлены'
    "
}

# Применение миграций базы данных
apply_migrations() {
    log "Применение миграций базы данных..."
    
    ssh ${REMOTE_USER}@${REMOTE_HOST} "
        cd ${REMOTE_PATH}
        
        # Создание новых миграций
        docker-compose run --rm backend python manage.py makemigrations
        
        # Применение миграций
        docker-compose run --rm backend python manage.py migrate
        
        # Инициализация настроек
        docker-compose run --rm backend python manage.py init_settings --warehouse-id='241ed919-a631-11ee-0a80-07a9000bb947'
        
        log '💾 Миграции применены'
    "
}

# Запуск сервисов
start_remote_services() {
    log "Запуск сервисов на удаленном сервере..."
    
    ssh ${REMOTE_USER}@${REMOTE_HOST} "
        cd ${REMOTE_PATH}
        
        # Запуск Docker контейнеров
        docker-compose up -d
        
        # Ожидание запуска сервисов
        sleep 10
        
        # Проверка статуса
        docker-compose ps
        
        log '🚀 Сервисы запущены'
    "
}

# Проверка работоспособности
health_check() {
    log "Проверка работоспособности системы..."
    
    ssh ${REMOTE_USER}@${REMOTE_HOST} "
        cd ${REMOTE_PATH}
        
        # Проверка API
        sleep 5
        response=\$(curl -s -w '%{http_code}' -o /dev/null http://localhost:8000/api/v1/products/)
        
        if [ \"\$response\" = '200' ]; then
            log '✅ API работает корректно'
        else
            warn '⚠️  API недоступен (HTTP \$response)'
        fi
        
        # Проверка настроек
        settings_response=\$(curl -s -w '%{http_code}' -o /dev/null http://localhost:8000/api/v1/settings/system-info/)
        
        if [ \"\$settings_response\" = '200' ]; then
            log '✅ Настройки API работают корректно'
        else
            warn '⚠️  Настройки API недоступны'
        fi
        
        log '🎉 Система готова к работе!'
    "
}

# Главная функция
main() {
    echo "Начинаем синхронизацию PrintFarm v3.2..."
    echo "Удаленный сервер: ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}"
    echo

    # Проверка подключения
    if ! check_remote_connection; then
        error "Прервано из-за ошибки подключения"
        exit 1
    fi

    # Создание бэкапа
    if ! create_remote_backup; then
        error "Прервано из-за ошибки создания бэкапа"
        exit 1
    fi

    # Остановка сервисов
    stop_remote_services

    # Синхронизация файлов
    if ! sync_files; then
        error "Прервано из-за ошибки синхронизации"
        exit 1
    fi

    # Обновление зависимостей
    update_remote_dependencies

    # Миграции
    apply_migrations

    # Запуск сервисов
    start_remote_services

    # Проверка
    health_check

    echo
    log "🎉 Синхронизация PrintFarm v3.2 завершена успешно!"
    log "📝 Доступные команды на сервере:"
    log "   - Просмотр логов: docker-compose logs -f"
    log "   - Статус: docker-compose ps"
    log "   - Перезапуск: docker-compose restart"
    log "   - Настройки: curl http://localhost:8000/api/v1/settings/summary/"
    echo
}

# Обработка параметров командной строки
case "${1:-}" in
    --help|-h)
        echo "PrintFarm v3.2 Sync Script"
        echo "Usage: $0 [options]"
        echo ""
        echo "Options:"
        echo "  --help, -h     Показать эту справку"
        echo "  --dry-run      Показать что будет сделано без выполнения"
        echo "  --backup-only  Только создать бэкап"
        echo ""
        echo "Environment variables:"
        echo "  REMOTE_HOST    Адрес удаленного сервера"
        echo "  REMOTE_USER    Пользователь на удаленном сервере"
        echo "  REMOTE_PATH    Путь к проекту на сервере"
        exit 0
        ;;
    --dry-run)
        warn "Режим DRY-RUN: показываем команды без выполнения"
        log "rsync команды, которые будут выполнены:"
        echo "backend/ -> ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/backend/"
        echo "frontend/src/ -> ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/frontend/src/"
        exit 0
        ;;
    --backup-only)
        log "Режим BACKUP-ONLY: создаем только резервную копию"
        check_remote_connection && create_remote_backup
        exit $?
        ;;
    *)
        main
        ;;
esac