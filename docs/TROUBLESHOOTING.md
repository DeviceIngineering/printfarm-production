# 🔧 Устранение неполадок PrintFarm

> Справочник по решению типичных проблем при локальной разработке

## 🖥️ Проблемы с React приложением

### ❌ Черный экран на http://localhost:3000

**Симптомы**: Страница загружается, но отображается черный экран без контента.

**Причины и решения**:

#### 1. Проблема с localStorage
```javascript
// Откройте консоль браузера (F12) и выполните:
localStorage.clear()
sessionStorage.clear()
// Затем обновите страницу (Ctrl+R)
```

#### 2. Автоматическая очистка через инструмент
- Откройте: `http://localhost:3000/clear-storage.html`
- Нажмите "Очистить все данные"
- Дождитесь автоматического перенаправления

#### 3. Проблема с состоянием React
```bash
# Остановите React сервер (Ctrl+C)
cd frontend
rm -rf node_modules/.cache
npm start
```

#### 4. Проверка в режиме инкогнито
- Откройте http://localhost:3000 в режиме инкогнито
- Если работает - проблема в кэше браузера

**Диагностика**:
1. Откройте DevTools (F12) → Console
2. Ищите красные ошибки JavaScript
3. Проверьте вкладку Network - загружаются ли файлы
4. Должны быть логи: "App component mounted", "Current token: ..."

### ❌ Приложение "зависает" после обновления страницы

**Решение**:
```bash
# Полный перезапуск
./restart-clean.sh

# Или вручную:
lsof -ti:3000 | xargs kill -9
lsof -ti:8000 | xargs kill -9
cd backend && python3 manage.py runserver 0.0.0.0:8000 &
cd frontend && npm start
```

### ❌ Ошибки компиляции React

**Симптомы**: Ошибки TypeScript или ESLint в консоли

**Решение**:
```bash
cd frontend
npm install  # переустановка зависимостей
```

**Игнорирование предупреждений**:
- Warnings про `useEffect dependencies` не критичны
- Warnings про deprecated Webpack middleware можно игнорировать

## 🔧 Проблемы с Django API

### ❌ Ошибка "Authentication required" для Excel экспорта

**Симптомы**: `{"detail": "Authentication required"}` при попытке экспорта

**Решение**: Проверить настройки development
```python
# В backend/config/settings/local_no_celery.py должно быть:
DEBUG = True
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [],
}
```

**Проверка**:
```bash
curl -I http://localhost:8000/api/v1/reports/export/products/
# Должен вернуть: HTTP/1.1 200 OK
```

### ❌ Django сервер не запускается

**Ошибка**: "That port is already in use"
```bash
# Найти и остановить процесс
lsof -ti:8000 | xargs kill -9
python3 manage.py runserver 0.0.0.0:8000
```

**Ошибка**: "No module named django"
```bash
# Переустановить зависимости
pip install -r backend/requirements.txt
```

**Ошибка**: "DJANGO_SETTINGS_MODULE not set"
```bash
# Проверить файл .env в корне проекта:
DJANGO_SETTINGS_MODULE=config.settings.local_no_celery
```

### ❌ Ошибки базы данных

**Ошибка**: "no such table"
```bash
cd backend
python3 manage.py migrate
```

**Ошибка**: "database is locked"
```bash
# Остановить все процессы Django
lsof -ti:8000 | xargs kill -9
# Удалить и пересоздать базу
rm db.sqlite3
python3 manage.py migrate
```

## 🌐 Проблемы с сетью и API

### ❌ CORS ошибки в браузере

**Симптомы**: "Access to fetch blocked by CORS policy"

**Решение**: Проверить настройки CORS
```python
# В settings должно быть:
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
```

### ❌ API запросы не проходят

**Диагностика**:
```bash
# Проверить Django API
curl http://localhost:8000/api/v1/

# Проверить настройки React
cat frontend/.env
# Должно быть: REACT_APP_API_URL=http://localhost:8000/api/v1
```

### ❌ МойСклад API недоступен

**Симптомы**: Ошибки синхронизации с МойСклад

**Проверка токена**:
```bash
cd backend
python3 test_sync_safe.py
```

**Ожидаемый результат**:
```
✅ Найдено складов: 6
✅ Токен валидный. Пользователь: ...
```

## 🔄 Проблемы синхронизации

### ❌ Синхронизация "зависает"

**Причина**: Celery не настроен

**Решение**: Убедиться что используется `local_no_celery` настройки
```bash
# В .env должно быть:
DJANGO_SETTINGS_MODULE=config.settings.local_no_celery
```

### ❌ Приложение падает при синхронизации

**Решение**: Проверить логи Django в консоли
```bash
# Запустить Django с подробными логами
cd backend
python3 manage.py runserver --verbosity=2
```

## 🛠️ Общие инструменты диагностики

### Автоматическая проверка системы
Откройте в браузере: `file:///.../status-check.html`

**Что проверяется**:
- Django API доступность
- React сервер статус  
- Размер экспортируемых файлов
- Настройки localStorage

### Принудительная очистка
```bash
# Очистка всех временных файлов
rm -rf frontend/node_modules/.cache
rm -rf frontend/build
rm backend/db.sqlite3

# Пересоздание окружения
cd backend
python3 manage.py migrate
cd ../frontend
npm start
```

### Проверка портов
```bash
# Какие порты заняты
lsof -i :3000
lsof -i :8000

# Освобождение портов
lsof -ti:3000 | xargs kill -9
lsof -ti:8000 | xargs kill -9
```

## 📋 Контрольный список

Если ничего не помогает, выполните полную переустановку:

- [ ] Остановить все процессы: `lsof -ti:3000,8000 | xargs kill -9`
- [ ] Проверить .env файлы в корне проекта и frontend/
- [ ] Переустановить Python зависимости: `pip install -r backend/requirements.txt`
- [ ] Переустановить Node зависимости: `cd frontend && npm install`
- [ ] Пересоздать базу: `rm backend/db.sqlite3 && python3 backend/manage.py migrate`
- [ ] Очистить браузер: localStorage.clear() в консоли
- [ ] Запустить сервера по очереди
- [ ] Проверить http://localhost:3000

## 🆘 Получение помощи

1. **Проверьте логи** в консоли Django и React
2. **Откройте DevTools** (F12) в браузере
3. **Используйте тестовые инструменты** из docs/
4. **Проверьте известные проблемы** в этом файле

---

**💡 Совет**: Большинство проблем решается полной очисткой кэша и перезапуском серверов.