# 🚀 PrintFarm v3.3.4 - Готово к развертыванию\!

## ✅ Что готово:

1. **✅ Скрипты развертывания**:
   - `deploy-interactive.sh` - интерактивное развертывание
   - `deploy-printfarm-server.sh` - автоматическое развертывание  
   - `test-deployment.sh` - тестирование

2. **✅ Конфигурация**:
   - `docker-compose.server.prod.yml` - production compose
   - `.env.prod` - настроен для вашего сервера (192.168.1.98)
   - Порты изменены: 8001, 3001, 8080, 5433, 6380

3. **✅ Настройки сервера**:
   - Хост: kemomail3.keenetic.pro:2131
   - Пользователь: printfarm  
   - Пароль: 1qaz2wsX
   - IP: 192.168.1.98

## 🚀 Быстрое развертывание:

### Вариант 1: Автоматический (рекомендуется)
```bash
./deploy-interactive.sh
# Введите 'y' когда спросит
# Введите пароль: 1qaz2wsX когда потребуется
```

### Вариант 2: Пошаговый

1. **Загрузить файлы на сервер:**
```bash
# Создастся скрипт upload-files.sh
./deploy-interactive.sh
# Выберите 'y' для загрузки файлов
```

2. **Подключиться к серверу:**
```bash
ssh -p 2131 printfarm@kemomail3.keenetic.pro
# Пароль: 1qaz2wsX
```

3. **На сервере выполнить:**
```bash
cd /opt/printfarm-production
bash server-deploy.sh
```

### Вариант 3: Полностью ручной

1. **Подключиться к серверу:**
```bash
ssh -p 2131 printfarm@kemomail3.keenetic.pro
```

2. **Установить Docker (если нет):**
```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
# Перелогиниться
```

3. **Установить Docker Compose:**
```bash
sudo curl -L "https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

4. **Создать папку проекта:**
```bash
sudo mkdir -p /opt/printfarm-production
sudo chown -R $USER /opt/printfarm-production
cd /opt/printfarm-production
```

5. **Загрузить файлы с локальной машины:**
```bash
# На локальной машине выполнить:
scp -P 2131 docker-compose.server.prod.yml printfarm@kemomail3.keenetic.pro:/opt/printfarm-production/
scp -P 2131 .env.prod printfarm@kemomail3.keenetic.pro:/opt/printfarm-production/
scp -P 2131 VERSION printfarm@kemomail3.keenetic.pro:/opt/printfarm-production/
scp -rP 2131 backend/ printfarm@kemomail3.keenetic.pro:/opt/printfarm-production/
scp -rP 2131 frontend/ printfarm@kemomail3.keenetic.pro:/opt/printfarm-production/
scp -rP 2131 docker/ printfarm@kemomail3.keenetic.pro:/opt/printfarm-production/
```

6. **На сервере запустить:**
```bash
cd /opt/printfarm-production
docker-compose -f docker-compose.server.prod.yml up -d --build
```

7. **Проверить развертывание:**
```bash
docker-compose -f docker-compose.server.prod.yml ps
curl http://localhost:8001/api/v1/settings/system-info/
```

## 🌐 После развертывания доступ по URL:

- **🌐 Главное приложение**: http://192.168.1.98:8080
- **🔧 Backend API**: http://192.168.1.98:8001/api/v1/
- **⚛️ Frontend**: http://192.168.1.98:3001
- **📊 Системная информация**: http://192.168.1.98:8001/api/v1/settings/system-info/

## 🧪 Тестирование:

```bash
# На локальной машине:
./test-deployment.sh printfarm@kemomail3.keenetic.pro
# Или прямой URL тест:
curl http://192.168.1.98:8001/api/v1/settings/system-info/
```

## 🔧 Управление на сервере:

```bash
# SSH подключение
ssh -p 2131 printfarm@kemomail3.keenetic.pro

# Команды в папке проекта /opt/printfarm-production:
docker-compose -f docker-compose.server.prod.yml ps          # статус
docker-compose -f docker-compose.server.prod.yml logs        # логи
docker-compose -f docker-compose.server.prod.yml restart     # перезапуск
docker-compose -f docker-compose.server.prod.yml down        # остановить
docker-compose -f docker-compose.server.prod.yml up -d       # запустить
```

## 🎯 Критическая проверка v3.3.4:

```bash
# Проверить функцию резерва
curl http://192.168.1.98:8001/api/v1/tochka/production/ | grep -c "reserved_stock"
# Должно вернуть > 0
```

---

**🎉 PrintFarm v3.3.4 готов к развертыванию\!** 

Система включает критическое исправление Reserve Stock Integration для корректной работы с 146+ товарами с резервом.

