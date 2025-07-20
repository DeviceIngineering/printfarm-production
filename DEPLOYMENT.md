# 🚀 Руководство по развертыванию PrintFarm на Linux сервере

## 📋 Содержание
1. [Подготовка сервера](#подготовка-сервера)
2. [Загрузка проекта на сервер](#загрузка-проекта)
3. [Настройка окружения](#настройка-окружения)
4. [Запуск приложения](#запуск-приложения)
5. [Настройка автозапуска](#автозапуск)
6. [Настройка домена и SSL](#домен-и-ssl)
7. [Мониторинг и обслуживание](#мониторинг)

## 🔧 Подготовка сервера

### Шаг 1: Подключение к серверу
```bash
ssh root@your-server-ip
```

### Шаг 2: Создание пользователя для приложения (рекомендуется)
```bash
adduser printfarm
usermod -aG sudo printfarm
su - printfarm
```

### Шаг 3: Обновление системы
```bash
sudo apt update && sudo apt upgrade -y
```

### Шаг 4: Установка необходимых пакетов
```bash
sudo apt install -y git curl wget nginx postgresql redis-server python3-pip python3-venv build-essential libpq-dev
```

### Шаг 5: Установка Docker
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
rm get-docker.sh

# Добавляем пользователя в группу docker
sudo usermod -aG docker $USER
# Перелогиньтесь или выполните: newgrp docker
```

### Шаг 6: Установка Docker Compose
```bash
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

## 📦 Загрузка проекта

### Вариант 1: Через Git (если проект в репозитории)
```bash
cd /opt
sudo git clone https://github.com/yourusername/printfarm.git
sudo chown -R $USER:$USER printfarm
cd printfarm
```

### Вариант 2: Через SCP (загрузка с локального компьютера)
На вашем локальном компьютере:
```bash
# Архивируем проект
cd /Users/dim11/Documents/myProjects/
tar -czf Factory_v2.tar.gz Factory_v2/

# Загружаем на сервер
scp Factory_v2.tar.gz root@your-server-ip:/opt/

# Или используем rsync (рекомендуется)
rsync -avz --exclude 'node_modules' --exclude '.git' --exclude '__pycache__' \
  --exclude '*.pyc' --exclude 'media/*' --exclude 'logs/*' \
  Factory_v2/ root@your-server-ip:/opt/printfarm/
```

На сервере:
```bash
cd /opt
tar -xzf Factory_v2.tar.gz
mv Factory_v2 printfarm
rm Factory_v2.tar.gz
```

## ⚙️ Настройка окружения

### Шаг 1: Создание файла окружения
```bash
cd /opt/printfarm
cp .env.production .env
```

### Шаг 2: Редактирование конфигурации
```bash
nano .env
```

Обязательно измените:
- `SECRET_KEY` - сгенерируйте новый: `python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'`
- `ALLOWED_HOSTS` - укажите ваш домен и IP
- `POSTGRES_PASSWORD` - установите надежный пароль
- `REACT_APP_API_URL` - укажите ваш домен

### Шаг 3: Настройка Nginx
```bash
sudo nano nginx/nginx.prod.conf
```
Замените `your-domain.com` на ваш реальный домен.

## 🚀 Запуск приложения

### Шаг 1: Сборка и запуск контейнеров
```bash
# Сборка образов
docker-compose -f docker-compose.prod.yml build

# Запуск в фоновом режиме
docker-compose -f docker-compose.prod.yml up -d
```

### Шаг 2: Проверка статуса
```bash
docker-compose -f docker-compose.prod.yml ps
```

### Шаг 3: Первоначальная настройка
```bash
# Выполнение миграций
docker-compose -f docker-compose.prod.yml exec backend python manage.py migrate

# Сбор статических файлов
docker-compose -f docker-compose.prod.yml exec backend python manage.py collectstatic --noinput

# Создание суперпользователя
docker-compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser
```

## 🔄 Настройка автозапуска

### Создание systemd сервиса
```bash
sudo nano /etc/systemd/system/printfarm.service
```

Вставьте следующее содержимое:
```ini
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
ExecReload=/usr/local/bin/docker-compose -f docker-compose.prod.yml restart
User=printfarm
StandardOutput=journal

[Install]
WantedBy=multi-user.target
```

### Активация автозапуска
```bash
sudo systemctl daemon-reload
sudo systemctl enable printfarm.service
sudo systemctl start printfarm.service
sudo systemctl status printfarm.service
```

## 🔐 Настройка домена и SSL

### Шаг 1: Настройка DNS
В панели управления вашего домена создайте A-запись:
```
Type: A
Name: @ (или subdomain)
Value: your-server-ip
```

### Шаг 2: Установка Certbot
```bash
sudo apt install certbot python3-certbot-nginx
```

### Шаг 3: Получение SSL сертификата
```bash
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

### Шаг 4: Настройка автообновления сертификата
```bash
sudo systemctl enable certbot.timer
```

## 📊 Мониторинг и обслуживание

### Просмотр логов
```bash
# Все логи
docker-compose -f docker-compose.prod.yml logs -f

# Логи конкретного сервиса
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f celery
```

### Перезапуск сервисов
```bash
# Перезапуск всех сервисов
docker-compose -f docker-compose.prod.yml restart

# Перезапуск конкретного сервиса
docker-compose -f docker-compose.prod.yml restart backend
```

### Обновление приложения
```bash
cd /opt/printfarm

# Получение обновлений
git pull origin main

# Пересборка и перезапуск
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# Применение миграций
docker-compose -f docker-compose.prod.yml exec backend python manage.py migrate
```

### Резервное копирование
```bash
# Backup базы данных
docker-compose -f docker-compose.prod.yml exec db pg_dump -U printfarm_user printfarm_db > backup_$(date +%Y%m%d).sql

# Backup медиафайлов
tar -czf media_backup_$(date +%Y%m%d).tar.gz backend/media/
```

### Мониторинг ресурсов
```bash
# Использование дисков
docker system df

# Статистика контейнеров
docker stats

# Очистка неиспользуемых ресурсов
docker system prune -a
```

## 🆘 Решение проблем

### Ошибка подключения к базе данных
```bash
# Проверьте, запущен ли контейнер с БД
docker-compose -f docker-compose.prod.yml ps db

# Проверьте логи
docker-compose -f docker-compose.prod.yml logs db
```

### Ошибка 502 Bad Gateway
```bash
# Проверьте, запущен ли backend
docker-compose -f docker-compose.prod.yml ps backend

# Проверьте логи Nginx
docker-compose -f docker-compose.prod.yml logs nginx
```

### Недостаточно памяти
```bash
# Проверьте использование памяти
free -h

# Добавьте swap файл
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

## 📝 Чек-лист после развертывания

- [ ] Проверьте, что сайт доступен по IP адресу
- [ ] Настройте домен и проверьте его работу
- [ ] Установите SSL сертификат
- [ ] Проверьте работу админ-панели (/admin)
- [ ] Протестируйте синхронизацию с МойСклад
- [ ] Настройте резервное копирование
- [ ] Настройте мониторинг (опционально)
- [ ] Обновите пароли в .env файле

## 🚨 Важные замечания

1. **Безопасность**: Обязательно измените все пароли по умолчанию
2. **Firewall**: Настройте ufw или iptables для ограничения доступа
3. **Обновления**: Регулярно обновляйте систему и Docker образы
4. **Мониторинг**: Рассмотрите установку систем мониторинга (Prometheus, Grafana)
5. **Бэкапы**: Настройте автоматическое резервное копирование