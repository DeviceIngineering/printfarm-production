# 🚀 PrintFarm Production v4.6 - Быстрый старт

**Развертывание за 5 минут на Ubuntu Server**

## 📋 Что вам нужно

1. **VPS сервер** с Ubuntu 20.04/22.04 LTS
   - Минимум: 2GB RAM, 2 CPU, 20GB диск
   - Рекомендуется: 4GB RAM, 2 CPU, 50GB диск

2. **Доступ по SSH** к серверу
   - IP-адрес или доменное имя
   - Логин и пароль root

## 🏃‍♂️ Быстрая установка (5 команд)

### Шаг 1: Подключитесь к серверу
```bash
ssh root@ваш-ip-адрес
# Введите пароль
```

### Шаг 2: Создайте пользователя (безопасность)
```bash
apt update && apt upgrade -y
adduser printfarm
usermod -aG sudo printfarm
su - printfarm
```

### Шаг 3: Скачайте и запустите установщик
```bash
wget https://raw.githubusercontent.com/DeviceIngineering/printfarm-production/main/deploy/install.sh
chmod +x install.sh
./install.sh
```

### Шаг 4: Следуйте инструкциям установщика
Введите когда спросят:
- **Database Password**: придумайте надежный пароль
- **Allowed Hosts**: ваш IP или домен (например: `192.168.1.100` или `mydomain.com`)
- **MoySklad Token**: `f9be4985f5e3488716c040ca52b8e04c7c0f9e0b` (или ваш)
- **Warehouse ID**: `241ed919-a631-11ee-0a80-07a9000bb947` (или ваш)

### Шаг 5: Создайте администратора
Когда установщик попросит, создайте суперпользователя:
- **Логин**: admin (или любой другой)
- **Email**: ваш email
- **Пароль**: надежный пароль

## ✅ Готово!

Откройте в браузере: `http://ваш-ip-адрес`

---

## 🛠️ Управление системой

### Основные команды
```bash
cd /home/printfarm/printfarm-production

# Проверить статус
docker-compose -f docker-compose.prod.yml ps

# Посмотреть логи
docker-compose -f docker-compose.prod.yml logs

# Перезапустить
docker-compose -f docker-compose.prod.yml restart

# Остановить
docker-compose -f docker-compose.prod.yml down

# Запустить
docker-compose -f docker-compose.prod.yml up -d
```

### Обновление
```bash
cd /home/printfarm/printfarm-production
./deploy/update.sh
```

### Резервное копирование
```bash
cd /home/printfarm/printfarm-production
./deploy/backup.sh
```

---

## 🆘 Нужна помощь?

### Проблема: Сайт не открывается
```bash
# Проверьте контейнеры
docker-compose -f docker-compose.prod.yml ps

# Если не запущены:
docker-compose -f docker-compose.prod.yml up -d
```

### Проблема: Ошибки в работе
```bash
# Создайте отчет о проблеме
./deploy/diagnostics.sh > problem_report.txt
# Отправьте файл разработчикам
```

### Получить помощь
- **GitHub**: https://github.com/DeviceIngineering/printfarm-production/issues
- **Email**: support@printfarm.com

---

## 📱 Возможности PrintFarm v4.6

✅ **Загрузка Excel файлов** - автоматическая обработка и дедупликация  
✅ **Анализ товаров** - сопоставление с базой МойСклад  
✅ **Списки производства** - автоматическое планирование  
✅ **Экспорт в Excel** - стилизованные отчеты для печати  
✅ **Веб-интерфейс** - удобная работа через браузер  

---

*PrintFarm Production v4.6 - Готов к работе!* 🎉