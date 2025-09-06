# 🚀 PrintFarm v4.1.8 - Настройка автозапуска

## 📋 Описание

Система автоматического запуска PrintFarm обеспечивает:
- ✅ Автоматический запуск при загрузке системы
- ✅ Восстановление после сбоев
- ✅ Управление через systemctl
- ✅ Централизованное логирование
- ✅ Мониторинг состояния сервисов

## 🛠️ Быстрая установка на удаленном сервере

### 1. Подключитесь к серверу и установите автозапуск:

```bash
# На локальной машине - установка на удаленный сервер
cd /Users/dim11/Documents/myProjects/Factory_v3
chmod +x scripts/autostart/install-autostart.sh
./scripts/autostart/install-autostart.sh install-remote
```

### 2. Запустите сервис:

```bash
./scripts/autostart/install-autostart.sh start-remote
```

### 3. Проверьте статус:

```bash
./scripts/autostart/install-autostart.sh status-remote
```

### 4. Протестируйте автозапуск:

```bash
./scripts/autostart/install-autostart.sh test-remote
```

## 📁 Структура файлов

```
scripts/autostart/
├── start-printfarm.sh      # Основной скрипт запуска
├── printfarm.service        # Systemd сервис файл
└── install-autostart.sh    # Установщик автозапуска
```

## 🔧 Ручная установка на сервере

Если автоматическая установка не работает, выполните эти команды вручную на сервере:

### 1. Подключитесь к серверу:

```bash
ssh -p 2132 printfarm@kemomail3.keenetic.pro
```

### 2. Создайте директорию для скриптов:

```bash
mkdir -p /home/printfarm/printfarm-test/scripts
```

### 3. Создайте скрипт запуска:

```bash
nano /home/printfarm/printfarm-test/scripts/start-printfarm.sh
# Скопируйте содержимое из scripts/autostart/start-printfarm.sh
chmod +x /home/printfarm/printfarm-test/scripts/start-printfarm.sh
```

### 4. Создайте systemd сервис:

```bash
sudo nano /etc/systemd/system/printfarm.service
# Скопируйте содержимое из scripts/autostart/printfarm.service
```

### 5. Активируйте автозапуск:

```bash
# Перезагрузите systemd
sudo systemctl daemon-reload

# Включите автозапуск
sudo systemctl enable printfarm.service

# Запустите сервис
sudo systemctl start printfarm.service

# Проверьте статус
sudo systemctl status printfarm.service
```

## 📊 Управление сервисом

### Основные команды:

```bash
# Запуск
sudo systemctl start printfarm

# Остановка
sudo systemctl stop printfarm

# Перезапуск
sudo systemctl restart printfarm

# Статус
sudo systemctl status printfarm

# Логи
sudo journalctl -u printfarm -f

# Отключить автозапуск
sudo systemctl disable printfarm

# Включить автозапуск
sudo systemctl enable printfarm
```

### Управление через установщик:

```bash
# Запуск на удаленном сервере
./scripts/autostart/install-autostart.sh start-remote

# Остановка на удаленном сервере
./scripts/autostart/install-autostart.sh stop-remote

# Перезапуск на удаленном сервере
./scripts/autostart/install-autostart.sh restart-remote

# Статус на удаленном сервере
./scripts/autostart/install-autostart.sh status-remote

# Логи на удаленном сервере
./scripts/autostart/install-autostart.sh logs-remote
```

## 📝 Логирование

Логи сохраняются в следующих местах:

- **Системные логи**: `/var/log/syslog` или `journalctl -u printfarm`
- **Логи приложения**: `/home/printfarm/printfarm-test/logs/`
  - `startup.log` - логи запуска
  - `systemd.log` - вывод сервиса
  - `systemd-error.log` - ошибки сервиса

### Просмотр логов:

```bash
# Последние 100 строк логов сервиса
sudo journalctl -u printfarm -n 100

# Следить за логами в реальном времени
sudo journalctl -u printfarm -f

# Логи за последний час
sudo journalctl -u printfarm --since "1 hour ago"

# Логи приложения
tail -f /home/printfarm/printfarm-test/logs/startup.log
```

## 🔍 Диагностика проблем

### Если сервис не запускается:

1. **Проверьте статус**:
```bash
sudo systemctl status printfarm
```

2. **Проверьте логи ошибок**:
```bash
sudo journalctl -u printfarm -n 50 --no-pager
```

3. **Проверьте Docker**:
```bash
sudo systemctl status docker
docker ps -a
```

4. **Проверьте порты**:
```bash
sudo ss -tlnp | grep -E "15432|16379|18000|13000"
```

5. **Запустите вручную для отладки**:
```bash
/home/printfarm/printfarm-test/scripts/start-printfarm.sh start
```

### Частые проблемы и решения:

| Проблема | Решение |
|----------|---------|
| Docker не запущен | `sudo systemctl start docker` |
| Порт занят | Найти процесс: `sudo lsof -i :PORT` и остановить |
| Нет прав на файлы | `sudo chown -R printfarm:printfarm /home/printfarm/printfarm-test` |
| База данных не готова | Подождать или перезапустить: `sudo systemctl restart printfarm` |

## 🔄 Обновление системы

При обновлении PrintFarm:

1. **Остановите сервис**:
```bash
sudo systemctl stop printfarm
```

2. **Обновите код**:
```bash
cd /home/printfarm/printfarm-test
git pull origin main  # или используйте rsync
```

3. **Обновите зависимости**:
```bash
docker-compose build --no-cache
```

4. **Запустите сервис**:
```bash
sudo systemctl start printfarm
```

## 🧪 Тестирование автозапуска

### Проверка после установки:

```bash
# 1. Перезагрузите сервер
sudo reboot

# 2. После перезагрузки (подождите 2-3 минуты)
ssh -p 2132 printfarm@kemomail3.keenetic.pro

# 3. Проверьте статус
sudo systemctl status printfarm

# 4. Проверьте доступность
curl http://localhost:13000/api/v1/health/
```

### Проверка восстановления после сбоя:

```bash
# 1. Имитируйте сбой
sudo systemctl kill printfarm

# 2. Подождите 30 секунд

# 3. Проверьте, что сервис перезапустился
sudo systemctl status printfarm
```

## 📊 Мониторинг

### Скрипт проверки здоровья:

```bash
#!/bin/bash
# health-check.sh

check_service() {
    if curl -f http://localhost:13000/api/v1/health/ &>/dev/null; then
        echo "✅ API: Healthy"
    else
        echo "❌ API: Not responding"
    fi
    
    if curl -f http://localhost:13000/ &>/dev/null; then
        echo "✅ Frontend: Healthy"
    else
        echo "❌ Frontend: Not responding"
    fi
    
    if docker ps | grep -q printfarm; then
        echo "✅ Containers: Running"
    else
        echo "❌ Containers: Not running"
    fi
}

check_service
```

## 🗑️ Удаление автозапуска

Если нужно удалить автозапуск:

```bash
# С локальной машины
./scripts/autostart/install-autostart.sh uninstall-remote

# Или вручную на сервере
sudo systemctl stop printfarm
sudo systemctl disable printfarm
sudo rm /etc/systemd/system/printfarm.service
sudo systemctl daemon-reload
```

## 📞 Поддержка

При возникновении проблем:

1. Проверьте логи: `sudo journalctl -u printfarm -n 100`
2. Проверьте статус Docker: `docker ps -a`
3. Проверьте сетевые соединения: `sudo ss -tlnp`
4. Проверьте дисковое пространство: `df -h`

## ✅ Контрольный список

После установки автозапуска убедитесь что:

- [ ] Сервис включен: `systemctl is-enabled printfarm`
- [ ] Сервис запущен: `systemctl is-active printfarm`
- [ ] API доступен: `curl http://localhost:13000/api/v1/health/`
- [ ] Frontend доступен: `curl http://localhost:13000/`
- [ ] Внешний доступ работает: `curl http://kemomail3.keenetic.pro:13000/`
- [ ] Логи пишутся: `ls -la /home/printfarm/printfarm-test/logs/`
- [ ] Автозапуск работает после перезагрузки

---

**Версия**: 4.1.8  
**Дата обновления**: 2025-09-05