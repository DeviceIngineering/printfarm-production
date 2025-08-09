#!/bin/bash

# Скрипт настройки автоматического развертывания
# Запускать на сервере от имени root

set -e

echo "=========================================="
echo "Настройка автоматического развертывания PrintFarm"
echo "=========================================="

# Проверка прав root
if [ "$EUID" -ne 0 ]; then
    echo "Пожалуйста, запустите скрипт с правами root (sudo)"
    exit 1
fi

# Переменные
WEBHOOK_PORT=9000
WEBHOOK_SECRET=""
APP_DIR="/opt/printfarm"

# Функция для генерации случайного секрета
generate_webhook_secret() {
    openssl rand -hex 32
}

# Проверка зависимостей
echo "Проверка зависимостей..."
if ! command -v python3 &> /dev/null; then
    echo "Установка Python3..."
    apt update
    apt install -y python3 python3-pip
fi

if ! command -v openssl &> /dev/null; then
    echo "Установка OpenSSL..."
    apt install -y openssl
fi

# Создание директорий
echo "Создание необходимых директорий..."
mkdir -p $APP_DIR/logs/deploy
mkdir -p $APP_DIR/logs/webhook
mkdir -p /etc/systemd/system
chown -R printfarm:printfarm $APP_DIR/logs

# Генерация webhook секрета если не задан
if [ -z "$WEBHOOK_SECRET" ]; then
    WEBHOOK_SECRET=$(generate_webhook_secret)
    echo "Сгенерирован webhook секрет: $WEBHOOK_SECRET"
fi

# Создание файла окружения для webhook
echo "Создание конфигурации webhook..."
cat > /opt/printfarm/webhook.env << EOF
# Webhook configuration
WEBHOOK_SECRET=$WEBHOOK_SECRET
WEBHOOK_PORT=$WEBHOOK_PORT
PYTHONUNBUFFERED=1
EOF

chmod 600 /opt/printfarm/webhook.env
chown printfarm:printfarm /opt/printfarm/webhook.env

# Создание systemd сервиса для webhook
echo "Создание systemd сервиса webhook..."
cat > /etc/systemd/system/printfarm-webhook.service << EOF
[Unit]
Description=PrintFarm Webhook Service
After=network.target
Wants=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$APP_DIR
EnvironmentFile=$APP_DIR/webhook.env
ExecStart=/usr/bin/python3 $APP_DIR/scripts/webhook-deploy.py
Restart=always
RestartSec=10
StandardOutput=append:$APP_DIR/logs/webhook/service.log
StandardError=append:$APP_DIR/logs/webhook/service.log

# Security settings
NoNewPrivileges=yes
PrivateTmp=yes
ProtectHome=yes
ProtectSystem=strict
ReadWritePaths=$APP_DIR

[Install]
WantedBy=multi-user.target
EOF

# Обновление файрвола для webhook порта
echo "Настройка файрвола..."
ufw allow $WEBHOOK_PORT/tcp comment "PrintFarm Webhook"

# Создание скрипта для мониторинга деплоев
echo "Создание скрипта мониторинга..."
cat > $APP_DIR/scripts/monitor-deploy.sh << 'ENDSCRIPT'
#!/bin/bash

# Скрипт мониторинга состояния развертывания

LOGS_DIR="/opt/printfarm/logs"
STATUS_FILE="$LOGS_DIR/last_deployment.json"

case "${1:-status}" in
    status)
        if [ -f "$STATUS_FILE" ]; then
            echo "Последнее развертывание:"
            python3 -m json.tool "$STATUS_FILE"
        else
            echo "Информация о развертывании недоступна"
        fi
        ;;
    logs)
        echo "Последние логи webhook:"
        tail -n 50 "$LOGS_DIR/webhook.log" 2>/dev/null || echo "Лог webhook недоступен"
        
        echo ""
        echo "Последние логи развертывания:"
        LAST_DEPLOY_LOG=$(find "$LOGS_DIR/deploy" -name "*.log" -type f -printf "%T@ %p\n" 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2-)
        if [ -n "$LAST_DEPLOY_LOG" ]; then
            echo "Файл: $LAST_DEPLOY_LOG"
            tail -n 30 "$LAST_DEPLOY_LOG"
        else
            echo "Логи развертывания недоступны"
        fi
        ;;
    health)
        echo "Проверка состояния служб..."
        echo ""
        echo "Webhook сервис:"
        systemctl is-active printfarm-webhook.service
        
        echo ""
        echo "PrintFarm контейнеры:"
        if [ -f "/opt/printfarm/docker-compose.prod.yml" ]; then
            cd /opt/printfarm && docker-compose -f docker-compose.prod.yml ps
        else
            echo "Docker compose файл не найден"
        fi
        
        echo ""
        echo "Webhook endpoint:"
        if curl -f -s "http://localhost:$WEBHOOK_PORT/health" > /dev/null; then
            echo "✓ Webhook доступен"
            curl -s "http://localhost:$WEBHOOK_PORT/health" | python3 -m json.tool
        else
            echo "✗ Webhook недоступен"
        fi
        ;;
    restart-webhook)
        echo "Перезапуск webhook сервиса..."
        systemctl restart printfarm-webhook.service
        sleep 2
        systemctl status printfarm-webhook.service
        ;;
    *)
        echo "Использование: $0 {status|logs|health|restart-webhook}"
        echo "  status         - Статус последнего развертывания"
        echo "  logs          - Просмотр логов"
        echo "  health        - Проверка состояния всех служб"
        echo "  restart-webhook - Перезапуск webhook сервиса"
        exit 1
        ;;
esac
ENDSCRIPT

chmod +x $APP_DIR/scripts/monitor-deploy.sh
chown printfarm:printfarm $APP_DIR/scripts/monitor-deploy.sh

# Создание cron задач для очистки логов
echo "Настройка ротации логов..."
cat > /etc/logrotate.d/printfarm-webhook << EOF
$APP_DIR/logs/webhook/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    copytruncate
    su printfarm printfarm
}

$APP_DIR/logs/deploy/*.log {
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

# Включение и запуск сервисов
echo "Включение сервисов..."
systemctl daemon-reload
systemctl enable printfarm-webhook.service
systemctl start printfarm-webhook.service

# Проверка статуса
echo ""
echo "Проверка статуса сервисов..."
systemctl status printfarm-webhook.service --no-pager

# Проверка webhook endpoint
echo ""
echo "Проверка webhook endpoint..."
sleep 3
if curl -f -s "http://localhost:$WEBHOOK_PORT/health" > /dev/null; then
    echo "✓ Webhook сервис запущен и доступен"
    curl -s "http://localhost:$WEBHOOK_PORT/health" | python3 -m json.tool
else
    echo "✗ Webhook сервис недоступен"
    echo "Проверьте логи: journalctl -u printfarm-webhook.service -f"
fi

echo ""
echo "=========================================="
echo "Автоматическое развертывание настроено!"
echo "=========================================="
echo ""
echo "Следующие шаги:"
echo ""
echo "1. Настройте GitHub Secrets в вашем репозитории:"
echo "   - DEPLOY_HOST: IP или домен вашего сервера"
echo "   - DEPLOY_USER: пользователь для SSH (обычно ubuntu или ваш пользователь)"
echo "   - DEPLOY_KEY: приватный SSH ключ для подключения"
echo ""
echo "2. Настройте GitHub Webhook (если используете):"
echo "   - URL: http://ВАШ_СЕРВЕР:$WEBHOOK_PORT/webhook"
echo "   - Secret: $WEBHOOK_SECRET"
echo "   - Content type: application/json"
echo "   - Events: push"
echo ""
echo "3. Команды для мониторинга:"
echo "   sudo $APP_DIR/scripts/monitor-deploy.sh health"
echo "   sudo $APP_DIR/scripts/monitor-deploy.sh status"
echo "   sudo $APP_DIR/scripts/monitor-deploy.sh logs"
echo ""
echo "4. Логи сервисов:"
echo "   journalctl -u printfarm-webhook.service -f"
echo "   tail -f $APP_DIR/logs/webhook.log"
echo ""
echo "Webhook секрет сохранен в: /opt/printfarm/webhook.env"
echo "=========================================="