# Инструкция по развертыванию PrintFarm Production System

## Подготовка к развертыванию

### 1. Подготовка Git репозитория

1. Создайте Git репозиторий для проекта:
```bash
# На локальной машине
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/username/printfarm-production.git
git push -u origin main
```

2. Отредактируйте файл `scripts/deploy.sh` и укажите правильный URL вашего репозитория в переменной `REPO_URL`.

### 2. Подготовка сервера

**Требования:**
- Ubuntu 20.04 LTS или новее / Debian 11 или новее
- Минимум 4 GB RAM
- Минимум 20 GB свободного места на диске
- SSH доступ с правами sudo

### 3. Настройка домена (опционально)

Если у вас есть домен:
1. Настройте DNS записи A для вашего домена на IP сервера
2. После развертывания настройте SSL сертификат

## Развертывание на сервере

### Шаг 1: Подключение к серверу

```bash
ssh user@your-server-ip
```

### Шаг 2: Подготовка сервера

Скопируйте и запустите скрипт подготовки сервера:

```bash
# Скачайте скрипт подготовки
wget https://raw.githubusercontent.com/username/printfarm-production/main/scripts/install-server.sh
chmod +x install-server.sh

# Запустите от имени root
sudo ./install-server.sh
```

Скрипт автоматически:
- Обновит систему
- Установит Docker и Docker Compose
- Настроит файрвол
- Создаст пользователя `printfarm`
- Настроит системный сервис

### Шаг 3: Переключение на пользователя приложения

```bash
# Перелогиньтесь или обновите группы
newgrp docker

# Переключитесь на пользователя приложения
sudo su - printfarm
cd /opt/printfarm
```

### Шаг 4: Клонирование проекта

```bash
# Клонируйте репозиторий проекта
git clone https://github.com/username/printfarm-production.git .

# Или скопируйте файлы вручную если Git репозиторий не настроен
```

### Шаг 5: Настройка переменных окружения

```bash
# Скопируйте пример конфигурации
cp .env.prod.example .env.prod

# Отредактируйте файл конфигурации
nano .env.prod
```

**Обязательно измените следующие параметры:**
- `SECRET_KEY` - сгенерируйте новый секретный ключ
- `POSTGRES_PASSWORD` - установите надежный пароль для БД
- `ALLOWED_HOSTS` - укажите IP сервера или домен
- `MOYSKLAD_TOKEN` - ваш токен API МойСклад
- `MOYSKLAD_DEFAULT_WAREHOUSE` - ID склада из МойСклад

### Шаг 6: Развертывание приложения

```bash
# Запустите скрипт развертывания
./scripts/deploy.sh
```

Скрипт автоматически:
- Создаст бэкап базы данных (при обновлении)
- Соберет Docker образы
- Запустит все сервисы
- Выполнит миграции базы данных
- Соберет статические файлы
- Проверит состояние сервисов

### Шаг 7: Проверка развертывания

После успешного развертывания проверьте:

```bash
# Статус контейнеров
docker-compose -f docker-compose.prod.yml ps

# Логи всех сервисов
docker-compose -f docker-compose.prod.yml logs

# Проверка API
curl http://localhost/api/v1/products/
```

## Настройка SSL (опционально)

Если у вас есть домен, настройте SSL сертификат:

```bash
# Получите SSL сертификат от Let's Encrypt
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Настройте автообновление
sudo crontab -e
# Добавьте строку:
0 12 * * * /usr/bin/certbot renew --quiet
```

## Системный сервис

Приложение настроено как системный сервис:

```bash
# Запуск
sudo systemctl start printfarm

# Остановка
sudo systemctl stop printfarm

# Перезапуск
sudo systemctl restart printfarm

# Статус
sudo systemctl status printfarm

# Автозапуск
sudo systemctl enable printfarm
```

## Ежедневное обслуживание

### Команды управления

```bash
# Переключитесь на пользователя printfarm
sudo su - printfarm
cd /opt/printfarm

# Просмотр логов
./scripts/deploy.sh logs

# Проверка состояния
./scripts/deploy.sh status

# Создание бэкапа БД
./scripts/deploy.sh backup

# Перезапуск сервисов
./scripts/deploy.sh restart

# Очистка старых данных
./scripts/deploy.sh cleanup
```

### Обновление приложения

```bash
# Переключитесь на пользователя printfarm
sudo su - printfarm
cd /opt/printfarm

# Полное обновление (загрузка кода + развертывание)
./scripts/deploy.sh deploy
```

## Мониторинг

### Логи

Логи хранятся в `/opt/printfarm/logs/`:
- `nginx/` - логи веб-сервера
- `django.log` - логи Django приложения
- `celery.log` - логи фоновых задач

### Бэкапы

Бэкапы базы данных автоматически создаются в `/opt/printfarm/backups/` и хранятся 30 дней.

### Мониторинг ресурсов

```bash
# Использование ресурсов контейнерами
docker stats

# Размер логов Docker
docker system df

# Очистка неиспользуемых данных Docker
docker system prune -f
```

## Устранение неполадок

### Проблемы с запуском

1. **Контейнеры не запускаются:**
```bash
docker-compose -f docker-compose.prod.yml logs
```

2. **Ошибки базы данных:**
```bash
docker-compose -f docker-compose.prod.yml exec db psql -U printfarm_user -d printfarm_db
```

3. **Проблемы с правами доступа:**
```bash
sudo chown -R printfarm:printfarm /opt/printfarm
```

### Восстановление из бэкапа

```bash
# Остановите сервисы
docker-compose -f docker-compose.prod.yml down

# Восстановите базу данных
docker-compose -f docker-compose.prod.yml up -d db
docker-compose -f docker-compose.prod.yml exec -T db psql -U printfarm_user -d printfarm_db < /opt/printfarm/backups/db_backup_YYYYMMDD_HHMMSS.sql

# Запустите все сервисы
docker-compose -f docker-compose.prod.yml up -d
```

## Полезные команды

### Docker

```bash
# Перезапуск одного сервиса
docker-compose -f docker-compose.prod.yml restart backend

# Выполнение команд Django
docker-compose -f docker-compose.prod.yml exec backend python manage.py shell

# Подключение к базе данных
docker-compose -f docker-compose.prod.yml exec db psql -U printfarm_user -d printfarm_db

# Просмотр логов одного сервиса
docker-compose -f docker-compose.prod.yml logs -f backend
```

### Синхронизация с МойСклад

```bash
# Ручной запуск синхронизации
docker-compose -f docker-compose.prod.yml exec backend python manage.py sync_products

# Проверка задач Celery
docker-compose -f docker-compose.prod.yml exec backend celery -A config inspect active
```

## Контакты и поддержка

При возникновении проблем проверьте:
1. Логи приложения: `/opt/printfarm/logs/`
2. Статус Docker контейнеров: `docker-compose -f docker-compose.prod.yml ps`
3. Доступность API: `curl http://localhost/api/v1/products/`

## Checklist развертывания

- [ ] Сервер подготовлен (install-server.sh выполнен)
- [ ] Git репозиторий настроен и код загружен
- [ ] Файл .env.prod настроен с правильными значениями
- [ ] Развертывание выполнено (deploy.sh успешно завершен)
- [ ] Все контейнеры запущены и работают
- [ ] API доступно через curl
- [ ] SSL сертификат настроен (если нужен)
- [ ] Системный сервис активирован
- [ ] Тестовая синхронизация с МойСклад выполнена

---

**Важно:** После развертывания сохраните:
- Пароли из .env.prod файла
- SSH ключи для доступа к серверу  
- URL и учетные данные для мониторинга