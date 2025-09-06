#!/bin/bash
# ============================================================
# PrintFarm v4.1.8 - Test Environment Deployment Script
# ============================================================
# Автоматическое развертывание в тестовой среде
# Использует нестандартные порты для избежания конфликтов
# ============================================================

set -e  # Остановка при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для вывода сообщений
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверка наличия необходимых инструментов
check_requirements() {
    log_info "Проверка требований..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker не установлен!"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose не установлен!"
        exit 1
    fi
    
    if ! command -v git &> /dev/null; then
        log_error "Git не установлен!"
        exit 1
    fi
    
    log_success "Все требования выполнены"
}

# Загрузка переменных окружения
load_env() {
    log_info "Загрузка переменных окружения..."
    
    if [ -f .env.test ]; then
        export $(cat .env.test | grep -v '^#' | xargs)
        log_success "Переменные окружения загружены из .env.test"
    else
        log_warning ".env.test не найден, используются значения по умолчанию"
    fi
}

# Проверка портов
check_ports() {
    log_info "Проверка доступности портов..."
    
    PORTS=(15432 16379 18000 13000 18080)
    PORT_NAMES=("PostgreSQL" "Redis" "Backend" "Frontend" "Nginx")
    
    for i in "${!PORTS[@]}"; do
        PORT=${PORTS[$i]}
        NAME=${PORT_NAMES[$i]}
        
        if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
            log_error "Порт $PORT ($NAME) уже занят!"
            log_info "Остановите процесс, использующий порт $PORT, или измените порт в конфигурации"
            exit 1
        fi
    done
    
    log_success "Все порты свободны"
}

# Создание необходимых директорий
create_directories() {
    log_info "Создание директорий..."
    
    mkdir -p logs/nginx
    mkdir -p backend/static
    mkdir -p backend/media
    
    log_success "Директории созданы"
}

# Остановка существующих контейнеров
stop_existing() {
    log_info "Остановка существующих контейнеров..."
    
    docker-compose -f docker-compose.test.yml down --volumes --remove-orphans 2>/dev/null || true
    
    # Удаление старых контейнеров с префиксом printfarm_test
    docker ps -a --format '{{.Names}}' | grep '^printfarm_test' | xargs -r docker rm -f 2>/dev/null || true
    
    log_success "Существующие контейнеры остановлены"
}

# Сборка образов
build_images() {
    log_info "Сборка Docker образов..."
    
    docker-compose -f docker-compose.test.yml build --no-cache
    
    log_success "Docker образы собраны"
}

# Запуск контейнеров
start_containers() {
    log_info "Запуск контейнеров..."
    
    docker-compose -f docker-compose.test.yml up -d
    
    log_success "Контейнеры запущены"
}

# Ожидание готовности сервисов
wait_for_services() {
    log_info "Ожидание готовности сервисов..."
    
    # Ожидание PostgreSQL
    log_info "Ожидание PostgreSQL..."
    for i in {1..30}; do
        if docker-compose -f docker-compose.test.yml exec -T printfarm-test-db pg_isready -U printfarm >/dev/null 2>&1; then
            log_success "PostgreSQL готов"
            break
        fi
        sleep 2
    done
    
    # Ожидание Redis
    log_info "Ожидание Redis..."
    for i in {1..30}; do
        if docker-compose -f docker-compose.test.yml exec -T printfarm-test-redis redis-cli ping >/dev/null 2>&1; then
            log_success "Redis готов"
            break
        fi
        sleep 2
    done
    
    # Ожидание Backend
    log_info "Ожидание Backend..."
    for i in {1..60}; do
        if curl -f http://localhost:18000/api/health/ >/dev/null 2>&1; then
            log_success "Backend готов"
            break
        fi
        sleep 2
    done
    
    # Ожидание Frontend
    log_info "Ожидание Frontend..."
    for i in {1..60}; do
        if curl -f http://localhost:13000 >/dev/null 2>&1; then
            log_success "Frontend готов"
            break
        fi
        sleep 2
    done
}

# Инициализация базы данных
init_database() {
    log_info "Инициализация базы данных..."
    
    # Создание суперпользователя
    docker-compose -f docker-compose.test.yml exec -T printfarm-test-backend python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@printfarm.test', 'admin123')
    print('Superuser created')
else:
    print('Superuser already exists')
" || log_warning "Не удалось создать суперпользователя"
    
    log_success "База данных инициализирована"
}

# Проверка состояния
check_status() {
    log_info "Проверка состояния контейнеров..."
    
    docker-compose -f docker-compose.test.yml ps
    
    log_info ""
    log_success "==================================================="
    log_success "PrintFarm v4.1.8 успешно развернут!"
    log_success "==================================================="
    log_info ""
    log_info "Доступ к сервисам:"
    log_info "  - Frontend:    http://localhost:13000"
    log_info "  - Backend API: http://localhost:18000/api/v1/"
    log_info "  - Admin Panel: http://localhost:18000/admin/"
    log_info "  - Nginx Proxy: http://localhost:18080"
    log_info ""
    log_info "База данных:"
    log_info "  - PostgreSQL:  localhost:15432"
    log_info "  - Redis:       localhost:16379"
    log_info ""
    log_info "Учетные данные администратора:"
    log_info "  - Username: admin"
    log_info "  - Password: admin123"
    log_info ""
    log_info "Команды управления:"
    log_info "  - Остановка:   docker-compose -f docker-compose.test.yml down"
    log_info "  - Логи:        docker-compose -f docker-compose.test.yml logs -f [service]"
    log_info "  - Перезапуск:  docker-compose -f docker-compose.test.yml restart"
    log_info ""
}

# Главная функция
main() {
    echo ""
    echo "============================================================"
    echo "   PrintFarm v4.1.8 - Test Environment Deployment"
    echo "============================================================"
    echo ""
    
    check_requirements
    load_env
    check_ports
    create_directories
    stop_existing
    build_images
    start_containers
    wait_for_services
    init_database
    check_status
}

# Обработка аргументов командной строки
case "${1:-}" in
    --help|-h)
        echo "Использование: $0 [ОПЦИЯ]"
        echo ""
        echo "Опции:"
        echo "  --help, -h      Показать эту справку"
        echo "  --stop          Остановить все контейнеры"
        echo "  --restart       Перезапустить все контейнеры"
        echo "  --logs          Показать логи всех контейнеров"
        echo "  --status        Показать статус контейнеров"
        echo "  --clean         Полная очистка (контейнеры, volumes, images)"
        echo ""
        ;;
    --stop)
        log_info "Остановка контейнеров..."
        docker-compose -f docker-compose.test.yml down
        log_success "Контейнеры остановлены"
        ;;
    --restart)
        log_info "Перезапуск контейнеров..."
        docker-compose -f docker-compose.test.yml restart
        log_success "Контейнеры перезапущены"
        ;;
    --logs)
        docker-compose -f docker-compose.test.yml logs -f
        ;;
    --status)
        docker-compose -f docker-compose.test.yml ps
        ;;
    --clean)
        log_warning "Полная очистка окружения..."
        docker-compose -f docker-compose.test.yml down --volumes --rmi all
        log_success "Очистка завершена"
        ;;
    *)
        main
        ;;
esac