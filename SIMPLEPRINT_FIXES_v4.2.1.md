# SimplePrint Fixes v4.2.1 - Исправления синхронизации

## 📋 Дата: 2025-10-23
## 🎯 Версия: 4.2.1

## 🐛 Исправленные проблемы

### 1. **Ошибка отмены синхронизации** ❌ → ✅

**Проблема**: При попытке отменить синхронизацию возникала ошибка "Not Found: /api/v1/simpleprint/sync/cancel/{task_id}/"

**Причина**: Неправильный URL pattern для ViewSet action - `url_path='cancel/(?P<task_id>[^/.]+)'` не работает с DRF Router

**Решение**:
```python
# Было (НЕ РАБОТАЛО):
@action(detail=False, methods=['post'], url_path='cancel/(?P<task_id>[^/.]+)')
def cancel_sync(self, request, task_id=None):
    ...

# Стало (РАБОТАЕТ):
@action(detail=False, methods=['post'], url_path='cancel')
def cancel_sync(self, request):
    task_id = request.data.get('task_id')
    ...
```

**Изменения**:
- `backend/apps/simpleprint/views.py:393-440` - изменен endpoint для отмены синхронизации
- `frontend/src/store/simpleprintSlice.ts:128-134` - task_id теперь передается в теле запроса
- `frontend/src/pages/SimplePrintPage.tsx:149-155` - обновлено логирование API request

**URL**:
- Было: `POST /api/v1/simpleprint/sync/cancel/{task_id}/`
- Стало: `POST /api/v1/simpleprint/sync/cancel/` + body: `{"task_id": "..."}`

---

### 2. **Закрытие окна во время синхронизации** ⚠️ → ✅

**Проблема**: Окно синхронизации закрывалось во время активной синхронизации при нажатии крестика, ESC или клике вне окна

**Решение**: Отключены все способы закрытия модального окна во время активной синхронизации

```typescript
<Modal
  title="Синхронизация с SimplePrint"
  open={syncModalVisible}
  closable={!syncing}         // ❌ Крестик (X) отключен
  maskClosable={!syncing}     // ❌ Клик вне окна отключен
  keyboard={!syncing}         // ❌ ESC отключен
  onCancel={() => {
    if (syncing && currentTaskId) {
      Modal.confirm({
        title: 'Синхронизация в процессе',
        content: 'Синхронизация продолжается в фоновом режиме. Закрыть окно?',
        okText: 'Да, закрыть',
        cancelText: 'Продолжить наблюдение',
        onOk: () => {
          setSyncModalVisible(false);
        },
      });
    } else {
      setSyncModalVisible(false);
    }
  }}
>
```

**Изменения**:
- `frontend/src/pages/SimplePrintPage.tsx:399-420` - добавлены три новых свойства Modal

**Результат**:
- ✅ Крестик (X) не появляется во время синхронизации
- ✅ Клик вне окна не закрывает его
- ✅ ESC не закрывает окно
- ✅ При попытке закрыть через кнопку "Закрыть" показывается подтверждение

---

### 3. **Прогресс загруженных файлов не отображается** 📊 → ✅

**Проблема**: Во время синхронизации прогресс показывал "Папки: 0 / 0, Файлы: 0 / 0"

**Причина**: SimplePrint синхронизация имеет 2 фазы:
1. **Фаза загрузки данных** (~5 минут): Рекурсивная загрузка всех файлов и папок из SimplePrint API с rate limiting (180 req/min)
2. **Фаза синхронизации**: Сохранение в базу данных и обновление прогресса

`total_files` и `total_folders` устанавливаются только ПОСЛЕ завершения фазы 1.

**Решение**: Добавлено информативное сообщение для фазы загрузки данных

```typescript
// Если данные еще загружаются (total = 0)
if (total_files === 0 && total_folders === 0) {
  return [
    ...baseLog,
    `⏳ Загрузка данных из SimplePrint API...`,
    `📡 Это может занять несколько минут (rate limit: 180 req/min)`,
    `🔄 Polling #${pollCount} [${timestamp}]`,
  ];
}

// Данные загружены, показываем прогресс
const progress = total_files > 0 ? Math.round((synced_files / total_files) * 100) : 0;
return [
  ...baseLog,
  `📁 Папки: ${synced_folders} / ${total_folders}`,
  `📄 Файлы: ${synced_files} / ${total_files}`,
  `⚡ Прогресс: ${progress}%`,
  `🔄 Polling #${pollCount} [${timestamp}]`,
];
```

**Изменения**:
- `frontend/src/pages/SimplePrintPage.tsx:78-96` - добавлено условие для фазы загрузки

**Результат**:
- ✅ При `total_files === 0`: показывается "⏳ Загрузка данных из SimplePrint API..."
- ✅ При `total_files > 0`: показывается реальный прогресс "Файлы: 350 / 1589"
- ✅ Пользователь понимает что происходит во время длительной загрузки

---

## 🚀 Деплой изменений

### Backend
```bash
# Загрузка файлов
scp -P 2132 backend/apps/simpleprint/views.py printfarm@kemomail3.keenetic.pro:~/factory_v3/backend/apps/simpleprint/

# Перезапуск backend
ssh -p 2132 printfarm@kemomail3.keenetic.pro "docker restart factory_v3-backend-1"
```

### Frontend
```bash
# Сборка
npm run build

# Создание архива и деплой
tar -czf /tmp/frontend-build.tar.gz -C build .
scp -P 2132 /tmp/frontend-build.tar.gz printfarm@kemomail3.keenetic.pro:/tmp/
ssh -p 2132 printfarm@kemomail3.keenetic.pro "
  docker cp /tmp/frontend-build.tar.gz factory_v3-nginx-1:/tmp/ &&
  docker exec factory_v3-nginx-1 sh -c 'rm -rf /usr/share/nginx/html/* && cd /usr/share/nginx/html && tar -xzf /tmp/frontend-build.tar.gz' &&
  docker restart factory_v3-nginx-1
"
rm /tmp/frontend-build.tar.gz
```

---

## ✅ Проверка работоспособности

### 1. Проверка отмены синхронизации
```bash
# Запустить синхронизацию
# Во время синхронизации нажать кнопку "Отменить синхронизацию"
# Ожидаемый результат: сообщение "✅ Задача синхронизации отменена"
```

### 2. Проверка закрытия окна
```bash
# Запустить синхронизацию
# Попробовать закрыть окно:
#   - Нажать крестик (X) - не должно работать
#   - Кликнуть вне окна - не должно закрывать
#   - Нажать ESC - не должно закрывать
#   - Нажать кнопку "Закрыть" - должен показаться диалог подтверждения
```

### 3. Проверка прогресса
```bash
# Запустить синхронизацию с галочкой "Принудительная синхронизация"
# Ожидаемые сообщения:
#   1. "⏳ Загрузка данных из SimplePrint API..." - первые ~5 минут
#   2. "📁 Папки: 150 / 649" - когда данные загружены
#   3. "📄 Файлы: 350 / 1589" - обновляется в реальном времени
#   4. "⚡ Прогресс: 22%" - процент выполнения
```

---

## 📊 Технические детали

### API Endpoints

#### Cancel Sync
```
POST /api/v1/simpleprint/sync/cancel/
Content-Type: application/json

{
  "task_id": "a881ca96-e619-4f2d-97a0-d8a9420801b9"
}

Response:
{
  "status": "cancelled",
  "task_id": "a881ca96-e619-4f2d-97a0-d8a9420801b9",
  "message": "Задача синхронизации отменена"
}
```

#### Check Status
```
GET /api/v1/simpleprint/sync/status/{task_id}/

Response (во время загрузки данных):
{
  "task_id": "...",
  "state": "PENDING",
  "ready": false,
  "progress": {
    "total_files": 0,         // ← Еще не установлено
    "synced_files": 0,
    "total_folders": 0,       // ← Еще не установлено
    "synced_folders": 0
  }
}

Response (после загрузки данных):
{
  "task_id": "...",
  "state": "STARTED",
  "ready": false,
  "progress": {
    "total_files": 1589,      // ← Установлено!
    "synced_files": 350,
    "total_folders": 649,     // ← Установлено!
    "synced_folders": 150
  }
}
```

### Фазы синхронизации SimplePrint

#### Фаза 1: Загрузка данных (5-10 минут)
```python
# backend/apps/simpleprint/services.py
def fetch_all_files_and_folders_recursively():
    """
    Рекурсивная загрузка ВСЕХ файлов и папок из SimplePrint API

    Rate limit: 180 req/min = 3 req/sec
    Всего папок: 649
    Всего файлов: 1589

    Время: ~649 запросов / 3 req/sec = ~216 секунд = ~4 минуты
    """
    # total_files = 0 на этой фазе
    # total_folders = 0 на этой фазе
```

#### Фаза 2: Синхронизация с БД (2-5 минут)
```python
# backend/apps/simpleprint/services.py
def sync_all_files(full_sync=False):
    """
    Сохранение в базу данных и обновление прогресса

    1. Устанавливаем total_files, total_folders
    2. Сохраняем папки (обновляем synced_folders)
    3. Сохраняем файлы (обновляем synced_files каждые 50 файлов)
    """
    # total_files = 1589 установлено!
    # total_folders = 649 установлено!

    # Обновление прогресса каждые 50 файлов
    if synced_count % 50 == 0:
        sync_log.synced_files = synced_count
        sync_log.save()
```

---

## 🔍 Диагностика проблем

### Проблема: Отмена не работает

**Проверка через логи**:
```bash
ssh -p 2132 printfarm@kemomail3.keenetic.pro "docker logs factory_v3-backend-1 --tail 50 | grep -i cancel"

# Ожидаемый вывод:
# INFO Attempting to cancel task: a881ca96-e619-4f2d..., state: STARTED
# INFO Updated sync log 8 status to cancelled
```

**Проверка task_id**:
```bash
# В логах синхронизации должно быть:
# 📡 API Request: POST /api/v1/simpleprint/sync/cancel/
# 📝 Body: { task_id: "a881ca96..." }
```

### Проблема: Прогресс показывает 0/0 слишком долго

**Проверка через Django shell**:
```bash
ssh -p 2132 printfarm@kemomail3.keenetic.pro "docker exec factory_v3-backend-1 python manage.py shell -c \"
from apps.simpleprint.models import SimplePrintSync
sync = SimplePrintSync.objects.filter(status='pending').first()
print(f'Total files: {sync.total_files}, Synced: {sync.synced_files}')
\""

# Если показывает "Total files: 0", значит еще на фазе загрузки данных
```

**Проверка Celery worker**:
```bash
ssh -p 2132 printfarm@kemomail3.keenetic.pro "docker logs factory_v3-celery-1 --tail 100 | grep -i 'fetching files'"

# Ожидаемый вывод:
# INFO Fetching files and folders for parent_id=16787
# INFO Fetched 25 folders and 150 files from parent_id=16787
```

---

## 📝 Итоги v4.2.1

✅ **Исправлено**:
1. Отмена синхронизации работает корректно через POST `/sync/cancel/`
2. Окно не закрывается во время активной синхронизации
3. Прогресс отображается корректно с информативным сообщением во время загрузки данных

🔧 **Измененные файлы**:
- `backend/apps/simpleprint/views.py` - изменен endpoint отмены
- `frontend/src/store/simpleprintSlice.ts` - изменен API call для отмены
- `frontend/src/pages/SimplePrintPage.tsx` - добавлена защита от закрытия и сообщение о загрузке

📦 **Деплой**:
- Backend: перезапущен docker container
- Frontend: пересобран и задеплоен через nginx

---

**Версия**: 4.2.1
**Дата**: 2025-10-23
**Статус**: ✅ Все исправления задеплоены и протестированы
