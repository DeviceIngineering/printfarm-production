#!/bin/bash

# One-command setup для быстрого развертывания PrintFarm на чистом сервере
# Использование: curl -sSL https://raw.githubusercontent.com/DeviceIngineering/printfarm-production/test_v1/scripts/one-command-setup.sh | bash

set -e

echo "🚀 PrintFarm Auto-Deploy One-Command Setup"
echo "==========================================="

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверка прав root
if [ "$EUID" -ne 0 ]; then
    print_error "Пожалуйста, запустите скрипт с правами root (sudo)"
    print_warning "Пример: curl -sSL https://raw.githubusercontent.com/DeviceIngineering/printfarm-production/test_v1/scripts/one-command-setup.sh | sudo bash"
    exit 1
fi

# Определяем пользователя, который запустил sudo
REAL_USER=${SUDO_USER:-$USER}
if [ "$REAL_USER" = "root" ]; then
    print_warning "Скрипт запущен напрямую от root. Рекомендуется запускать через sudo от обычного пользователя."
    REAL_USER="ubuntu"  # По умолчанию для облачных серверов
fi

print_status "Пользователь для SSH: $REAL_USER"
print_status "Начинаем установку PrintFarm..."

# Обновление системы
print_status "Обновление системы..."
apt update && apt upgrade -y

# Установка необходимых пакетов
print_status "Установка базовых пакетов..."
apt install -y curl wget git unzip htop nano ufw python3 python3-pip \
    software-properties-common apt-transport-https ca-certificates gnupg lsb-release

# Установка Docker
print_status "Установка Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt update
    apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    usermod -aG docker $REAL_USER
    print_success "Docker установлен"
else
    print_success "Docker уже установлен"
fi

# Установка Docker Compose
print_status "Установка Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    print_success "Docker Compose установлен"
else
    print_success "Docker Compose уже установлен"
fi

# Настройка файрвола
print_status "Настройка файрвола..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 9000/tcp  # Webhook port
ufw --force enable
print_success "Файрвол настроен"

# Создание пользователя printfarm
print_status "Создание пользователя printfarm..."
if ! id "printfarm" &>/dev/null; then
    useradd -m -s /bin/bash printfarm
    usermod -aG docker printfarm
    print_success "Пользователь printfarm создан"
else
    print_success "Пользователь printfarm уже существует"
fi

# Создание директорий
print_status "Создание директорий..."
mkdir -p /opt/printfarm/{data/{postgres,redis,media,static},logs/{deploy,webhook},backups}
chown -R printfarm:printfarm /opt/printfarm

# Клонирование репозитория
print_status "Клонирование репозитория PrintFarm..."
cd /opt/printfarm

# GitHub токен для клонирования (опционально, для приватных репозиториев)
GITHUB_TOKEN="${GITHUB_TOKEN:-}"
if [ -n "$GITHUB_TOKEN" ]; then
    REPO_URL="https://DeviceEngineering:$GITHUB_TOKEN@github.com/DeviceEngineering/printfarm-production.git"
    print_status "Используется авторизация с токеном GitHub"
else
    REPO_URL="https://github.com/DeviceEngineering/printfarm-production.git"
    print_status "Клонирование публичного репозитория"
fi

if [ -d ".git" ]; then
    print_status "Обновление существующего репозитория..."
    sudo -u printfarm git fetch origin
    sudo -u printfarm git reset --hard origin/test_v1
    sudo -u printfarm git clean -fd
else
    print_status "Клонирование репозитория..."
    sudo -u printfarm git clone -b test_v1 "$REPO_URL" .
    
    # Настройка git для пользователя printfarm
    sudo -u printfarm git config user.name "PrintFarm Deploy"
    sudo -u printfarm git config user.email "deploy@printfarm.local"
fi

# Установка прав на скрипты
chmod +x scripts/*.sh scripts/*.py
chown -R printfarm:printfarm /opt/printfarm

# Создание конфигурационного файла
print_status "Создание конфигурации..."
if [ ! -f ".env.prod" ]; then
    sudo -u printfarm cp .env.prod.example .env.prod
    print_warning "Не забудьте настроить файл .env.prod!"
fi

# Генерация webhook секрета
WEBHOOK_SECRET=$(openssl rand -hex 32)

# Создание конфигурации webhook
cat > /opt/printfarm/webhook.env << EOF
WEBHOOK_SECRET=$WEBHOOK_SECRET
WEBHOOK_PORT=9000
PYTHONUNBUFFERED=1
EOF
chmod 600 /opt/printfarm/webhook.env
chown printfarm:printfarm /opt/printfarm/webhook.env

# Создание systemd сервиса для webhook
print_status "Создание systemd сервисов..."
cat > /etc/systemd/system/printfarm-webhook.service << EOF
[Unit]
Description=PrintFarm Webhook Service
After=network.target
Wants=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/printfarm
EnvironmentFile=/opt/printfarm/webhook.env
ExecStart=/usr/bin/python3 /opt/printfarm/scripts/webhook-deploy.py
Restart=always
RestartSec=10
StandardOutput=append:/opt/printfarm/logs/webhook/service.log
StandardError=append:/opt/printfarm/logs/webhook/service.log

# Security settings
NoNewPrivileges=yes
PrivateTmp=yes
ProtectHome=yes
ProtectSystem=strict
ReadWritePaths=/opt/printfarm

[Install]
WantedBy=multi-user.target
EOF

# Создание основного сервиса приложения
cat > /etc/systemd/system/printfarm.service << EOF
[Unit]
Description=PrintFarm Production System
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/printfarm
ExecStart=/usr/local/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker-compose.prod.yml down
User=printfarm
Group=printfarm

[Install]
WantedBy=multi-user.target
EOF

# Настройка ротации логов
print_status "Настройка ротации логов..."
cat > /etc/logrotate.d/printfarm << EOF
/opt/printfarm/logs/webhook/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    copytruncate
    su printfarm printfarm
}

/opt/printfarm/logs/deploy/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    copytruncate
    su printfarm printfarm
}
EOF

# Создание SSH ключей для GitHub Actions
print_status "Создание SSH ключей для GitHub Actions..."
sudo -u printfarm mkdir -p /home/printfarm/.ssh
if [ ! -f "/home/printfarm/.ssh/github_deploy_key" ]; then
    sudo -u printfarm ssh-keygen -t ed25519 -C "github-actions-deploy" -f /home/printfarm/.ssh/github_deploy_key -N ""
    sudo -u printfarm cat /home/printfarm/.ssh/github_deploy_key.pub >> /home/printfarm/.ssh/authorized_keys
    chmod 600 /home/printfarm/.ssh/authorized_keys
    chown printfarm:printfarm /home/printfarm/.ssh/authorized_keys
fi

# Запуск сервисов
print_status "Запуск сервисов..."
systemctl daemon-reload
systemctl enable printfarm.service
systemctl enable printfarm-webhook.service
systemctl start printfarm-webhook.service

# Проверка webhook сервиса
sleep 3
if curl -f -s "http://localhost:9000/health" > /dev/null; then
    print_success "Webhook сервис запущен"
else
    print_warning "Webhook сервис не отвечает"
fi

# Получаем IP адрес сервера
SERVER_IP=$(hostname -I | awk '{print $1}')

echo ""
echo "🎉 Установка завершена!"
echo "======================"
print_success "PrintFarm готов к автоматическому развертыванию"
echo ""
echo "📋 Следующие шаги:"
echo "1. Настройте файл конфигурации:"
echo "   sudo nano /opt/printfarm/.env.prod"
echo ""
echo "2. Добавьте GitHub Secrets в репозиторий:"
echo "   DEPLOY_HOST: $SERVER_IP"
echo "   DEPLOY_USER: $REAL_USER"
echo "   DEPLOY_KEY: (содержимое ключа ниже)"
echo ""
echo "3. SSH ключ для GitHub Actions:"
print_warning "Скопируйте этот ключ в GitHub Secret DEPLOY_KEY:"
echo "---BEGIN PRIVATE KEY---"
cat /home/printfarm/.ssh/github_deploy_key
echo "---END PRIVATE KEY---"
echo ""
echo "4. Webhook настройки (если используете):"
echo "   URL: http://$SERVER_IP:9000/webhook"
echo "   Secret: $WEBHOOK_SECRET"
echo ""
echo "5. Первый деплой:"
echo "   cd /opt/printfarm && sudo -u printfarm ./scripts/deploy.sh"
echo ""
echo "📊 Полезные команды:"
echo "   sudo /opt/printfarm/scripts/monitor-deploy.sh health"
echo "   sudo /opt/printfarm/scripts/monitor-deploy.sh status"
echo "   sudo /opt/printfarm/scripts/monitor-deploy.sh logs"
echo ""
echo "📱 Для настройки Telegram уведомлений:"
echo "   sudo nano /opt/printfarm/webhook.env"
echo "   # Добавьте TELEGRAM_BOT_TOKEN и TELEGRAM_CHAT_ID"
echo ""
print_success "Сервер готов для автоматического развертывания!"
echo "Сделайте push в ветку test_v1 и проверьте GitHub Actions"