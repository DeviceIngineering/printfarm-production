# 🛠️ Вспомогательные инструменты PrintFarm

> Документация по всем созданным инструментам для локальной разработки и диагностики

## 📋 Обзор инструментов

| Инструмент | Назначение | Путь |
|-----------|------------|------|
| **run-local-dev.sh** | Быстрый запуск | `./run-local-dev.sh` |
| **restart-clean.sh** | Полный перезапуск | `./restart-clean.sh` |
| **status-check.html** | Диагностика системы | `file:///.../status-check.html` |
| **test-export.html** | Тест экспорта Excel | `file:///.../test-export.html` |
| **clear-storage.html** | Очистка localStorage | `http://localhost:3000/clear-storage.html` |
| **test_sync_safe.py** | Тест МойСклад API | `python backend/test_sync_safe.py` |

## 🚀 Скрипты запуска

### 1. run-local-dev.sh
**Назначение**: Одновременный запуск Django и React серверов

**Использование**:
```bash
chmod +x run-local-dev.sh
./run-local-dev.sh
```

**Что делает**:
1. Проверяет существование `.env` файла
2. Останавливает запущенные процессы на портах 8000 и 3000
3. Запускает Django сервер в фоне
4. Запускает React приложение в фоне
5. Отображает статус и URL для доступа
6. Ожидает Ctrl+C для остановки

**Вывод**:
```
=== Приложение запущено! ===

📍 Frontend: http://localhost:3000
📍 Backend API: http://localhost:8000/api/v1/
📍 Django Admin: http://localhost:8000/admin/

Для остановки нажмите Ctrl+C
```

### 2. restart-clean.sh
**Назначение**: Полная очистка и перезапуск системы

**Использование**:
```bash
chmod +x restart-clean.sh
./restart-clean.sh
```

**Что делает**:
1. Просит очистить localStorage в браузере
2. Останавливает все процессы на портах 8000/3000
3. Очищает кэш Node.js
4. Перезапускает Django и React
5. Предоставляет инструкции по устранению проблем

**Особенности**:
- Интерактивный (требует подтверждения)
- Выводит подробные инструкции
- Включает советы по диагностике

## 🧪 Диагностические инструменты

### 1. status-check.html
**Назначение**: Автоматическая проверка работоспособности системы

**Открытие**: Откройте файл в браузере напрямую
```
file:///Users/ваш_путь/printfarm-production/status-check.html
```

**Функции**:
- ✅ **Проверить Django API** - тестирует `/api/v1/` endpoint
- ✅ **Проверить React** - проверяет доступность порта 3000
- ✅ **Очистить localStorage** - автоматическая очистка браузера
- ✅ **Открыть приложение** - переход на главную страницу
- ✅ **Полная проверка** - запуск всех тестов

**Результаты**:
```
✅ Django API работает
Ответ: {"message": "PrintFarm API v1.0"}

✅ React сервер отвечает
📄 Content-Type: text/html

✅ Очищено 3 записей из localStorage
```

### 2. test-export.html
**Назначение**: Тестирование функций экспорта Excel

**Открытие**: 
```
file:///Users/ваш_путь/printfarm-production/test-export.html
```

**Функции**:
- 📊 **Экспорт всех товаров** - скачивает Excel со всеми товарами
- 📋 **Экспорт списка производства** - только товары для производства
- 🔍 **Проверить API экспорта** - тестирует endpoints без скачивания

**Что тестируется**:
```
✅ API экспорта работает
📄 Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
📏 Размер файла: 63 KB
✅ Правильный формат Excel файла
```

**Автоматическое скачивание**:
- Файлы сохраняются с именами `printfarm_products_YYYY-MM-DD.xlsx`
- Проверяется корректность MIME-типов
- Отображается размер файла

### 3. clear-storage.html
**Назначение**: Решение проблемы "черного экрана" React

**Открытие**: 
```
http://localhost:3000/clear-storage.html
```

**Автоматическая очистка**:
```
http://localhost:3000/clear-storage.html?auto=true
```

**Что очищает**:
- ✅ localStorage
- ✅ sessionStorage  
- ✅ IndexedDB базы данных
- ✅ Cookies для домена

**Интерфейс**:
```
🧹 Очистка PrintFarm Storage
[Очистить все данные] [Открыть приложение]

✅ Все данные очищены!
📍 localStorage: очищен
📍 sessionStorage: очищен
📍 Cookies: очищены
📍 IndexedDB: очищен
```

## 🔧 Серверные инструменты

### 1. test_sync_safe.py
**Назначение**: Безопасное тестирование подключения к МойСклад

**Использование**:
```bash
cd backend
python test_sync_safe.py
```

**Что проверяет**:
- Подключение к МойСклад API
- Валидность токена
- Доступность складов
- Корректность настроек

**Пример вывода**:
```
=== Тест подключения к МойСклад ===

1. Получение списка складов...
✅ Найдено складов: 6
   1. Адресный склад (ID: 241ed919...)
   2. WB-ИП виртуальный (ID: 251f4b7f...)

2. Проверка токена...
✅ Токен валидный. Пользователь: PrintFarm User

✅ Тест подключения прошел успешно!
```

## 📁 Файлы конфигурации

### Автогенерируемые файлы
Инструменты создают следующие файлы:

| Файл | Создается | Назначение |
|------|-----------|------------|
| `.env` | run-local-dev.sh | Переменные Django |
| `frontend/.env` | DEVELOPMENT_SETUP.md | Переменные React |
| `backend/db.sqlite3` | migrate | База данных SQLite |

### Временные файлы
Инструменты могут создавать временные файлы:

- `node_modules/.cache/` - кэш Webpack (очищается restart-clean.sh)
- `frontend/build/` - сборка React (не используется в dev)
- Логи в консоли (не сохраняются в файлы)

## 🔄 Интеграция с основным проектом

### Запуск через npm scripts
Можно добавить в `package.json`:
```json
{
  "scripts": {
    "dev": "./run-local-dev.sh",
    "dev:clean": "./restart-clean.sh",
    "test:status": "open status-check.html",
    "test:export": "open test-export.html"
  }
}
```

### Интеграция с IDE
Инструменты можно вызывать из:
- **VS Code**: Tasks и Launch configurations
- **PyCharm**: External Tools
- **Терминал**: Прямой вызов скриптов

## 🔍 Диагностика проблем инструментов

### Права доступа
```bash
# Если скрипты не запускаются
chmod +x run-local-dev.sh restart-clean.sh
```

### Порты заняты
```bash
# Проверка занятых портов
lsof -i :3000 :8000

# Принудительное освобождение
lsof -ti:3000,8000 | xargs kill -9
```

### Браузер блокирует file://
Если `status-check.html` не работает:
- Используйте Firefox (меньше ограничений)
- Запустите локальный HTTP сервер:
  ```bash
  python -m http.server 8080
  # Откройте http://localhost:8080/status-check.html
  ```

### CORS ошибки
Если тестовые HTML файлы не могут обращаться к API:
- Проверьте настройки CORS в Django
- Используйте браузерные расширения для отключения CORS
- Запустите браузер с отключенной безопасностью (только для тестов!)

## 📝 Логирование инструментов

### Серверные логи
```bash
# Django с подробностями
python manage.py runserver --verbosity=2

# React с отладкой
DEBUG=true npm start
```

### Браузерные логи
Все HTML инструменты выводят логи в консоль браузера (F12):
```javascript
console.log('API Request:', method, url);
console.log('API Response:', data);
console.error('API Error:', error);
```

## 🎯 Рекомендации по использованию

### Ежедневная разработка
1. **Запуск**: `./run-local-dev.sh`
2. **При проблемах**: Откройте `status-check.html`
3. **Черный экран**: Откройте `clear-storage.html`

### Тестирование новых функций
1. **Экспорт**: Используйте `test-export.html`
2. **API**: Проверяйте через `status-check.html`
3. **МойСклад**: Запускайте `test_sync_safe.py`

### Устранение проблем
1. **Полная перезагрузка**: `./restart-clean.sh`
2. **Диагностика**: `status-check.html` → "Полная проверка"
3. **Очистка браузера**: `clear-storage.html?auto=true`

---

**💡 Совет**: Добавьте инструменты в закладки браузера для быстрого доступа!