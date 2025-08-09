#!/bin/bash

# Быстрое развертывание на сервере без Git (для первоначальной настройки)

echo "=========================================="
echo "Быстрое развертывание PrintFarm на сервер"
echo "=========================================="

# Проверяем параметры
if [ $# -lt 1 ]; then
    echo "Использование: $0 SERVER_IP [USER]"
    echo "Пример: $0 192.168.1.100"
    echo "Пример: $0 192.168.1.100 ubuntu"
    exit 1
fi

SERVER_IP=$1
SERVER_USER=${2:-ubuntu}  # По умолчанию ubuntu

echo "Сервер: $SERVER_IP"
echo "Пользователь: $SERVER_USER"
echo ""

# Создание архива с нужными файлами
echo "Создание архива для передачи..."
tar -czf /tmp/printfarm-deploy.tar.gz \
    scripts/ \
    docker-compose.prod.yml \
    .env.prod.example \
    DEPLOYMENT.md \
    docker/ \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='node_modules' \
    --exclude='*.log'

echo "Архив создан: /tmp/printfarm-deploy.tar.gz"

# Копирование архива на сервер
echo "Копирование файлов на сервер..."
scp /tmp/printfarm-deploy.tar.gz $SERVER_USER@$SERVER_IP:/tmp/

# Подключение к серверу и выполнение команд
echo "Подключение к серверу для настройки..."
ssh $SERVER_USER@$SERVER_IP << 'ENDSSH'
    echo "Установка базовых пакетов..."
    sudo apt update
    
    # Создание файла install-server.sh на сервере
    cat > /tmp/install-server.sh << 'ENDSCRIPT'
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

echo "=========================================="
echo "Установка завершена!"
echo "=========================================="
ENDSCRIPT

    chmod +x /tmp/install-server.sh
    echo "Запуск установки сервера..."
    sudo /tmp/install-server.sh
    
    echo "Распаковка файлов приложения..."
    sudo su - printfarm -c "
        cd /opt/printfarm
        tar -xzf /tmp/printfarm-deploy.tar.gz
        chmod +x scripts/*.sh
        cp .env.prod.example .env.prod
        echo 'Файлы распакованы в /opt/printfarm'
        ls -la
    "
    
    echo ""
    echo "=========================================="
    echo "ГОТОВО! Следующие шаги:"
    echo "=========================================="
    echo "1. Войдите на сервер: ssh $USER@$(hostname -I | awk '{print $1}')"
    echo "2. Переключитесь на пользователя: sudo su - printfarm"
    echo "3. Перейдите в директорию: cd /opt/printfarm"
    echo "4. Настройте .env.prod: nano .env.prod"
    echo "5. Запустите развертывание: ./scripts/deploy.sh"
    echo "=========================================="
ENDSSH

# Удаление временного архива
rm -f /tmp/printfarm-deploy.tar.gz

echo ""
echo "Файлы успешно скопированы на сервер!"
echo ""
echo "Для завершения установки подключитесь к серверу:"
echo "ssh $SERVER_USER@$SERVER_IP"