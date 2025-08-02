# 🚀 Руководство по развертыванию PrintFarm Production v4.6

**Полностью автоматизированное развертывание на Ubuntu Server**  
*Для пользователей без опыта работы с Linux*

## 📋 Оглавление

1. [Требования к серверу](#требования-к-серверу)
2. [Подготовка сервера](#подготовка-сервера)
3. [Автоматическая установка](#автоматическая-установка)
4. [Проверка работоспособности](#проверка-работоспособности)
5. [Управление системой](#управление-системой)
6. [Резервное копирование](#резервное-копирование)
7. [Устранение неполадок](#устранение-неполадок)

---

## 🖥️ Требования к серверу

### Минимальные требования:
- **ОС**: Ubuntu 20.04 LTS или 22.04 LTS
- **RAM**: 2 GB (рекомендуется 4 GB)
- **CPU**: 2 ядра (рекомендуется 4 ядра)
- **Диск**: 20 GB свободного места (рекомендуется 50 GB)
- **Сеть**: Статический IP-адрес или доменное имя

### Рекомендуемые провайдеры VPS:
1. **DigitalOcean** - Droplet Ubuntu 22.04 (4GB RAM, 2 CPU)
2. **Hetzner** - CX21 (4GB RAM, 2 CPU) 
3. **Vultr** - Regular Performance (4GB RAM, 2 CPU)
4. **Linode** - Nanode 4GB

---

## 🔑 Подготовка сервера

### Шаг 1: Получение доступа к серверу

После создания VPS вы получите:
```
IP-адрес: 192.168.1.100 (пример)
Пользователь: root
Пароль: ваш_пароль
```

### Шаг 2: Подключение к серверу

**Для Windows (рекомендуется PuTTY):**
1. Скачайте PuTTY: https://www.putty.org/
2. Запустите PuTTY
3. В поле "Host Name" введите IP-адрес сервера
4. Port: 22
5. Connection type: SSH
6. Нажмите "Open"
7. Введите логин: `root`
8. Введите пароль

**Для Mac/Linux:**
```bash
ssh root@192.168.1.100
# Введите пароль при запросе
```

### Шаг 3: Базовая настройка безопасности

Выполните эти команды по порядку (копируйте и вставляйте):

```bash
# Обновление системы
apt update && apt upgrade -y

# Создание пользователя для приложения
adduser printfarm
usermod -aG sudo printfarm

# Настройка файрвола
ufw allow ssh
ufw allow 80
ufw allow 443
ufw --force enable

# Переключение на пользователя printfarm
su - printfarm
```

---

## ⚡ Автоматическая установка

### Шаг 1: Скачивание установочного скрипта

Выполните под пользователем `printfarm`:

```bash
# Скачивание скрипта установки
wget https://raw.githubusercontent.com/DeviceIngineering/printfarm-production/main/deploy/install.sh

# Или если wget не работает:
curl -O https://raw.githubusercontent.com/DeviceIngineering/printfarm-production/main/deploy/install.sh

# Делаем скрипт исполняемым
chmod +x install.sh

# Запускаем автоматическую установку
./install.sh
```

### Шаг 2: Настройка переменных окружения

Скрипт попросит вас ввести:

```bash
# Настройки базы данных
Database Name (по умолчанию: printfarm_prod): [ENTER]
Database User (по умолчанию: printfarm_user): [ENTER] 
Database Password: [введите_надежный_пароль]

# Настройки Django
Django Secret Key (будет сгенерирован автоматически): [ENTER]
Allowed Hosts (ваш домен или IP): mydomain.com,192.168.1.100

# Настройки МойСклад
MoySklad Token: f9be4985f5e3488716c040ca52b8e04c7c0f9e0b
MoySklad Warehouse ID: 241ed919-a631-11ee-0a80-07a9000bb947

# Email настройки (опционально)
Email Host (для уведомлений): smtp.gmail.com
Email User: your-email@gmail.com
Email Password: your-app-password
```

### Шаг 3: Ожидание завершения установки

Процесс займет 10-15 минут. Скрипт выполнит:

- ✅ Установку Docker и Docker Compose
- ✅ Клонирование репозитория
- ✅ Настройку переменных окружения
- ✅ Сборку и запуск контейнеров
- ✅ Создание суперпользователя
- ✅ Настройку Nginx и SSL
- ✅ Настройку автозапуска

---

## ✅ Проверка работоспособности

### Шаг 1: Проверка статуса сервисов

```bash
# Проверка Docker контейнеров
docker-compose ps

# Ожидаемый результат:
#        Name                      Command              State           Ports         
# ----------------------------------------------------------------------------------
# printfarm_backend_1    gunicorn config.wsgi:app ...   Up      8000/tcp            
# printfarm_celery_1     celery -A config worker  ...   Up                          
# printfarm_db_1         docker-entrypoint.sh pos ...   Up      5432/tcp            
# printfarm_frontend_1   docker-entrypoint.sh npm ...   Up      3000/tcp            
# printfarm_nginx_1      /docker-entrypoint.sh ngi ...   Up      0.0.0.0:80->80/tcp  
# printfarm_redis_1      docker-entrypoint.sh redi ...   Up      6379/tcp            
```

### Шаг 2: Проверка веб-интерфейса

Откройте в браузере:
- `http://ваш-ip-адрес` или `http://ваш-домен.com`
- Должна открыться страница входа PrintFarm

### Шаг 3: Вход в админ-панель

1. Перейдите на `http://ваш-сайт.com/admin/`
2. Войдите с данными суперпользователя (созданными при установке)
3. Проверьте, что все разделы доступны

---

## 🎛️ Управление системой

### Запуск/остановка приложения

```bash
# Переход в папку проекта
cd /home/printfarm/printfarm-production

# Остановка всех сервисов
docker-compose down

# Запуск всех сервисов
docker-compose up -d

# Перезапуск конкретного сервиса
docker-compose restart backend
docker-compose restart frontend
docker-compose restart nginx
```

### Просмотр логов

```bash
# Логи всех сервисов
docker-compose logs

# Логи конкретного сервиса
docker-compose logs backend
docker-compose logs celery
docker-compose logs nginx

# Логи в реальном времени
docker-compose logs -f backend
```

### Обновление приложения

```bash
# Автоматическое обновление (создайте этот скрипт)
cd /home/printfarm/printfarm-production
./deploy/update.sh
```

---

## 💾 Резервное копирование

### Автоматический бэкап

```bash
# Создание скрипта автоматического бэкапа
cd /home/printfarm
chmod +x printfarm-production/deploy/backup.sh

# Запуск ручного бэкапа
./printfarm-production/deploy/backup.sh

# Настройка автоматического бэкапа (ежедневно в 2:00)
crontab -e
# Добавьте строку:
# 0 2 * * * /home/printfarm/printfarm-production/deploy/backup.sh
```

### Восстановление из бэкапа

```bash
# Восстановление последнего бэкапа
cd /home/printfarm/printfarm-production
./deploy/restore.sh backup_2025-07-31_02-00.tar.gz
```

---

## 🔧 Устранение неполадок

### Проблема: Сайт не открывается

```bash
# 1. Проверьте статус контейнеров
docker-compose ps

# 2. Если контейнеры не запущены:
docker-compose up -d

# 3. Проверьте логи nginx
docker-compose logs nginx

# 4. Проверьте файрвол
sudo ufw status
```

### Проблема: Ошибка базы данных

```bash
# 1. Проверьте контейнер базы данных
docker-compose logs db

# 2. Перезапустите базу данных
docker-compose restart db

# 3. Если не помогает, пересоздайте:
docker-compose down
docker volume rm printfarm_postgres_data
docker-compose up -d
# ВНИМАНИЕ: Это удалит все данные!
```

### Проблема: Медленная работа

```bash
# 1. Проверьте использование ресурсов
docker stats

# 2. Проверьте место на диске
df -h

# 3. Очистка Docker кэша
docker system prune -f
```

### Получение помощи

```bash
# Сбор диагностической информации
cd /home/printfarm/printfarm-production
./deploy/diagnostics.sh > diagnostic_report.txt

# Отправьте файл diagnostic_report.txt разработчикам
```

---

## 📞 Контакты технической поддержки

- **GitHub Issues**: https://github.com/DeviceIngineering/printfarm-production/issues
- **Email**: support@printfarm.com
- **Telegram**: @printfarm_support

---

## 📚 Дополнительные ресурсы

- [Официальная документация Docker](https://docs.docker.com/)
- [Docker Compose документация](https://docs.docker.com/compose/)
- [Ubuntu Server Guide](https://ubuntu.com/server/docs)
- [Nginx документация](https://nginx.org/ru/docs/)

---

## ⚡ Быстрый старт (TL;DR)

Для опытных пользователей:

```bash
# 1. Создайте Ubuntu 22.04 VPS
# 2. Подключитесь по SSH
# 3. Выполните:
apt update && apt upgrade -y
adduser printfarm && usermod -aG sudo printfarm
su - printfarm
wget https://raw.githubusercontent.com/DeviceIngineering/printfarm-production/main/deploy/install.sh
chmod +x install.sh && ./install.sh
# 4. Следуйте инструкциям скрипта
# 5. Откройте http://ваш-ip в браузере
```

---

*Автоматизированное развертывание PrintFarm Production v4.6*  
*Дата: 31 июля 2025*