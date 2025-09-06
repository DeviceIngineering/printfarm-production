# 🚀 PrintFarm v4.1.8 - Минимальные SSH команды

## 🔧 Настройка удаленного сервера

### 1. Отредактируйте конфигурацию в `deploy-remote.sh`

```bash
# Откройте файл и измените эти переменные:
nano deploy-remote.sh

# Найдите и измените:
REMOTE_HOST="kemomail3.keenetic.pro    # ← Ваш сервер
REMOTE_USER="printfarm"                  # ← Ваш SSH пользователь  
REMOTE_PORT="2132"                      # ← SSH порт
```

### 2. Настройка SSH ключей (если не настроены)

```bash
# Создайте SSH ключ (если нет)
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"

# Скопируйте ключ на сервер
ssh-copy-id -p 22 ubuntu@your-test-server.com
```

## 🚀 Команды развертывания

### Полное автоматическое развертывание (одна команда)
```bash
./deploy-remote.sh
```

### Проверка конфигурации
```bash
./deploy-remote.sh --config
```

### Синхронизация только файлов
```bash
./deploy-remote.sh --sync
```

### Проверка статуса
```bash
./deploy-remote.sh --status
```

### Остановка контейнеров
```bash
./deploy-remote.sh --stop
```

### Просмотр логов
```bash
./deploy-remote.sh --logs
```

## 📊 Прямые SSH команды (после развертывания)

### Подключение к серверу
```bash
ssh -p 22 ubuntu@your-test-server.com
```

### Статус контейнеров
```bash
ssh ubuntu@your-test-server.com "cd /opt/printfarm-test && docker-compose -f docker-compose.remote.yml ps"
```

### Логи всех сервисов
```bash
ssh ubuntu@your-test-server.com "cd /opt/printfarm-test && docker-compose -f docker-compose.remote.yml logs -f"
```

### Логи конкретного сервиса
```bash
ssh ubuntu@your-test-server.com "cd /opt/printfarm-test && docker-compose -f docker-compose.remote.yml logs -f printfarm-remote-backend"
```

### Перезапуск сервисов
```bash
ssh ubuntu@your-test-server.com "cd /opt/printfarm-test && docker-compose -f docker-compose.remote.yml restart"
```

### Выполнение команд Django
```bash
# Миграции
ssh ubuntu@your-test-server.com "cd /opt/printfarm-test && docker-compose -f docker-compose.remote.yml exec printfarm-remote-backend python manage.py migrate"

# Создание суперпользователя
ssh ubuntu@your-test-server.com "cd /opt/printfarm-test && docker-compose -f docker-compose.remote.yml exec printfarm-remote-backend python manage.py createsuperuser"

# Django shell
ssh ubuntu@your-test-server.com "cd /opt/printfarm-test && docker-compose -f docker-compose.remote.yml exec printfarm-remote-backend python manage.py shell"
```

### Мониторинг ресурсов
```bash
# Использование ресурсов контейнерами
ssh ubuntu@your-test-server.com "docker stats --format 'table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}'"

# Дисковое пространство
ssh ubuntu@your-test-server.com "df -h && docker system df"
```

### Резервное копирование базы данных
```bash
ssh ubuntu@your-test-server.com "cd /opt/printfarm-test && docker-compose -f docker-compose.remote.yml exec printfarm-remote-db pg_dump -U printfarm_remote printfarm_remote" > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Очистка системы
```bash
# Удаление неиспользуемых образов
ssh ubuntu@your-test-server.com "docker image prune -f"

# Полная остановка и удаление
ssh ubuntu@your-test-server.com "cd /opt/printfarm-test && docker-compose -f docker-compose.remote.yml down -v"
```

## 🌐 URLs после развертывания

Замените `your-test-server.com` на ваш реальный хостнейм/IP:

### Основные сервисы
- **Frontend**: http://your-test-server.com:13000
- **Backend API**: http://your-test-server.com:18000/api/v1/
- **Admin Panel**: http://your-test-server.com:18000/admin/
- **Nginx Load Balancer**: http://your-test-server.com:18080

### Health Checks
- **Backend Health**: http://your-test-server.com:18000/api/v1/health/
- **Detailed Health**: http://your-test-server.com:18000/api/v1/health/detailed/
- **Nginx Health**: http://your-test-server.com:18080/health

### Базы данных (только для администрирования)
- **PostgreSQL**: your-test-server.com:15432
- **Redis**: your-test-server.com:16379

## ⚠️ Учетные данные по умолчанию

**Django Admin:**
- Username: `admin`
- Password: `admin123`

**PostgreSQL:**
- Database: `printfarm_remote`
- Username: `printfarm_remote`
- Password: `printfarm_remote_2025` (зависит от года развертывания)

**Redis:**
- Password: `redis_remote_2025` (зависит от года развертывания)

## 🔥 Экстренные команды

### Если что-то пошло не так
```bash
# Остановить все
./deploy-remote.sh --stop

# Полная пересборка
ssh ubuntu@your-test-server.com "cd /opt/printfarm-test && docker-compose -f docker-compose.remote.yml down -v && docker-compose -f docker-compose.remote.yml build --no-cache && docker-compose -f docker-compose.remote.yml up -d"

# Проверить логи ошибок
ssh ubuntu@your-test-server.com "cd /opt/printfarm-test && docker-compose -f docker-compose.remote.yml logs --tail=100"
```

### Если порты заняты
```bash
# Проверить какие порты заняты
ssh ubuntu@your-test-server.com "ss -tlnp | grep -E ':(13000|15432|16379|18000|18080)'"

# Найти и убить процессы на конкретном порту
ssh ubuntu@your-test-server.com "sudo fuser -k 18000/tcp"
```

## 📞 Поддержка

При проблемах проверьте:
1. SSH доступ к серверу
2. Установлен ли Docker и Docker Compose на сервере  
3. Свободны ли нужные порты
4. Достаточно ли места на диске (минимум 10GB)
5. Правильно ли настроены переменные в `deploy-remote.sh`