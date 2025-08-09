#!/bin/bash

# Полный диагностический скрипт для PrintFarm Production System
# Автоматически проверяет все компоненты системы и предлагает исправления

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Переменные
APP_DIR="/opt/printfarm"
LOG_FILE="/tmp/printfarm_diagnosis.log"
ISSUES_FOUND=0
FIX_APPLIED=0

# Функции вывода
print_header() {
    echo -e "\n${CYAN}${BOLD}=========================================="
    echo -e "$1"
    echo -e "==========================================${NC}\n"
}

print_section() {
    echo -e "\n${BLUE}${BOLD}>>> $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((ISSUES_FOUND++))
}

print_error() {
    echo -e "${RED}✗${NC} $1"
    ((ISSUES_FOUND++))
}

print_info() {
    echo -e "${CYAN}ℹ${NC} $1"
}

print_fix() {
    echo -e "${GREEN}🔧${NC} Исправление: $1"
    ((FIX_APPLIED++))
}

# Функция для выполнения команд с логированием
run_command() {
    local cmd="$1"
    local description="$2"
    
    echo "=== $description ===" >> "$LOG_FILE"
    echo "Command: $cmd" >> "$LOG_FILE"
    echo "Time: $(date)" >> "$LOG_FILE"
    
    if eval "$cmd" >> "$LOG_FILE" 2>&1; then
        print_success "$description"
        return 0
    else
        print_error "$description - Failed"
        echo "Error: Command failed" >> "$LOG_FILE"
        return 1
    fi
}

# Проверка прав запуска
check_permissions() {
    print_section "Проверка прав доступа"
    
    # Проверка пользователя
    if [ "$USER" != "root" ] && [ "$USER" != "printfarm" ]; then
        print_warning "Скрипт запущен от пользователя $USER. Рекомендуется root или printfarm"
        print_info "Запустите: sudo ./scripts/diagnose.sh или sudo su - printfarm"
    else
        print_success "Пользователь: $USER"
    fi
    
    # Проверка директории
    if [ ! -d "$APP_DIR" ]; then
        print_error "Директория $APP_DIR не существует"
        return 1
    else
        print_success "Директория приложения найдена"
    fi
    
    # Проверка прав на директорию
    if [ ! -w "$APP_DIR" ]; then
        print_warning "Нет прав записи в $APP_DIR"
        if [ "$USER" = "root" ]; then
            print_fix "Исправляем права доступа..."
            chown -R printfarm:printfarm "$APP_DIR"
            chmod -R 755 "$APP_DIR"
        fi
    else
        print_success "Права доступа корректны"
    fi
}

# Проверка системы
check_system() {
    print_section "Проверка системы"
    
    # Проверка Docker
    if command -v docker &> /dev/null; then
        print_success "Docker установлен: $(docker --version | cut -d' ' -f3)"
        
        # Проверка службы Docker
        if systemctl is-active --quiet docker; then
            print_success "Docker сервис активен"
        else
            print_error "Docker сервис не активен"
            if [ "$USER" = "root" ]; then
                print_fix "Запускаем Docker сервис..."
                systemctl start docker
                systemctl enable docker
            fi
        fi
    else
        print_error "Docker не установлен"
        return 1
    fi
    
    # Проверка Docker Compose
    if command -v docker-compose &> /dev/null; then
        print_success "Docker Compose установлен: $(docker-compose --version | cut -d' ' -f4)"
    else
        print_error "Docker Compose не установлен"
        return 1
    fi
    
    # Проверка портов
    print_info "Проверка используемых портов:"
    for port in 80 443 5432 6379 8000 8080 9000 9001; do
        if netstat -tln 2>/dev/null | grep -q ":$port "; then
            local process=$(netstat -tlnp 2>/dev/null | grep ":$port " | awk '{print $7}' | head -1)
            print_info "Порт $port: используется ($process)"
        else
            print_info "Порт $port: свободен"
        fi
    done
    
    # Проверка ресурсов
    local mem_total=$(free -h | awk '/^Mem:/{print $2}')
    local mem_free=$(free -h | awk '/^Mem:/{print $7}')
    local disk_free=$(df -h "$APP_DIR" | awk 'NR==2{print $4}')
    
    print_info "Память: $mem_free доступно из $mem_total"
    print_info "Диск: $disk_free свободно в $APP_DIR"
}

# Проверка кода и конфигурации
check_code() {
    print_section "Проверка кода и конфигурации"
    
    cd "$APP_DIR"
    
    # Проверка Git репозитория
    if [ -d ".git" ]; then
        print_success "Git репозиторий найден"
        
        local branch=$(git branch --show-current 2>/dev/null || echo "unknown")
        local commit=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
        print_info "Ветка: $branch, коммит: $commit"
        
        # Проверка на обновления
        if run_command "git fetch origin" "Проверка обновлений из GitHub"; then
            local behind=$(git rev-list --count HEAD..origin/test_v1 2>/dev/null || echo "0")
            if [ "$behind" -gt 0 ]; then
                print_warning "Код отстает на $behind коммитов"
                if [ "$USER" = "root" ] || [ "$USER" = "printfarm" ]; then
                    print_fix "Обновляем код..."
                    if [ "$USER" = "root" ]; then
                        sudo -u printfarm git reset --hard origin/test_v1
                    else
                        git reset --hard origin/test_v1
                    fi
                fi
            else
                print_success "Код актуален"
            fi
        fi
    else
        print_error "Git репозиторий не найден"
    fi
    
    # Проверка конфигурационных файлов
    for file in docker-compose.prod.yml .env.prod; do
        if [ -f "$file" ]; then
            print_success "Файл $file найден"
        else
            print_error "Файл $file не найден"
            if [ "$file" = ".env.prod" ] && [ -f ".env.prod.example" ]; then
                print_fix "Создаем $file из примера..."
                cp .env.prod.example .env.prod
                print_warning "Необходимо настроить переменные в .env.prod"
            fi
        fi
    done
    
    # Проверка .env.prod
    if [ -f ".env.prod" ]; then
        print_info "Проверка конфигурации .env.prod:"
        
        # Проверка критичных переменных
        local critical_vars=("SECRET_KEY" "POSTGRES_PASSWORD" "MOYSKLAD_TOKEN")
        for var in "${critical_vars[@]}"; do
            if grep -q "^${var}=" .env.prod && ! grep -q "^${var}=.*default" .env.prod; then
                print_success "$var настроен"
            else
                print_warning "$var не настроен или использует значение по умолчанию"
            fi
        done
        
        # Проверка ALLOWED_HOSTS
        local server_ip=$(hostname -I | awk '{print $1}')
        if grep -q "$server_ip" .env.prod; then
            print_success "IP сервера ($server_ip) добавлен в ALLOWED_HOSTS"
        else
            print_warning "IP сервера ($server_ip) не найден в ALLOWED_HOSTS"
            if [ "$USER" = "root" ] || [ "$USER" = "printfarm" ]; then
                print_fix "Добавляем IP сервера в ALLOWED_HOSTS..."
                sed -i "s/ALLOWED_HOSTS=.*/ALLOWED_HOSTS=localhost,127.0.0.1,$server_ip/" .env.prod
            fi
        fi
    fi
}

# Проверка Docker контейнеров
check_containers() {
    print_section "Проверка Docker контейнеров"
    
    cd "$APP_DIR"
    
    # Проверка docker-compose файла
    if run_command "docker-compose -f docker-compose.prod.yml config" "Проверка docker-compose конфигурации"; then
        print_success "Docker Compose конфигурация корректна"
    else
        print_error "Ошибка в docker-compose.prod.yml"
        return 1
    fi
    
    # Получение статуса контейнеров
    local container_status
    if [ "$USER" = "root" ]; then
        container_status=$(sudo -u printfarm docker-compose -f docker-compose.prod.yml ps 2>/dev/null || echo "")
    else
        container_status=$(docker-compose -f docker-compose.prod.yml ps 2>/dev/null || echo "")
    fi
    
    if [ -n "$container_status" ]; then
        print_info "Статус контейнеров:"
        echo "$container_status"
        
        # Проверка каждого сервиса
        local services=("db" "redis" "backend" "frontend" "nginx")
        for service in "${services[@]}"; do
            if echo "$container_status" | grep -q "$service.*Up"; then
                print_success "Сервис $service: работает"
            elif echo "$container_status" | grep -q "$service.*unhealthy"; then
                print_warning "Сервис $service: нездоров"
            else
                print_error "Сервис $service: не работает"
            fi
        done
    else
        print_warning "Контейнеры не запущены"
    fi
}

# Проверка сетевой доступности
check_connectivity() {
    print_section "Проверка сетевой доступности"
    
    local server_ip=$(hostname -I | awk '{print $1}')
    
    # Проверка локальных endpoint'ов
    local endpoints=(
        "http://localhost:8080/health:Nginx health"
        "http://localhost:8080:Frontend"
        "http://localhost:8000/health/:Backend health (internal)"
        "http://localhost:9001/health:Webhook health"
    )
    
    for endpoint in "${endpoints[@]}"; do
        local url=$(echo "$endpoint" | cut -d':' -f1)
        local name=$(echo "$endpoint" | cut -d':' -f2-)
        
        if curl -f -s --max-time 5 "$url" > /dev/null 2>&1; then
            print_success "$name: доступен"
        else
            print_warning "$name: недоступен ($url)"
        fi
    done
    
    # Проверка внешней доступности
    if [ -n "$server_ip" ]; then
        print_info "Внешний IP сервера: $server_ip"
        
        if curl -f -s --max-time 5 "http://$server_ip:8080/" > /dev/null 2>&1; then
            print_success "Веб-сайт доступен извне по http://$server_ip:8080/"
        else
            print_warning "Веб-сайт недоступен извне по порту 8080"
            print_info "Проверьте файрвол: sudo ufw status"
        fi
    fi
}

# Проверка журналов
check_logs() {
    print_section "Анализ журналов"
    
    cd "$APP_DIR"
    
    # Проверка журналов контейнеров
    local services=("backend" "frontend" "nginx" "db" "redis")
    for service in "${services[@]}"; do
        print_info "Последние ошибки в $service:"
        local logs
        if [ "$USER" = "root" ]; then
            logs=$(sudo -u printfarm docker-compose -f docker-compose.prod.yml logs --tail=10 "$service" 2>/dev/null | grep -i error || echo "Нет ошибок")
        else
            logs=$(docker-compose -f docker-compose.prod.yml logs --tail=10 "$service" 2>/dev/null | grep -i error || echo "Нет ошибок")
        fi
        echo "  $logs"
    done
    
    # Проверка системных журналов
    print_info "Системные ошибки Docker:"
    local docker_errors=$(journalctl -u docker --since "1 hour ago" --no-pager | grep -i error | tail -5 || echo "Нет ошибок")
    echo "  $docker_errors"
    
    # Проверка webhook службы
    if systemctl is-active --quiet printfarm-webhook.service; then
        print_success "Webhook служба активна"
        local webhook_errors=$(journalctl -u printfarm-webhook.service --since "1 hour ago" --no-pager | grep -i error | tail -3 || echo "Нет ошибок")
        print_info "Ошибки webhook: $webhook_errors"
    else
        print_warning "Webhook служба неактивна"
    fi
}

# Автоматическое исправление проблем
auto_fix() {
    print_section "Автоматическое исправление"
    
    if [ "$ISSUES_FOUND" -eq 0 ]; then
        print_success "Проблем не найдено!"
        return 0
    fi
    
    print_info "Найдено проблем: $ISSUES_FOUND"
    print_info "Применено исправлений: $FIX_APPLIED"
    
    if [ "$USER" != "root" ] && [ "$USER" != "printfarm" ]; then
        print_warning "Для автоматических исправлений требуются права root или printfarm"
        return 1
    fi
    
    cd "$APP_DIR"
    
    # Попытка перезапуска сервисов
    print_fix "Перезапуск сервисов..."
    
    # Создание директорий если нужно
    mkdir -p logs/{deploy,webhook} data/{postgres,redis,media,static} backups
    
    if [ "$USER" = "root" ]; then
        chown -R printfarm:printfarm logs data backups
        
        # Перезапуск от имени printfarm
        print_info "Перезапуск Docker контейнеров..."
        if sudo -u printfarm docker-compose -f docker-compose.prod.yml down 2>/dev/null; then
            sleep 5
            sudo -u printfarm docker-compose -f docker-compose.prod.yml up -d
            sleep 10
        fi
        
        # Перезапуск webhook службы
        if systemctl list-unit-files | grep -q printfarm-webhook.service; then
            systemctl restart printfarm-webhook.service
        fi
    else
        # Если запущено от printfarm
        docker-compose -f docker-compose.prod.yml down 2>/dev/null || true
        sleep 5
        docker-compose -f docker-compose.prod.yml up -d
        sleep 10
    fi
}

# Генерация отчета
generate_report() {
    print_section "Генерация отчета"
    
    local report_file="/tmp/printfarm_report_$(date +%Y%m%d_%H%M%S).txt"
    
    {
        echo "PrintFarm Production System - Диагностический отчет"
        echo "=================================================="
        echo "Дата: $(date)"
        echo "Сервер: $(hostname) ($(hostname -I | awk '{print $1}'))"
        echo "Пользователь: $USER"
        echo ""
        
        echo "Статус системы:"
        echo "- Найдено проблем: $ISSUES_FOUND"
        echo "- Применено исправлений: $FIX_APPLIED"
        echo ""
        
        echo "Docker контейнеры:"
        if [ "$USER" = "root" ]; then
            sudo -u printfarm docker-compose -f "$APP_DIR/docker-compose.prod.yml" ps 2>/dev/null || echo "Недоступно"
        else
            docker-compose -f "$APP_DIR/docker-compose.prod.yml" ps 2>/dev/null || echo "Недоступно"
        fi
        echo ""
        
        echo "Сетевая доступность:"
        curl -f -s --max-time 5 "http://localhost:8080/" > /dev/null && echo "- Frontend: ✓" || echo "- Frontend: ✗"
        curl -f -s --max-time 5 "http://localhost:8000/health/" > /dev/null && echo "- Backend: ✓" || echo "- Backend: ✗"
        curl -f -s --max-time 5 "http://localhost:9001/health" > /dev/null && echo "- Webhook: ✓" || echo "- Webhook: ✗"
        echo ""
        
        echo "Рекомендации:"
        if [ "$ISSUES_FOUND" -gt 0 ]; then
            echo "- Проверьте подробные логи: $LOG_FILE"
            echo "- Убедитесь, что настроен .env.prod файл"
            echo "- Проверьте GitHub Actions для автоматических обновлений"
        else
            echo "- Система работает корректно"
            echo "- Настройте мониторинг для отслеживания состояния"
        fi
        
    } > "$report_file"
    
    print_success "Отчет сохранен: $report_file"
    
    # Показать ключевые URL для пользователя
    local server_ip=$(hostname -I | awk '{print $1}')
    print_info "Ключевые ссылки:"
    echo "  🌐 Веб-сайт: http://$server_ip/"
    echo "  🔧 API: http://$server_ip/api/v1/"
    echo "  ⚡ Webhook: http://$server_ip:9000/health"
    echo "  📊 Отчет: $report_file"
    echo "  📋 Детальные логи: $LOG_FILE"
}

# Интерактивные команды
interactive_menu() {
    if [ "${1:-}" = "--auto" ]; then
        return  # Пропустить меню в автоматическом режиме
    fi
    
    print_section "Дополнительные действия"
    print_info "Выберите действие:"
    echo "  1) Полный перезапуск системы"
    echo "  2) Обновить код из GitHub"
    echo "  3) Просмотр логов в реальном времени"
    echo "  4) Проверить GitHub Actions"
    echo "  5) Настроить Telegram уведомления"
    echo "  0) Выход"
    
    read -p "Введите номер (0-5): " choice
    
    case $choice in
        1)
            print_info "Полный перезапуск системы..."
            cd "$APP_DIR"
            if [ "$USER" = "root" ]; then
                sudo -u printfarm docker-compose -f docker-compose.prod.yml down
                sudo -u printfarm docker system prune -f
                sleep 5
                sudo -u printfarm ./scripts/deploy.sh
                systemctl restart printfarm-webhook.service
            else
                docker-compose -f docker-compose.prod.yml down
                docker system prune -f
                sleep 5
                ./scripts/deploy.sh
            fi
            ;;
        2)
            print_info "Обновление кода..."
            cd "$APP_DIR"
            if [ "$USER" = "root" ]; then
                sudo -u printfarm git pull origin test_v1
                sudo -u printfarm ./scripts/deploy.sh
            else
                git pull origin test_v1
                ./scripts/deploy.sh
            fi
            ;;
        3)
            print_info "Логи в реальном времени (Ctrl+C для выхода):"
            cd "$APP_DIR"
            if [ "$USER" = "root" ]; then
                sudo -u printfarm docker-compose -f docker-compose.prod.yml logs -f
            else
                docker-compose -f docker-compose.prod.yml logs -f
            fi
            ;;
        4)
            print_info "GitHub Actions статус:"
            echo "Перейдите в https://github.com/DeviceIngineering/printfarm-production/actions"
            ;;
        5)
            print_info "Настройка Telegram уведомлений:"
            echo "1. Создайте бота через @BotFather"
            echo "2. Получите токен бота и chat_id"
            echo "3. Добавьте в /opt/printfarm/webhook.env:"
            echo "   TELEGRAM_BOT_TOKEN=your_token"
            echo "   TELEGRAM_CHAT_ID=your_chat_id"
            echo "4. Перезапустите webhook: sudo systemctl restart printfarm-webhook.service"
            ;;
        0|"")
            print_info "Выход из диагностики"
            ;;
        *)
            print_warning "Неверный выбор"
            ;;
    esac
}

# Главная функция
main() {
    # Создание лог файла
    echo "PrintFarm Diagnostic Log - $(date)" > "$LOG_FILE"
    
    print_header "🏭 PrintFarm Production System - Диагностика"
    print_info "Диагностический лог: $LOG_FILE"
    
    # Последовательная проверка всех компонентов
    check_permissions
    check_system  
    check_code
    check_containers
    check_connectivity
    check_logs
    
    # Автоматические исправления
    auto_fix
    
    # Повторная проверка после исправлений
    if [ "$FIX_APPLIED" -gt 0 ]; then
        print_header "🔄 Повторная проверка после исправлений"
        sleep 10
        check_containers
        check_connectivity
    fi
    
    # Генерация отчета
    generate_report
    
    # Интерактивное меню
    interactive_menu "$@"
    
    # Итоговый статус
    print_header "📊 Итоговый статус"
    if [ "$ISSUES_FOUND" -eq 0 ]; then
        print_success "Система работает корректно! ✨"
        echo -e "${GREEN}Все компоненты PrintFarm функционируют нормально.${NC}"
    else
        print_warning "Обнаружено проблем: $ISSUES_FOUND"
        if [ "$FIX_APPLIED" -gt 0 ]; then
            print_info "Применено исправлений: $FIX_APPLIED"
            print_info "Рекомендуется повторный запуск диагностики через несколько минут"
        fi
        echo -e "${YELLOW}Проверьте детальные логи: $LOG_FILE${NC}"
    fi
    
    local server_ip=$(hostname -I | awk '{print $1}')
    echo -e "\n${CYAN}🌐 Ваш сайт: ${BOLD}http://$server_ip:8080/${NC}"
    echo -e "${CYAN}📚 Документация: AUTO-DEPLOY.md${NC}"
}

# Проверка аргументов командной строки
case "${1:-}" in
    --help|-h)
        echo "PrintFarm Production System - Диагностический скрипт"
        echo ""
        echo "Использование:"
        echo "  ./scripts/diagnose.sh [опции]"
        echo ""
        echo "Опции:"
        echo "  --auto    Автоматический режим (без интерактивного меню)"
        echo "  --help    Показать эту справку"
        echo ""
        echo "Скрипт выполняет полную диагностику системы и автоматически"
        echo "исправляет найденные проблемы."
        exit 0
        ;;
    --auto)
        main --auto
        ;;
    *)
        main "$@"
        ;;
esac