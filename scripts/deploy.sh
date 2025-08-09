#!/bin/bash

# Скрипт развертывания PrintFarm Production System
# Запускать от имени пользователя printfarm в директории /opt/printfarm

set -e

echo "=========================================="
echo "PrintFarm Production Deployment"
echo "=========================================="

# Переменные
REPO_URL="https://github.com/DeviceIngineering/printfarm-production.git"
REPO_BRANCH="test_v1"
APP_DIR="/opt/printfarm"
BACKUP_DIR="/opt/printfarm/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Проверка пользователя
if [ "$USER" != "printfarm" ]; then
    echo "Ошибка: Скрипт должен запускаться от пользователя printfarm"
    echo "Выполните: sudo su - printfarm"
    exit 1
fi

# Проверка Docker
if ! command -v docker &> /dev/null; then
    echo "Ошибка: Docker не установлен"
    exit 1
fi

# Создание директории для бэкапов
mkdir -p $BACKUP_DIR

# Функция для бэкапа базы данных
backup_database() {
    echo "Создание бэкапа базы данных..."
    if docker-compose -f docker-compose.prod.yml ps | grep -q postgres; then
        docker-compose -f docker-compose.prod.yml exec -T postgres pg_dump -U printfarm_user printfarm_db > $BACKUP_DIR/db_backup_$DATE.sql
        echo "Бэкап базы данных сохранен: $BACKUP_DIR/db_backup_$DATE.sql"
    else
        echo "Контейнер PostgreSQL не запущен, пропускаем бэкап"
    fi
}

# Функция для клонирования/обновления репозитория
deploy_code() {
    echo "Развертывание кода..."
    
    if [ -d ".git" ]; then
        echo "Обновление существующего репозитория..."
        git fetch origin
        git reset --hard origin/$REPO_BRANCH
        git clean -fd
    else
        echo "Клонирование репозитория..."
        if [ ! -z "$REPO_URL" ]; then
            git clone -b $REPO_BRANCH $REPO_URL .
            echo "Репозиторий успешно клонирован"
        else
            echo "Ошибка: URL репозитория не указан"
            exit 1
        fi
    fi
}

# Функция для подготовки окружения
prepare_environment() {
    echo "Подготовка окружения..."
    
    # Проверка файла .env.prod
    if [ ! -f ".env.prod" ]; then
        echo "Ошибка: Файл .env.prod не найден"
        echo "Скопируйте .env.example в .env.prod и настройте переменные"
        exit 1
    fi
    
    # Создание символической ссылки на production env файл
    ln -sf .env.prod .env
    
    # Установка правильных прав доступа
    chmod 600 .env.prod
    chmod +x scripts/*.sh
}

# Функция для сборки и запуска контейнеров
deploy_containers() {
    echo "Остановка старых контейнеров..."
    docker-compose -f docker-compose.prod.yml down || true
    
    echo "Сборка новых образов..."
    docker-compose -f docker-compose.prod.yml build --no-cache
    
    echo "Запуск контейнеров..."
    docker-compose -f docker-compose.prod.yml up -d
    
    echo "Ожидание запуска сервисов..."
    sleep 10
}

# Функция для выполнения миграций
run_migrations() {
    echo "Выполнение миграций базы данных..."
    docker-compose -f docker-compose.prod.yml exec -T backend python manage.py migrate --noinput
    
    echo "Сбор статических файлов..."
    docker-compose -f docker-compose.prod.yml exec -T backend python manage.py collectstatic --noinput
}

# Функция для проверки состояния сервисов
check_health() {
    echo "Проверка состояния сервисов..."
    
    # Проверка контейнеров
    echo "Статус контейнеров:"
    docker-compose -f docker-compose.prod.yml ps
    
    # Проверка логов
    echo "Последние логи backend:"
    docker-compose -f docker-compose.prod.yml logs --tail=20 backend
    
    # Простая проверка HTTP
    echo "Проверка HTTP доступности..."
    sleep 5
    if curl -f http://localhost/api/v1/products/ > /dev/null 2>&1; then
        echo "✓ API доступно"
    else
        echo "✗ API недоступно"
    fi
}

# Функция очистки старых образов
cleanup() {
    echo "Очистка старых Docker образов..."
    docker image prune -f
    
    echo "Удаление старых бэкапов (старше 7 дней)..."
    find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
}

# Основной процесс развертывания
main() {
    cd $APP_DIR
    
    echo "Начало развертывания в $(pwd)"
    
    # Создание бэкапа (только если контейнеры уже запущены)
    if [ -f "docker-compose.prod.yml" ] && docker-compose -f docker-compose.prod.yml ps | grep -q Up; then
        backup_database
    fi
    
    # Развертывание кода
    deploy_code
    
    # Подготовка окружения
    prepare_environment
    
    # Развертывание контейнеров
    deploy_containers
    
    # Выполнение миграций
    run_migrations
    
    # Проверка состояния
    check_health
    
    # Очистка
    cleanup
    
    echo "=========================================="
    echo "Развертывание завершено успешно!"
    echo "=========================================="
    echo "Приложение доступно по адресу: http://$(hostname -I | awk '{print $1}')"
    echo "Логи: docker-compose -f docker-compose.prod.yml logs -f"
    echo "Остановка: docker-compose -f docker-compose.prod.yml down"
    echo "=========================================="
}

# Обработка аргументов командной строки
case "${1:-deploy}" in
    deploy)
        main
        ;;
    backup)
        cd $APP_DIR
        backup_database
        ;;
    restart)
        cd $APP_DIR
        echo "Перезапуск сервисов..."
        docker-compose -f docker-compose.prod.yml restart
        check_health
        ;;
    logs)
        cd $APP_DIR
        docker-compose -f docker-compose.prod.yml logs -f
        ;;
    status)
        cd $APP_DIR
        check_health
        ;;
    cleanup)
        cd $APP_DIR
        cleanup
        ;;
    *)
        echo "Использование: $0 {deploy|backup|restart|logs|status|cleanup}"
        echo "  deploy  - Полное развертывание (по умолчанию)"
        echo "  backup  - Создать бэкап базы данных"
        echo "  restart - Перезапустить сервисы"
        echo "  logs    - Показать логи"
        echo "  status  - Проверить состояние"
        echo "  cleanup - Очистить старые данные"
        exit 1
        ;;
esac