# Автоматическое развертывание PrintFarm

Система автоматического развертывания позволяет автоматически обновлять тестовый сервер при каждом push в репозиторий GitHub.

## 🚀 Возможности

- **GitHub Actions CI/CD**: Автоматические тесты и развертывание
- **Webhook сервер**: Мгновенное развертывание при push
- **Мониторинг**: Отслеживание статуса развертываний
- **Уведомления**: Telegram бот для уведомлений
- **Откат**: Автоматическое создание бэкапов
- **Логирование**: Подробные логи всех операций

## 📋 Настройка автоматического развертывания

### Шаг 1: Настройка SSH ключей

**На сервере создайте SSH ключ для GitHub Actions:**
```bash
# На сервере
sudo su - printfarm
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/github_deploy_key -N ""

# Добавьте публичный ключ в authorized_keys
cat ~/.ssh/github_deploy_key.pub >> ~/.ssh/authorized_keys

# Скопируйте приватный ключ (понадобится для GitHub Secrets)
cat ~/.ssh/github_deploy_key
```

### Шаг 2: Настройка GitHub Secrets

В репозитории GitHub перейдите в **Settings → Secrets and variables → Actions** и добавьте:

- `DEPLOY_HOST`: IP адрес или домен вашего сервера
- `DEPLOY_USER`: имя пользователя для SSH (обычно `ubuntu` или ваш пользователь)
- `DEPLOY_KEY`: содержимое приватного SSH ключа (из предыдущего шага)

### Шаг 3: Настройка сервера для автодеплоя

**На сервере запустите скрипт настройки:**
```bash
# Скачайте и запустите скрипт
sudo /opt/printfarm/scripts/setup-autodeploy.sh
```

Этот скрипт:
- Установит webhook сервер
- Настроит systemd сервисы
- Создаст мониторинг скрипты
- Настроит ротацию логов
- Сгенерирует webhook секрет

### Шаг 4: Настройка GitHub Webhook (опционально)

Если хотите мгновенные развертывания без GitHub Actions:

1. В GitHub репозитории перейдите в **Settings → Webhooks**
2. Нажмите **Add webhook**
3. Заполните:
   - **Payload URL**: `http://ВАШ_СЕРВЕР_IP:9000/webhook`
   - **Content type**: `application/json`
   - **Secret**: секрет из `/opt/printfarm/webhook.env`
   - **Events**: выберите "Just the push event"

## 🔄 Как это работает

### GitHub Actions (рекомендуется)

1. **Push в branch `test_v1`** → GitHub Actions запускается
2. **Тесты кода** → Проверка синтаксиса и форматирования
3. **SSH подключение** → Подключение к серверу
4. **Развертывание** → Обновление кода и перезапуск сервисов
5. **Проверка** → Тест доступности API
6. **Уведомления** → Статус в GitHub Actions

### Webhook (дополнительно)

1. **Push в branch** → GitHub отправляет webhook
2. **Проверка подписи** → Проверка безопасности
3. **Фоновое развертывание** → Обновление в отдельном потоке
4. **Логирование** → Запись всех операций

## 📊 Мониторинг и управление

### Команды мониторинга

```bash
# Общий статус системы
sudo /opt/printfarm/scripts/monitor-deploy.sh health

# Статус последнего развертывания
sudo /opt/printfarm/scripts/monitor-deploy.sh status

# Просмотр логов
sudo /opt/printfarm/scripts/monitor-deploy.sh logs

# Перезапуск webhook сервиса
sudo /opt/printfarm/scripts/monitor-deploy.sh restart-webhook
```

### Логи системы

```bash
# Логи webhook сервиса
journalctl -u printfarm-webhook.service -f

# Логи развертывания
tail -f /opt/printfarm/logs/deploy/webhook-*.log

# Логи контейнеров
cd /opt/printfarm && docker-compose -f docker-compose.prod.yml logs -f
```

### Статус сервисов

```bash
# Статус webhook сервиса
systemctl status printfarm-webhook.service

# Статус контейнеров
cd /opt/printfarm && docker-compose -f docker-compose.prod.yml ps

# Проверка webhook endpoint
curl http://localhost:9000/health
```

## 📱 Telegram уведомления (опционально)

### Настройка Telegram бота

1. **Создайте бота**: Напишите @BotFather в Telegram и выполните `/newbot`
2. **Получите токен**: Сохраните токен бота
3. **Найдите chat_id**: Напишите боту, затем откройте `https://api.telegram.org/botТОКЕН/getUpdates`

### Настройка на сервере

```bash
# Добавьте в /opt/printfarm/webhook.env
echo "TELEGRAM_BOT_TOKEN=your_bot_token" | sudo tee -a /opt/printfarm/webhook.env
echo "TELEGRAM_CHAT_ID=your_chat_id" | sudo tee -a /opt/printfarm/webhook.env

# Перезапустите сервис
sudo systemctl restart printfarm-webhook.service

# Тестируйте уведомления
sudo python3 /opt/printfarm/scripts/telegram-notify.py test
sudo python3 /opt/printfarm/scripts/telegram-notify.py status
```

## 🔧 Настройка развертывания

### Файлы конфигурации

- `/opt/printfarm/webhook.env` - настройки webhook
- `/opt/printfarm/.env.prod` - настройки приложения
- `/opt/printfarm/logs/last_deployment.json` - статус последнего деплоя

### Ветки для автодеплоя

По умолчанию автоматически развертываются ветки:
- `test_v1` - тестовая ветка
- `main` - основная ветка

Для изменения отредактируйте:
- `.github/workflows/deploy.yml` (GitHub Actions)
- `scripts/webhook-deploy.py` (Webhook)

### Изменение портов

Webhook по умолчанию использует порт 9000. Для изменения:

```bash
# Отредактируйте конфигурацию
sudo nano /opt/printfarm/webhook.env
# Измените WEBHOOK_PORT=9000 на нужный порт

# Обновите файрвол
sudo ufw delete allow 9000/tcp
sudo ufw allow НОВЫЙ_ПОРТ/tcp

# Перезапустите сервис
sudo systemctl restart printfarm-webhook.service
```

## 🔒 Безопасность

### Webhook безопасность

- Использование HMAC подписей для проверки запросов
- Фильтрация по веткам
- Ограничение одновременных развертываний
- Логирование всех запросов

### SSH безопасность

- Отдельные SSH ключи для развертывания
- Ограниченные права доступа
- Проверка подлинности GitHub Actions

### Системная безопасность

- Файрвол настроен только для нужных портов
- Сервисы работают с минимальными правами
- Логирование всех операций

## 🚨 Устранение неполадок

### Развертывание не работает

1. **Проверьте GitHub Secrets:**
```bash
# На сервере проверьте SSH подключение
ssh -i ~/.ssh/github_deploy_key ubuntu@localhost
```

2. **Проверьте webhook сервис:**
```bash
sudo systemctl status printfarm-webhook.service
journalctl -u printfarm-webhook.service -n 50
```

3. **Проверьте логи развертывания:**
```bash
sudo /opt/printfarm/scripts/monitor-deploy.sh logs
```

### Webhook не отвечает

```bash
# Проверьте порт
sudo netstat -tlnp | grep 9000

# Проверьте файрвол
sudo ufw status | grep 9000

# Перезапустите сервис
sudo systemctl restart printfarm-webhook.service
```

### Контейнеры не запускаются

```bash
# Проверьте Docker
sudo systemctl status docker

# Проверьте логи контейнеров
cd /opt/printfarm && docker-compose -f docker-compose.prod.yml logs

# Проверьте ресурсы
df -h
free -h
```

### GitHub Actions fails

1. Проверьте Secrets в GitHub
2. Проверьте SSH доступ с локальной машины
3. Проверьте логи в GitHub Actions
4. Убедитесь что сервер доступен по SSH

## 📈 Мониторинг производительности

### Автоматический мониторинг

Система автоматически создает:
- Бэкапы БД перед каждым развертыванием
- Логи всех операций
- Статистику времени развертывания
- Отчеты об ошибках

### Ручной мониторинг

```bash
# Использование ресурсов
htop
docker stats

# Место на диске
df -h /opt/printfarm

# Размер логов
du -sh /opt/printfarm/logs/*

# Время последних развертываний
ls -la /opt/printfarm/logs/deploy/
```

## 🔄 Процесс обновления

### Обычное обновление (автоматическое)

1. Внесите изменения в код
2. Сделайте commit и push в ветку `test_v1`
3. GitHub Actions автоматически развернет изменения
4. Проверьте статус в Actions или через мониторинг

### Ручное развертывание

```bash
# На сервере
sudo su - printfarm
cd /opt/printfarm
./scripts/deploy.sh
```

### Откат к предыдущей версии

```bash
# Найдите нужный бэкап
ls -la /opt/printfarm/backups/

# Остановите сервисы
docker-compose -f docker-compose.prod.yml down

# Восстановите БД
docker-compose -f docker-compose.prod.yml up -d db
docker-compose -f docker-compose.prod.yml exec -T db psql -U printfarm_user -d printfarm_db < backups/BACKUP_FILE.sql

# Откатите код до нужного коммита
git reset --hard COMMIT_HASH

# Запустите сервисы
./scripts/deploy.sh
```

## 📋 Checklist настройки

- [ ] SSH ключи созданы и настроены
- [ ] GitHub Secrets добавлены (DEPLOY_HOST, DEPLOY_USER, DEPLOY_KEY)
- [ ] Скрипт setup-autodeploy.sh выполнен на сервере
- [ ] Webhook сервис запущен и работает
- [ ] GitHub Actions workflow активен
- [ ] Тестовый push в ветку test_v1 успешен
- [ ] Webhook endpoint доступен (если используется)
- [ ] Telegram уведомления настроены (опционально)
- [ ] Мониторинг функционирует
- [ ] Логи записываются корректно

---

## 💡 Полезные команды

```bash
# Быстрая проверка всей системы
sudo /opt/printfarm/scripts/monitor-deploy.sh health

# Просмотр статуса развертывания в реальном времени
watch -n 5 'sudo /opt/printfarm/scripts/monitor-deploy.sh status'

# Очистка старых логов и бэкапов
sudo find /opt/printfarm/logs -name "*.log" -mtime +30 -delete
sudo find /opt/printfarm/backups -name "*.sql" -mtime +7 -delete

# Перезапуск всей системы
sudo systemctl restart printfarm-webhook.service
cd /opt/printfarm && sudo su - printfarm -c 'docker-compose -f docker-compose.prod.yml restart'
```

Теперь ваша система будет автоматически развертываться при каждом изменении кода! 🎉