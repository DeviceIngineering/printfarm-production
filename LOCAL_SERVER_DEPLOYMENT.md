# 🚀 Локальное развертывание PrintFarm v3.3.4 на сервере

## ✅ Вы уже на сервере szboxz66 в папке /opt/printfarm-production

Код успешно загружен из GitHub\! Теперь выполните следующие команды для развертывания:

---

## 📋 Команды для выполнения на сервере:

### 1. Проверьте что вы в правильной папке:
```bash
pwd
# Должно показать: /opt/printfarm-production

ls -la
# Должны увидеть файлы: docker-compose.server.prod.yml, .env.prod, quick-deploy.sh и др.
```

### 2. Проверьте установку Docker:
```bash
docker --version
docker-compose --version
```

### 3. Если Docker не установлен:
```bash
# Установить Docker
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER

# Установить Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Перелогиньтесь для применения группы docker
exit
# И зайдите снова: ssh -p 2131 printfarm@kemomail3.keenetic.pro
```

### 4. Локальное развертывание:
```bash
cd /opt/printfarm-production

# Остановить старые контейнеры (если есть)
docker-compose -f docker-compose.server.prod.yml down --remove-orphans 2>/dev/null || true

# Очистить старые образы
docker system prune -f 2>/dev/null || true

# Собрать новые образы
docker-compose -f docker-compose.server.prod.yml build --no-cache

# Запустить контейнеры
docker-compose -f docker-compose.server.prod.yml up -d

# Подождать запуска сервисов
echo "⏳ Ожидание запуска сервисов..."
sleep 30
```

### 5. Проверить развертывание:
```bash
# Статус контейнеров
docker-compose -f docker-compose.server.prod.yml ps

# Логи контейнеров
docker-compose -f docker-compose.server.prod.yml logs --tail=20

# Тест API
curl http://localhost:8001/api/v1/settings/system-info/

# Тест критической функции резерва (v3.3.4)
curl http://localhost:8001/api/v1/tochka/production/ | grep -c "reserved_stock" || echo "API еще запускается..."
```

---

## 🌐 После успешного развертывания:

### Доступ к системе:
- **🌐 Основное приложение**: http://192.168.1.98:8080
- **🔧 Backend API**: http://192.168.1.98:8001/api/v1/
- **⚛️ Frontend**: http://192.168.1.98:3001
- **📊 Системная информация**: http://192.168.1.98:8001/api/v1/settings/system-info/

---

## 🛠️ Команды управления:

```bash
cd /opt/printfarm-production

# Основные команды:
docker-compose -f docker-compose.server.prod.yml ps          # статус
docker-compose -f docker-compose.server.prod.yml logs        # логи
docker-compose -f docker-compose.server.prod.yml logs backend # логи backend
docker-compose -f docker-compose.server.prod.yml restart     # перезапуск
docker-compose -f docker-compose.server.prod.yml down        # остановить
docker-compose -f docker-compose.server.prod.yml up -d       # запустить

# Мониторинг:
docker stats                                                 # использование ресурсов
docker-compose -f docker-compose.server.prod.yml exec backend bash  # войти в контейнер backend
```

---

## 🔧 Устранение проблем:

### Если порты заняты:
```bash
# Проверьте какие порты используются
sudo ss -tlnp | grep -E ':8001|:3001|:8080|:5433|:6380'

# Остановите процессы или измените порты в docker-compose.server.prod.yml
```

### Проблемы с Docker:
```bash
# Полная очистка Docker
docker system prune -a
docker volume prune

# Перезапуск Docker службы
sudo systemctl restart docker
```

### Логи для диагностики:
```bash
# Логи всех сервисов
docker-compose -f docker-compose.server.prod.yml logs

# Логи конкретного сервиса
docker-compose -f docker-compose.server.prod.yml logs backend
docker-compose -f docker-compose.server.prod.yml logs frontend
docker-compose -f docker-compose.server.prod.yml logs db
```

---

## 📊 Мониторинг системы:

```bash
# Проверка здоровья системы
curl -s http://localhost:8001/api/v1/settings/system-info/ | python3 -m json.tool

# Проверка товаров с резервом
curl -s http://localhost:8001/api/v1/tochka/production/ | python3 -c "
import json, sys
data = json.load(sys.stdin)
reserve_count = len([p for p in data.get('results', []) if float(p.get('reserved_stock', 0)) > 0])
print(f'Товаров с резервом: {reserve_count}')
"

# Мониторинг использования ресурсов
htop  # или top
df -h # использование диска
free -h # использование памяти
```

