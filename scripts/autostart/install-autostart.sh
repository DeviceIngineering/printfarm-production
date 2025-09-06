#!/bin/bash
# ============================================================
# PrintFarm v4.1.8 - Install Autostart Service
# ============================================================
# Установка systemd сервиса для автоматического запуска
# ============================================================

set -e

# Конфигурация
REMOTE_HOST="kemomail3.keenetic.pro"
REMOTE_USER="printfarm"
REMOTE_PORT="2132"
PROJECT_DIR="/home/${REMOTE_USER}/printfarm-test"
SERVICE_NAME="printfarm"

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Логирование
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

# Проверка прав
check_permissions() {
    log_info "Checking permissions..."
    
    if [ "$EUID" -eq 0 ]; then
        log_info "Running as root (local install)"
    else
        log_warning "Not running as root - will install for remote server"
    fi
}

# Установка на удаленном сервере
install_remote() {
    log_info "Installing autostart on remote server ${REMOTE_HOST}..."
    
    # Копируем файлы на удаленный сервер
    log_info "Copying files to remote server..."
    
    # Создаем директорию для скриптов
    ssh -p ${REMOTE_PORT} ${REMOTE_USER}@${REMOTE_HOST} "mkdir -p ${PROJECT_DIR}/scripts"
    
    # Копируем скрипт запуска
    scp -P ${REMOTE_PORT} scripts/autostart/start-printfarm.sh \
        ${REMOTE_USER}@${REMOTE_HOST}:${PROJECT_DIR}/scripts/
    
    # Копируем systemd сервис
    scp -P ${REMOTE_PORT} scripts/autostart/printfarm.service \
        ${REMOTE_USER}@${REMOTE_HOST}:/tmp/
    
    # Устанавливаем сервис на удаленном сервере
    log_info "Installing systemd service on remote server..."
    
    ssh -p ${REMOTE_PORT} ${REMOTE_USER}@${REMOTE_HOST} << 'REMOTE_SCRIPT'
set -e

echo "Setting up autostart service..."

# Делаем скрипт исполняемым
chmod +x /home/printfarm/printfarm-test/scripts/start-printfarm.sh

# Создаем директорию для PID файлов (без sudo пока)
mkdir -p /tmp/printfarm-install

# Создаем установочный скрипт
cat > /tmp/printfarm-install/install.sh << 'INSTALL_EOF'
#!/bin/bash
set -e

# Создаем директорию для PID файлов
mkdir -p /var/run/printfarm
chown printfarm:printfarm /var/run/printfarm

# Копируем сервис файл
cp /tmp/printfarm.service /etc/systemd/system/
chmod 644 /etc/systemd/system/printfarm.service

# Перезагружаем systemd
systemctl daemon-reload

# Включаем автозапуск
systemctl enable printfarm.service

echo "Service installed and enabled successfully"

# Проверяем статус
systemctl status printfarm.service --no-pager || true
INSTALL_EOF

chmod +x /tmp/printfarm-install/install.sh

# Запускаем установку с правами root
echo "Running installation script as root..."
sudo /tmp/printfarm-install/install.sh

# Очистка
rm -rf /tmp/printfarm-install

echo "Installation completed"
REMOTE_SCRIPT
    
    log_success "Remote installation completed"
}

# Установка локально
install_local() {
    log_info "Installing autostart locally..."
    
    # Проверяем наличие файлов
    if [ ! -f "scripts/autostart/start-printfarm.sh" ]; then
        log_error "start-printfarm.sh not found!"
        exit 1
    fi
    
    if [ ! -f "scripts/autostart/printfarm.service" ]; then
        log_error "printfarm.service not found!"
        exit 1
    fi
    
    # Копируем скрипт запуска
    log_info "Installing startup script..."
    sudo cp scripts/autostart/start-printfarm.sh /usr/local/bin/printfarm-start
    sudo chmod +x /usr/local/bin/printfarm-start
    
    # Создаем директорию для PID файлов
    sudo mkdir -p /var/run/printfarm
    
    # Устанавливаем systemd сервис
    log_info "Installing systemd service..."
    sudo cp scripts/autostart/printfarm.service /etc/systemd/system/
    sudo chmod 644 /etc/systemd/system/printfarm.service
    
    # Перезагружаем systemd
    sudo systemctl daemon-reload
    
    # Включаем автозапуск
    log_info "Enabling autostart..."
    sudo systemctl enable printfarm.service
    
    log_success "Local installation completed"
}

# Управление сервисом
manage_service() {
    local action=$1
    local location=$2
    
    if [ "$location" = "remote" ]; then
        log_info "Managing remote service: ${action}..."
        ssh -p ${REMOTE_PORT} ${REMOTE_USER}@${REMOTE_HOST} \
            "sudo systemctl ${action} printfarm.service"
    else
        log_info "Managing local service: ${action}..."
        sudo systemctl ${action} printfarm.service
    fi
    
    log_success "Service ${action} completed"
}

# Проверка статуса
check_status() {
    local location=$1
    
    if [ "$location" = "remote" ]; then
        log_info "Checking remote service status..."
        ssh -p ${REMOTE_PORT} ${REMOTE_USER}@${REMOTE_HOST} \
            "sudo systemctl status printfarm.service --no-pager"
    else
        log_info "Checking local service status..."
        sudo systemctl status printfarm.service --no-pager
    fi
}

# Удаление автозапуска
uninstall() {
    local location=$1
    
    if [ "$location" = "remote" ]; then
        log_info "Uninstalling from remote server..."
        ssh -p ${REMOTE_PORT} ${REMOTE_USER}@${REMOTE_HOST} << 'REMOTE_UNINSTALL'
set -e

# Останавливаем и отключаем сервис
sudo systemctl stop printfarm.service 2>/dev/null || true
sudo systemctl disable printfarm.service 2>/dev/null || true

# Удаляем файлы
sudo rm -f /etc/systemd/system/printfarm.service
sudo rm -rf /var/run/printfarm

# Перезагружаем systemd
sudo systemctl daemon-reload

echo "Service uninstalled successfully"
REMOTE_UNINSTALL
    else
        log_info "Uninstalling locally..."
        
        # Останавливаем и отключаем сервис
        sudo systemctl stop printfarm.service 2>/dev/null || true
        sudo systemctl disable printfarm.service 2>/dev/null || true
        
        # Удаляем файлы
        sudo rm -f /etc/systemd/system/printfarm.service
        sudo rm -f /usr/local/bin/printfarm-start
        sudo rm -rf /var/run/printfarm
        
        # Перезагружаем systemd
        sudo systemctl daemon-reload
    fi
    
    log_success "Uninstallation completed"
}

# Показать логи
show_logs() {
    local location=$1
    
    if [ "$location" = "remote" ]; then
        log_info "Showing remote service logs..."
        ssh -p ${REMOTE_PORT} ${REMOTE_USER}@${REMOTE_HOST} \
            "sudo journalctl -u printfarm.service -n 100 --no-pager"
    else
        log_info "Showing local service logs..."
        sudo journalctl -u printfarm.service -n 100 --no-pager
    fi
}

# Основная функция
main() {
    echo ""
    echo "============================================================"
    echo "   PrintFarm v4.1.8 - Autostart Installation"
    echo "============================================================"
    echo ""
    
    case "${1:-help}" in
        install-remote)
            install_remote
            log_success "Remote autostart installed!"
            log_info "To start the service: $0 start-remote"
            ;;
        install-local)
            check_permissions
            install_local
            log_success "Local autostart installed!"
            log_info "To start the service: $0 start-local"
            ;;
        start-remote)
            manage_service "start" "remote"
            ;;
        start-local)
            manage_service "start" "local"
            ;;
        stop-remote)
            manage_service "stop" "remote"
            ;;
        stop-local)
            manage_service "stop" "local"
            ;;
        restart-remote)
            manage_service "restart" "remote"
            ;;
        restart-local)
            manage_service "restart" "local"
            ;;
        status-remote)
            check_status "remote"
            ;;
        status-local)
            check_status "local"
            ;;
        logs-remote)
            show_logs "remote"
            ;;
        logs-local)
            show_logs "local"
            ;;
        uninstall-remote)
            uninstall "remote"
            ;;
        uninstall-local)
            uninstall "local"
            ;;
        test-remote)
            log_info "Testing remote autostart..."
            ssh -p ${REMOTE_PORT} ${REMOTE_USER}@${REMOTE_HOST} \
                "sudo systemctl restart printfarm.service && sleep 10 && sudo systemctl status printfarm.service --no-pager"
            log_info "Checking if services are accessible..."
            curl -f http://${REMOTE_HOST}:13000/ && echo "Frontend: OK" || echo "Frontend: FAILED"
            curl -f http://${REMOTE_HOST}:13000/api/v1/health/ && echo "API: OK" || echo "API: FAILED"
            ;;
        *)
            echo "Usage: $0 {command} [options]"
            echo ""
            echo "Installation commands:"
            echo "  install-remote    Install autostart on remote server"
            echo "  install-local     Install autostart locally (requires sudo)"
            echo ""
            echo "Service management:"
            echo "  start-remote      Start remote service"
            echo "  start-local       Start local service"
            echo "  stop-remote       Stop remote service"
            echo "  stop-local        Stop local service"
            echo "  restart-remote    Restart remote service"
            echo "  restart-local     Restart local service"
            echo ""
            echo "Monitoring:"
            echo "  status-remote     Check remote service status"
            echo "  status-local      Check local service status"
            echo "  logs-remote       Show remote service logs"
            echo "  logs-local        Show local service logs"
            echo "  test-remote       Test remote autostart"
            echo ""
            echo "Maintenance:"
            echo "  uninstall-remote  Remove autostart from remote server"
            echo "  uninstall-local   Remove autostart locally"
            echo ""
            echo "Remote server configuration:"
            echo "  Host: ${REMOTE_HOST}"
            echo "  User: ${REMOTE_USER}"
            echo "  Port: ${REMOTE_PORT}"
            echo ""
            exit 0
            ;;
    esac
}

# Запуск
main "$@"