# 🚀 Развертывание PrintFarm v3.3.4 через Git

## ✅ Файлы успешно загружены в GitHub\!

**Repository**: https://github.com/DeviceIngineering/printfarm-production  
**Branch**: `hotfix/production-reserve-inclusion`

---

## 📋 Инструкции для развертывания на сервере:

### 1. Подключитесь к серверу:
```bash
ssh -p 2131 printfarm@kemomail3.keenetic.pro
# Пароль: 1qaz2wsX
```

### 2. Установите git (если не установлен):
```bash
sudo apt update
sudo apt install git -y
```

### 3. Установите Docker (если не установлен):
```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
# Выйдите и зайдите заново для применения изменений группы
```

### 4. Установите Docker Compose:
```bash
sudo curl -L "https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 5. Клонируйте репозиторий:
```bash
# Создайте папку для проекта
sudo mkdir -p /opt/printfarm-production
sudo chown -R $USER /opt/printfarm-production

# Клонируйте проект
cd /opt
git clone -b hotfix/production-reserve-inclusion https://github.com/DeviceIngineering/printfarm-production.git
cd printfarm-production

# Или если папка уже существует, обновите:
cd /opt/printfarm-production
git fetch origin
git checkout hotfix/production-reserve-inclusion
git pull origin hotfix/production-reserve-inclusion
```

### 6. Запустите развертывание:
```bash
# Убедитесь что вы в папке проекта
cd /opt/printfarm-production

# Запустите быстрое развертывание
chmod +x quick-deploy.sh
./quick-deploy.sh

# ИЛИ выполните развертывание вручную:
docker-compose -f docker-compose.server.prod.yml down --remove-orphans || true
docker system prune -f || true
docker-compose -f docker-compose.server.prod.yml build --no-cache
docker-compose -f docker-compose.server.prod.yml up -d
```

### 7. Проверьте развертывание:
```bash
# Статус контейнеров
docker-compose -f docker-compose.server.prod.yml ps

# Тест API
curl http://localhost:8001/api/v1/settings/system-info/

# Проверка резерва (критическая функция v3.3.4)
curl http://localhost:8001/api/v1/tochka/production/ | grep -c "reserved_stock" || echo "API еще запускается..."

# Логи (если что-то не работает)
docker-compose -f docker-compose.server.prod.yml logs
```

---

## 🌐 После успешного развертывания:

### Доступ к системе:
- **🌐 Основное приложение**: http://192.168.1.98:8080
- **🔧 Backend API**: http://192.168.1.98:8001/api/v1/
- **⚛️ Frontend**: http://192.168.1.98:3001
- **📊 Системная информация**: http://192.168.1.98:8001/api/v1/settings/system-info/

### Управление на сервере:
```bash
cd /opt/printfarm-production

# Основные команды Docker Compose:
docker-compose -f docker-compose.server.prod.yml ps        # статус
docker-compose -f docker-compose.server.prod.yml logs      # логи  
docker-compose -f docker-compose.server.prod.yml restart   # перезапуск
docker-compose -f docker-compose.server.prod.yml down      # остановить
docker-compose -f docker-compose.server.prod.yml up -d     # запустить
```

---

## 🔄 Обновление системы:

```bash
cd /opt/printfarm-production

# Получить последние изменения
git pull origin hotfix/production-reserve-inclusion

# Перезапустить с новым кодом
docker-compose -f docker-compose.server.prod.yml down
docker-compose -f docker-compose.server.prod.yml build --no-cache  
docker-compose -f docker-compose.server.prod.yml up -d
```

---

## 🛠️ Устранение проблем:

### Если git clone не работает из-за файрвола:
```bash
# Попробуйте HTTPS вместо SSH
git clone https://github.com/DeviceIngineering/printfarm-production.git

# Или скачайте архив
wget https://github.com/DeviceIngineering/printfarm-production/archive/refs/heads/hotfix/production-reserve-inclusion.zip
unzip production-reserve-inclusion.zip
mv printfarm-production-hotfix-production-reserve-inclusion/* /opt/printfarm-production/
```

### Если порты заняты:
```bash
# Проверьте какие порты заняты
sudo ss -tlnp | grep -E ':8001|:3001|:8080|:5433|:6380'

# Остановите процессы или измените порты в docker-compose.server.prod.yml
```

### Проблемы с Docker:
```bash
# Перезапустите Docker
sudo systemctl restart docker

# Очистите все
docker system prune -a
docker volume prune
```

---

**🎉 PrintFarm v3.3.4 готов к развертыванию через Git\!**

Все файлы находятся в GitHub репозитории и готовы для клонирования на сервер.

