# 🚀 Настройка GitHub Actions для PrintFarm

## 📋 Быстрый старт

### Шаг 1: Генерация SSH ключей

На вашем локальном компьютере выполните:

```bash
# Генерация нового SSH ключа для деплоя
ssh-keygen -t ed25519 -f ~/.ssh/printfarm_deploy_key -C "github-actions-deploy"

# Просмотр публичного ключа (добавить на сервер)
cat ~/.ssh/printfarm_deploy_key.pub

# Просмотр приватного ключа (добавить в GitHub Secrets)
cat ~/.ssh/printfarm_deploy_key
```

### Шаг 2: Добавление публичного ключа на сервер

Подключитесь к серверу и добавьте публичный ключ:

```bash
# На сервере
ssh printfarm@szboxz66
echo "ВСТАВЬТЕ_ПУБЛИЧНЫЙ_КЛЮЧ_СЮДА" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

### Шаг 3: Настройка GitHub Secrets

1. Перейдите в репозиторий на GitHub
2. Settings → Secrets and variables → Actions
3. Нажмите "New repository secret"
4. Добавьте следующие секреты:

| Secret Name | Value | Описание |
|------------|-------|----------|
| `SSH_PRIVATE_KEY` | Содержимое `~/.ssh/printfarm_deploy_key` | Приватный SSH ключ |
| `SERVER_HOST` | `szboxz66` или IP адрес | Адрес сервера |
| `SERVER_USER` | `printfarm` | Пользователь на сервере |
| `PROJECT_PATH` | `/home/printfarm/printfarm-production` | Путь к проекту |

### Шаг 4: Создание Environment

1. Settings → Environments
2. New environment → "production"
3. Добавьте protection rules (опционально):
   - Required reviewers
   - Deployment branches: только `main`

## 🔧 Структура Workflows

### 1. **deploy.yml** - Основное развертывание
- Запускается при push в `main`
- Можно запустить вручную
- Выполняет полное развертывание с health checks

### 2. **rollback.yml** - Откат изменений
- Только ручной запуск
- Откатывает к предыдущей версии
- Требует указания причины

### 3. **test.yml** - Тестирование
- Запускается при PR в `main` или `develop`
- Прогоняет тесты
- Собирает Docker образы

## 📝 Использование

### Автоматическое развертывание

```bash
# Сделать коммит и push в main
git add .
git commit -m "feat: new feature"
git push origin main

# GitHub Actions автоматически запустит деплой
```

### Ручное развертывание

1. Перейдите в Actions → Deploy to Production
2. Нажмите "Run workflow"
3. Выберите branch и environment
4. Нажмите "Run workflow"

### Откат изменений

1. Перейдите в Actions → Rollback Deployment
2. Нажмите "Run workflow"
3. Укажите причину отката
4. (Опционально) укажите commit SHA
5. Нажмите "Run workflow"

## 🔍 Мониторинг

### Просмотр логов деплоя

1. Actions → выберите workflow run
2. Кликните на job для детальных логов

### Проверка статуса на сервере

```bash
ssh printfarm@szboxz66 'cd ~/printfarm-production && docker-compose ps'
```

## 🛠 Отладка проблем

### Проблема: Permission denied (publickey)

**Решение:** Проверьте SSH ключи
```bash
# Проверка на сервере
ssh printfarm@szboxz66 'ls -la ~/.ssh/authorized_keys'

# Проверка в GitHub Secrets
# Убедитесь что SSH_PRIVATE_KEY содержит весь ключ включая:
# -----BEGIN OPENSSH PRIVATE KEY-----
# ...
# -----END OPENSSH PRIVATE KEY-----
```

### Проблема: docker-compose: command not found

**Решение:** Установите Docker на сервере
```bash
ssh printfarm@szboxz66
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

### Проблема: Health check failed

**Решение:** Проверьте логи на сервере
```bash
ssh printfarm@szboxz66 'cd ~/printfarm-production && docker-compose logs backend --tail=50'
```

## 📊 Статусы и бейджи

Добавьте в README.md:

```markdown
![Deploy Status](https://github.com/DeviceIngineering/printfarm-production/actions/workflows/deploy.yml/badge.svg)
![Tests](https://github.com/DeviceIngineering/printfarm-production/actions/workflows/test.yml/badge.svg)
```

## 🔐 Безопасность

### Рекомендации:

1. **Используйте отдельный SSH ключ** только для деплоя
2. **Ограничьте права пользователя** на сервере
3. **Используйте Environment Protection** в GitHub
4. **Регулярно обновляйте секреты**
5. **Не коммитьте .env файлы**

### Ротация ключей:

```bash
# Генерация нового ключа
ssh-keygen -t ed25519 -f ~/.ssh/new_deploy_key -C "github-actions-deploy-new"

# Обновление на сервере
ssh printfarm@szboxz66
sed -i '/github-actions-deploy/d' ~/.ssh/authorized_keys
echo "НОВЫЙ_ПУБЛИЧНЫЙ_КЛЮЧ" >> ~/.ssh/authorized_keys

# Обновление в GitHub Secrets
# Settings → Secrets → SSH_PRIVATE_KEY → Update secret
```

## ✅ Чеклист настройки

- [ ] SSH ключи сгенерированы
- [ ] Публичный ключ добавлен на сервер
- [ ] GitHub Secrets настроены
- [ ] Environment создан
- [ ] Workflows добавлены в репозиторий
- [ ] Тестовый деплой выполнен успешно

## 📞 Поддержка

При возникновении проблем:

1. Проверьте логи в GitHub Actions
2. Проверьте логи на сервере
3. Используйте `quick_diagnosis.sh` на сервере
4. Создайте issue в репозитории

---

**Последнее обновление:** 2025-08-03
**Версия:** 1.0