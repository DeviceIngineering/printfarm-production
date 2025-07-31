# ⚙️ Изменения конфигурации для локальной разработки

> Подробное описание всех изменений, внесенных для обеспечения работы проекта без Docker

## 📁 Структура новых файлов

```
printfarm-production/
├── .env                                    # ✨ НОВЫЙ - переменные окружения
├── backend/config/settings/
│   └── local_no_celery.py                 # ✨ НОВЫЙ - настройки без Celery
├── frontend/.env                          # ✨ НОВЫЙ - настройки React
├── frontend/src/components/common/
│   └── DebugInfo.tsx                      # ✨ НОВЫЙ - отладочная информация
├── docs/                                  # ✨ НОВАЯ ПАПКА
│   ├── DEVELOPMENT_SETUP.md               # ✨ НОВЫЙ - инструкция
│   ├── TROUBLESHOOTING.md                 # ✨ НОВЫЙ - решение проблем
│   └── CONFIGURATION_CHANGES.md           # ✨ НОВЫЙ - этот файл
├── run-local-dev.sh                       # ✨ НОВЫЙ - скрипт запуска
├── restart-clean.sh                       # ✨ НОВЫЙ - скрипт перезапуска
├── status-check.html                      # ✨ НОВЫЙ - диагностика
├── test-export.html                       # ✨ НОВЫЙ - тест экспорта
└── frontend/public/clear-storage.html     # ✨ НОВЫЙ - очистка localStorage
```

## 🔧 Изменения в существующих файлах

### 1. `backend/config/settings/development.py` (изменен)
**Что изменено**: Отключена аутентификация для разработки
```python
# БЫЛО (в base.py):
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
}

# СТАЛО:
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',  # ← Разрешаем всем
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        # ← Отключаем аутентификацию
    ],
}
```

### 2. `backend/apps/reports/export_views.py` (изменен)
**Что изменено**: Отключена аутентификация для экспорта Excel в development
```python
def authenticate_from_query(request):
    # ДОБАВЛЕНО:
    from django.conf import settings
    
    # В development режиме отключаем аутентификацию
    if settings.DEBUG:
        return True  # ← Всегда разрешаем в development
    
    # Остальной код без изменений...
```

### 3. `frontend/src/App.tsx` (изменен)
**Что изменено**: Добавлены отладочные логи и DebugInfo компонент
```tsx
// ДОБАВЛЕНО:
import { DebugInfo } from './components/common/DebugInfo';

function App() {
  useEffect(() => {
    console.log('App component mounted');        // ← Новый лог
    console.log('Current token:', token);        // ← Новый лог
    // ...остальной код
  }, []);

  return (
    <ErrorBoundary>
      {/* существующий код */}
      <DebugInfo />  {/* ← Новый компонент */}
    </ErrorBoundary>
  );
}
```

### 4. `frontend/src/api/client.ts` (изменен)
**Что изменено**: Отключена аутентификация и добавлено логирование
```typescript
// Request interceptor - ИЗМЕНЕН
apiClient.interceptors.request.use(
  (config) => {
    // ВРЕМЕННО ОТКЛЮЧЕНО для локальной разработки
    // const token = localStorage.getItem('auth_token');
    // if (token) {
    //   config.headers.Authorization = `Token ${token}`;
    // }
    console.log('API Request:', config.method?.toUpperCase(), config.url); // ← Новый лог
    return config;
  },
  // ...
);

// Response interceptor - ИЗМЕНЕН
apiClient.interceptors.response.use(
  (response) => {
    console.log('API Response:', response.config.url, response.data); // ← Новый лог
    return response.data;
  },
  (error) => {
    console.error('API Error:', error.response?.status, error.response?.data || error.message); // ← Новый лог
    // ВРЕМЕННО ОТКЛЮЧЕНО автоматическое перенаправление на login
    return Promise.reject(error);
  }
);
```

### 5. `README.md` (изменен)
**Что изменено**: Добавлены ссылки на новую документацию
```markdown
- ✅ Экспорт данных в Excel          ← Обновлен статус
- ✅ Веб-интерфейс React            ← Обновлен статус

## 🚀 Быстрый старт

> **Выберите способ запуска:**        ← Новая секция
> - **🐳 Docker** (рекомендуется для production) - см. ниже
> - **💻 Локальная разработка** - см. [docs/DEVELOPMENT_SETUP.md](docs/DEVELOPMENT_SETUP.md)

## 📚 Документация                   ← Новая секция
```

## 📄 Новые файлы конфигурации

### 1. `.env` (корень проекта)
```env
# Django
SECRET_KEY=dev-secret-key-for-local-development
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database - для локальной разработки используем SQLite
DATABASE_URL=sqlite:///db.sqlite3

# Настройки для development
DJANGO_SETTINGS_MODULE=config.settings.local_no_celery
```

**Назначение**: Основные переменные окружения для локальной разработки без Docker

### 2. `backend/config/settings/local_no_celery.py`
```python
from .development import *

# Отключаем Celery для локальной разработки
CELERY_TASK_ALWAYS_EAGER = True  # Выполнять задачи синхронно
CELERY_TASK_EAGER_PROPAGATES = True  # Пробрасывать исключения

# ПРИНУДИТЕЛЬНО отключаем аутентификацию для ВСЕХ endpoints
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [],
}

# Используем локальный кэш вместо Redis
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}
```

**Назначение**: Специальные настройки Django для разработки без внешних зависимостей

### 3. `frontend/.env`
```env
REACT_APP_API_URL=http://localhost:8000/api/v1
REACT_APP_MEDIA_URL=http://localhost:8000/media/
```

**Назначение**: Переменные окружения для React приложения

### 4. `frontend/src/components/common/DebugInfo.tsx`
```tsx
export const DebugInfo: React.FC = () => {
  const [debugData, setDebugData] = useState<any>({});

  useEffect(() => {
    const data = {
      token: localStorage.getItem('auth_token'),
      apiUrl: process.env.REACT_APP_API_URL || 'NOT SET',
      // ... другие данные для отладки
    };
    setDebugData(data);
    console.log('Debug Info:', data);
  }, []);

  // Отображается только в development
  if (process.env.NODE_ENV !== 'development') {
    return null;
  }

  return (
    <Alert /* отладочная информация в правом нижнем углу */ />
  );
};
```

**Назначение**: Компонент для отображения отладочной информации в development режиме

## 🚀 Скрипты автоматизации

### 1. `run-local-dev.sh`
```bash
#!/bin/bash
echo "=== Запуск PrintFarm в режиме локальной разработки ==="

# Запуск Django в фоне
cd backend
python manage.py runserver 0.0.0.0:8000 &
DJANGO_PID=$!

# Запуск React в фоне
cd ../frontend
npm start &
REACT_PID=$!

# Ожидание сигнала остановки
trap "kill $DJANGO_PID $REACT_PID; exit" INT
while true; do sleep 1; done
```

**Назначение**: Одновременный запуск Django и React серверов

### 2. `restart-clean.sh`
```bash
#!/bin/bash
echo "=== Полный перезапуск PrintFarm ==="

# Остановка процессов
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:3000 | xargs kill -9 2>/dev/null

# Очистка кэша
rm -rf node_modules/.cache 2>/dev/null

# Перезапуск серверов
# ...
```

**Назначение**: Полная очистка и перезапуск всех сервисов

## 🧪 Диагностические инструменты

### 1. `status-check.html`
```html
<!-- Веб-интерфейс для проверки статуса Django и React серверов -->
<script>
async function checkDjango() {
  const response = await fetch('http://localhost:8000/api/v1/');
  // ... проверка и отображение результатов
}
</script>
```

**Назначение**: Автоматическая проверка работоспособности серверов

### 2. `test-export.html`
```html
<!-- Интерфейс для тестирования Excel экспорта -->
<script>
function exportProducts() {
  const url = 'http://localhost:8000/api/v1/reports/export/products/';
  // ... автоматическое скачивание файла
}
</script>
```

**Назначение**: Тестирование функций экспорта без основного интерфейса

### 3. `frontend/public/clear-storage.html`
```html
<!-- Инструмент для очистки localStorage браузера -->
<script>
function clearAllStorage() {
  localStorage.clear();
  sessionStorage.clear();
  // ... очистка IndexedDB и cookies
}
</script>
```

**Назначение**: Решение проблемы "черного экрана" React

## 🔄 Отличия от production конфигурации

| Аспект | Production (Docker) | Development (локально) |
|--------|-------------------|----------------------|
| **База данных** | PostgreSQL 15 | SQLite |
| **Кэширование** | Redis | В памяти |
| **Очереди задач** | Celery + Redis | Синхронно |
| **Аутентификация** | Включена | Отключена |
| **CORS** | Ограниченный | Полный доступ |
| **Логирование** | В файлы | В консоль |
| **Статика** | Nginx | Django dev server |
| **Переменные окружения** | .env.production | .env + local_no_celery |

## ⚠️ Важные замечания

1. **Безопасность**: Настройки development НЕ подходят для production
2. **Производительность**: SQLite и синхронные задачи медленнее чем production
3. **Функциональность**: Некоторые функции могут работать по-разному
4. **Отладка**: Включено подробное логирование для диагностики

## 🔧 Откат изменений

Для возврата к оригинальной конфигурации:

1. **Удалить новые файлы**:
   ```bash
   rm .env frontend/.env
   rm run-local-dev.sh restart-clean.sh
   rm status-check.html test-export.html
   rm -rf docs/
   ```

2. **Восстановить измененные файлы** из git:
   ```bash
   git checkout HEAD -- backend/apps/reports/export_views.py
   git checkout HEAD -- frontend/src/App.tsx
   git checkout HEAD -- frontend/src/api/client.ts
   git checkout HEAD -- README.md
   ```

3. **Удалить новые настройки**:
   ```bash
   rm backend/config/settings/local_no_celery.py
   rm frontend/src/components/common/DebugInfo.tsx
   ```

---

**📝 Примечание**: Все изменения обратимы и не влияют на основную production конфигурацию проекта.