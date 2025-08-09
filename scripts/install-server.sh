#!/bin/bash

# Скрипт подготовки сервера для PrintFarm Production System
# Для Ubuntu/Debian Linux

set -e  # Остановить выполнение при ошибке

echo "=========================================="
echo "PrintFarm Production Server Setup"
echo "=========================================="

# Проверка прав root
if [ "$EUID" -ne 0 ]; then
    echo "Пожалуйста, запустите скрипт с правами root (sudo)"
    exit 1
fi

# Обновление системы
echo "Обновление системы..."
apt update && apt upgrade -y

# Установка необходимых пакетов
echo "Установка базовых пакетов..."
apt install -y \
    curl \
    wget \
    git \
    unzip \
    htop \
    nano \
    ufw \
    certbot \
    python3-certbot-nginx \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release

# Установка Docker
echo "Установка Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt update
    apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    
    # Добавление пользователя в группу docker
    usermod -aG docker $SUDO_USER
    
    echo "Docker установлен успешно"
else
    echo "Docker уже установлен"
fi

# Установка Docker Compose (standalone)
echo "Установка Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    echo "Docker Compose установлен успешно"
else
    echo "Docker Compose уже установлен"
fi

# Настройка файрвола
echo "Настройка файрвола..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# Создание пользователя для приложения
echo "Создание пользователя printfarm..."
if ! id "printfarm" &>/dev/null; then
    useradd -m -s /bin/bash printfarm
    usermod -aG docker printfarm
    echo "Пользователь printfarm создан"
else
    echo "Пользователь printfarm уже существует"
fi

# Создание директории для приложения
echo "Создание директории приложения..."
mkdir -p /opt/printfarm
chown printfarm:printfarm /opt/printfarm

# Создание директорий для данных
mkdir -p /opt/printfarm/data/postgres
mkdir -p /opt/printfarm/data/redis
mkdir -p /opt/printfarm/data/media
mkdir -p /opt/printfarm/data/static
mkdir -p /opt/printfarm/logs
chown -R printfarm:printfarm /opt/printfarm

# Настройка логов
echo "Настройка ротации логов..."
cat > /etc/logrotate.d/printfarm << EOF
/opt/printfarm/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    copytruncate
    su printfarm printfarm
}
EOF

# Оптимизация Docker для production
echo "Настройка Docker для production..."
cat > /etc/docker/daemon.json << EOF
{
    "log-driver": "json-file",
    "log-opts": {
        "max-size": "10m",
        "max-file": "3"
    },
    "storage-driver": "overlay2",
    "live-restore": true
}
EOF

systemctl restart docker

# Создание systemd сервиса для автозапуска
echo "Создание systemd сервиса..."
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

systemctl daemon-reload
systemctl enable printfarm.service

echo "=========================================="
echo "Установка завершена!"
echo "=========================================="
echo "Следующие шаги:"
echo "1. Перелогиньтесь или выполните: newgrp docker"
echo "2. Переключитесь на пользователя printfarm: sudo su - printfarm"
echo "3. Перейдите в /opt/printfarm и запустите deploy.sh"
echo "=========================================="