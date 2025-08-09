# PrintFarm Production System 🏭

Система автоматического управления производством с интеграцией МойСклад и автоматическим развертыванием.

## 🚀 Быстрое развертывание

### Одной командой на чистом сервере Ubuntu:

```bash
curl -sSL https://raw.githubusercontent.com/DeviceIngineering/printfarm-production/test_v1/scripts/one-command-setup.sh | sudo bash
```

### С GitHub токеном (для приватных репозиториев):

```bash
curl -sSL https://raw.githubusercontent.com/DeviceIngineering/printfarm-production/test_v1/scripts/one-command-setup.sh | sudo GITHUB_TOKEN=your_token_here bash
```

## 📋 Что включено

- ✅ **Автоматическое развертывание**: GitHub Actions + Webhook
- ✅ **Docker контейнеризация**: Полная изоляция сервисов
- ✅ **База данных**: PostgreSQL с автоматическими бэкапами
- ✅ **Кэширование**: Redis для сессий и задач
- ✅ **Фоновые задачи**: Celery для синхронизации
- ✅ **Мониторинг**: Логи, статус, уведомления
- ✅ **Безопасность**: Файрвол, SSL готов
- ✅ **Интеграция МойСклад**: Синхронизация товаров и остатков

## 📖 Документация

- [AUTO-DEPLOY.md](AUTO-DEPLOY.md) - Подробное руководство по автодеплою
- [DEPLOYMENT.md](DEPLOYMENT.md) - Ручное развертывание и настройка
- [CLAUDE.md](CLAUDE.md) - Техническое задание системы

## 🔧 Настройка GitHub Actions

1. **Добавьте Secrets в репозитории:**
   - `DEPLOY_HOST`: IP адрес сервера
   - `DEPLOY_USER`: пользователь SSH (обычно ubuntu)
   - `DEPLOY_KEY`: приватный SSH ключ

2. **Push в ветку `test_v1`** - автоматически развернет изменения

## 🖥️ Системные требования

- **ОС**: Ubuntu 20.04+ / Debian 11+
- **RAM**: Минимум 4GB (рекомендуется 8GB)
- **Диск**: Минимум 20GB свободного места
- **Сеть**: Доступ в интернет для загрузки зависимостей

## 🎯 Быстрый старт после установки

1. **Настройте переменные окружения:**
   ```bash
   sudo nano /opt/printfarm/.env.prod
   ```

2. **Запустите первое развертывание:**
   ```bash
   cd /opt/printfarm
   sudo -u printfarm ./scripts/deploy.sh
   ```

3. **Проверьте статус:**
   ```bash
   sudo /opt/printfarm/scripts/monitor-deploy.sh health
   ```

## 🔄 Управление системой

```bash
# Статус всех сервисов
sudo /opt/printfarm/scripts/monitor-deploy.sh health

# Логи развертывания
sudo /opt/printfarm/scripts/monitor-deploy.sh logs

# Перезапуск webhook
sudo systemctl restart printfarm-webhook.service

# Просмотр логов контейнеров
cd /opt/printfarm && docker-compose -f docker-compose.prod.yml logs -f
```

## 📱 Telegram уведомления (опционально)

1. Создайте бота через @BotFather
2. Добавьте настройки в `/opt/printfarm/webhook.env`:
   ```bash
   TELEGRAM_BOT_TOKEN=your_bot_token
   TELEGRAM_CHAT_ID=your_chat_id
   ```
3. Перезапустите webhook: `sudo systemctl restart printfarm-webhook.service`

## 🔧 API Endpoints

После развертывания доступны:

- `http://your-server/` - Frontend приложение
- `http://your-server/api/v1/products/` - API товаров
- `http://your-server/api/v1/sync/` - API синхронизации
- `http://your-server:9000/health` - Webhook статус

## 🏗️ Архитектура

```
┌─────────────────┐    ┌──────────────┐    ┌───────────────┐
│   GitHub Repo   │────│ GitHub       │────│   Test        │
│                 │    │ Actions      │    │   Server      │
└─────────────────┘    └──────────────┘    └───────────────┘
                                                    │
┌─────────────────┐    ┌──────────────┐    ┌───────────────┐
│   МойСклад      │────│   Backend    │────│  PostgreSQL   │
│   API           │    │   Django     │    │  Database     │
└─────────────────┘    └──────────────┘    └───────────────┘
                                │
                       ┌──────────────┐
                       │    Redis     │
                       │   + Celery   │
                       └──────────────┘
```

## 🐛 Устранение неполадок

### Развертывание не работает
```bash
# Проверьте SSH подключение
ssh ubuntu@your-server

# Проверьте логи
sudo /opt/printfarm/scripts/monitor-deploy.sh logs
```

### Контейнеры не запускаются
```bash
# Проверьте Docker
sudo systemctl status docker

# Проверьте ресурсы
df -h && free -h
```

### API недоступен
```bash
# Проверьте контейнеры
cd /opt/printfarm && docker-compose -f docker-compose.prod.yml ps

# Проверьте логи
docker-compose -f docker-compose.prod.yml logs backend
```

## 🤝 Поддержка

- **Issues**: Создавайте в GitHub Issues
- **Документация**: См. файлы в корне проекта
- **Мониторинг**: Используйте встроенные скрипты мониторинга

## 📄 Лицензия

MIT License - см. файл LICENSE для подробностей.

---

**🎉 Добро пожаловать в PrintFarm Production System!**

Система готова к автоматическому развертыванию при каждом изменении кода.