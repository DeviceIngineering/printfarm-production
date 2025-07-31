# 🛠️ Настройка локальной разработки PrintFarm

> **Внимание**: Эта инструкция описывает запуск проекта **без Docker** для локальной разработки и тестирования.

## 📋 Предварительные требования

- **Python 3.11+** установлен в системе
- **Node.js 16+** и npm установлены
- **Git** для клонирования репозитория

## 🚀 Быстрый старт

### 1. Клонирование проекта
```bash
git clone https://github.com/DeviceIngineering/printfarm-production.git
cd printfarm-production
```

### 2. Настройка Backend (Django)

#### 2.1 Создание виртуального окружения
```bash
python3 -m venv venv
# Активация не требуется - будем использовать напрямую
```

#### 2.2 Установка зависимостей
```bash
# Установка Python зависимостей (глобально для простоты)
pip install -r backend/requirements.txt
```

#### 2.3 Настройка переменных окружения
Создайте файл `.env` в корне проекта:
```bash
cat > .env << 'EOF'
# Django
SECRET_KEY=dev-secret-key-for-local-development
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database - используем SQLite для локальной разработки
DATABASE_URL=sqlite:///db.sqlite3

# Redis - отключен для локальной разработки
REDIS_URL=redis://localhost:6379/0

# МойСклад
MOYSKLAD_TOKEN=f9be4985f5e3488716c040ca52b8e04c7c0f9e0b
MOYSKLAD_DEFAULT_WAREHOUSE=241ed919-a631-11ee-0a80-07a9000bb947

# Celery - отключен для локальной разработки
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Дополнительные настройки для локальной разработки
DJANGO_SETTINGS_MODULE=config.settings.local_no_celery
EOF
```

#### 2.4 Выполнение миграций
```bash
cd backend
python3 manage.py migrate
```

#### 2.5 Создание суперпользователя (опционально)
```bash
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@example.com', 'admin123')" | python3 manage.py shell
```

### 3. Настройка Frontend (React)

#### 3.1 Создание .env файла для React
```bash
cd ../frontend
cat > .env << 'EOF'
REACT_APP_API_URL=http://localhost:8000/api/v1
REACT_APP_MEDIA_URL=http://localhost:8000/media/
EOF
```

#### 3.2 Установка зависимостей
```bash
npm install
```

### 4. Запуск приложения

#### 4.1 Запуск Django (в одном терминале)
```bash
cd backend
python3 manage.py runserver 0.0.0.0:8000
```

#### 4.2 Запуск React (в другом терминале)
```bash
cd frontend
npm start
```

## 🌐 Доступ к приложению

После успешного запуска:

- **Frontend (основное приложение)**: http://localhost:3000
- **Django API**: http://localhost:8000/api/v1/
- **Django Admin**: http://localhost:8000/admin/ (admin/admin123)

## ⚙️ Особенности локальной конфигурации

### Отключенные сервисы
- **Redis**: заменен на локальный кэш в памяти
- **Celery**: задачи выполняются синхронно  
- **PostgreSQL**: заменен на SQLite
- **Аутентификация**: отключена для разработки

### Созданные файлы конфигурации
- `backend/config/settings/local_no_celery.py` - настройки без Celery
- `frontend/.env` - переменные окружения React
- `.env` - основные переменные проекта

## 🔧 Вспомогательные инструменты

### Скрипт быстрого запуска
```bash
./run-local-dev.sh
```

### Скрипт полного перезапуска
```bash
./restart-clean.sh
```

### Тестовые страницы
- **Проверка статуса**: `file:///.../status-check.html`
- **Тест экспорта**: `file:///.../test-export.html`
- **Очистка localStorage**: `http://localhost:3000/clear-storage.html`

## 🐛 Известные проблемы

См. [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) для решения типичных проблем.

## 📝 Примечания

1. **Данные**: Используется SQLite база данных `backend/db.sqlite3`
2. **Медиа файлы**: Сохраняются в `backend/media/`
3. **Логи**: Выводятся в консоль с уровнем DEBUG
4. **Безопасность**: Настройки оптимизированы для разработки, НЕ для production

## 🔄 Обновление проекта

```bash
git pull origin main
pip install -r backend/requirements.txt  # обновление Python зависимостей
cd frontend && npm install              # обновление Node.js зависимостей
cd ../backend && python3 manage.py migrate  # применение новых миграций
```

---

**⚠️ Важно**: Эта конфигурация предназначена только для локальной разработки. Для production используйте Docker конфигурацию из основного README.md.