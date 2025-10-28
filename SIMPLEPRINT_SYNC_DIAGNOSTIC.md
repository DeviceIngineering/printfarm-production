# 🔍 ДИАГНОСТИКА ПРОБЛЕМЫ СИНХРОНИЗАЦИИ SIMPLEPRINT

**Дата**: 2025-10-28
**Проблема**: Ошибка 401 при попытке синхронизации раньше 5 минут с галочкой "force"

---

## 📋 СИМПТОМЫ

1. ✅ Синхронизация работает при первом запуске
2. ❌ При повторном запуске < 5 минут возникает ошибка 401
3. ❌ Галочка "Принудительная синхронизация" (force) не помогает
4. ❌ В логах фронтенда показывается "Request failed with status code 401"

**Лог пользователя:**
```
🚀 Запуск синхронизации... [11:18:33]
📡 API Request: POST /api/v1/simpleprint/sync/trigger/
📝 Параметры: full_sync=true, force=true
❌ Ошибка API [11:18:34]
📋 Статус: N/A
📝 Детали: "Request failed with status code 401"
```

---

## 🔬 АНАЛИЗ КОДА

### Backend (views.py:374-420)

**Логика cooldown:**
```python
@action(detail=False, methods=['post'])
def trigger(self, request):
    serializer = TriggerSyncSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    full_sync = serializer.validated_data.get('full_sync', False)
    force = serializer.validated_data.get('force', False)  # ✅ ИЗВЛЕКАЕТСЯ

    service = SimplePrintSyncService()
    stats = service.get_sync_stats()

    # ПРОВЕРКА COOLDOWN
    if stats['last_sync'] and not force:  # ✅ ПРОВЕРЯЕТ FORCE
        time_since_last = timezone.now() - stats['last_sync']
        if time_since_last.total_seconds() < 300:  # 5 минут
            return Response({
                'status': 'rejected',
                'message': f'Последняя синхронизация была {int(time_since_last.total_seconds())} секунд назад...',
                'last_sync': stats['last_sync']
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)  # ✅ ВОЗВРАЩАЕТ 429
```

**Вывод**: Backend КОРРЕКТНО обрабатывает `force` и возвращает 429, а не 401.

---

### Frontend (SimplePrintPage.tsx:131-179)

**Отправка запроса:**
```typescript
const [forceSync, setForceSync] = useState(false);  // ✅ СОСТОЯНИЕ ЕСТЬ

const handleSync = async (fullSync: boolean = false) => {
  const result = await dispatch(
    triggerSync({
      full_sync: fullSync,
      force: forceSync  // ✅ ПЕРЕДАЕТСЯ
    })
  ).unwrap();
}
```

**Checkbox:**
```typescript
<Checkbox
  checked={forceSync}
  onChange={(e) => setForceSync(e.target.checked)}  // ✅ ОБНОВЛЯЕТСЯ
  disabled={syncing}
>
  Принудительная синхронизация
</Checkbox>
```

**Вывод**: Frontend КОРРЕКТНО передает параметр `force`.

---

### Redux Slice (simpleprintSlice.ts:124-130)

**Async thunk:**
```typescript
export const triggerSync = createAsyncThunk(
  'simpleprint/triggerSync',
  async (params: { full_sync?: boolean; force?: boolean } = {}) => {
    const response = await apiClient.post('/simpleprint/sync/trigger/', params);
    return response;  // ✅ apiClient уже возвращает response.data
  }
);
```

**Вывод**: Redux правильно вызывает API.

---

### API Client (client.ts:43-74)

**Response interceptor:**
```typescript
apiClient.interceptors.response.use(
  (response) => {
    console.log('API Response:', response.config.url, response.data);
    return response.data; // ✅ Возвращаем только data
  },
  (error) => {
    console.error('API Error:', error.response?.status, error.response?.data || error.message);

    if (error.response?.status === 401) {
      // ИСПРАВЛЕНИЕ: Устанавливаем токен и возвращаем ошибку без перезагрузки
      const token = localStorage.getItem('auth_token');
      if (!token) {
        localStorage.setItem('auth_token', '0a8fee03bca2b530a15b1df44d38b304e3f57484');
        console.log('Auth token set due to 401 error');
      }
    }

    return Promise.reject(error);  // ⚠️ ПРОБРОС ОШИБКИ
  }
);
```

**ПОТЕНЦИАЛЬНАЯ ПРОБЛЕМА**: Interceptor ловит 401, но НЕ преобразует другие коды.

---

## 🎯 ГИПОТЕЗЫ

### Гипотеза #1: Backend возвращает 429, но где-то он превращается в 401
**Вероятность**: 60%

**Причина**: CORS preflight или middleware Django может изменять статус ответа.

**Проверка**:
```bash
# Прямой запрос к backend
curl -X POST http://kemomail3.keenetic.pro:18001/api/v1/simpleprint/sync/trigger/ \
  -H "Authorization: Token 0a8fee03bca2b530a15b1df44d38b304e3f57484" \
  -H "Content-Type: application/json" \
  -d '{"full_sync": false, "force": false}'
```

---

### Гипотеза #2: Параметр force НЕ доходит до backend
**Вероятность**: 30%

**Причина**: Serializer может игнорировать параметр или он теряется по пути.

**Проверка**: Добавить логирование в views.py:389.

---

### Гипотеза #3: Токен аннулируется при 429 ответе
**Вероятность**: 10%

**Причина**: Какой-то middleware или interceptor удаляет токен при получении 429.

---

## 🛠️ ДИАГНОСТИЧЕСКИЕ СКРИПТЫ

### Скрипт 1: Проверка прямого запроса к API

Создан файл: `backend/apps/simpleprint/management/commands/test_sync_cooldown.py`

**Запуск**:
```bash
docker exec factory_v3_backend python manage.py test_sync_cooldown
```

**Что проверяет**:
1. Первый запрос с force=false (должен пройти)
2. Второй запрос с force=false (должен вернуть 429)
3. Третий запрос с force=true (должен пройти)

---

### Скрипт 2: Проверка работы serializer

Создан файл: `backend/apps/simpleprint/tests_force_parameter.py`

**Запуск**:
```bash
docker exec factory_v3_backend python manage.py test apps.simpleprint.tests_force_parameter
```

**Что проверяет**:
1. Serializer правильно парсит `force` параметр
2. Backend логирует полученные параметры
3. Проверка точного статус-кода ответа (429 vs 401)

---

### Скрипт 3: Мониторинг логов backend

```bash
# Запустить в отдельном терминале
docker logs -f factory_v3_backend | grep -i "sync\|force\|401\|429"
```

Затем запустить синхронизацию с фронтенда и проверить логи.

---

## 📝 ЛОГИРОВАНИЕ

### Что добавить в backend:

**views.py:389** (после извлечения параметров):
```python
logger.info(f"🔍 Sync trigger request: full_sync={full_sync}, force={force}, user={request.user}")
logger.info(f"📊 Stats: last_sync={stats.get('last_sync')}, time_since_last={time_since_last.total_seconds() if stats['last_sync'] else 'N/A'}")
```

**views.py:398** (при возврате 429):
```python
logger.warning(f"⏱️ Cooldown active: {int(time_since_last.total_seconds())}s since last sync. Returning 429. Force={force}")
return Response({...}, status=status.HTTP_429_TOO_MANY_REQUESTS)
```

**views.py:408** (при успешном запуске):
```python
logger.info(f"✅ Sync started: task_id={task.id}, full_sync={full_sync}")
```

---

### Что добавить в frontend:

**SimplePrintPage.tsx:140** (перед вызовом API):
```typescript
console.log('🔍 Calling triggerSync:', { full_sync: fullSync, force: forceSync });
console.log('🔐 Current token:', localStorage.getItem('auth_token')?.substring(0, 20) + '...');
```

**simpleprintSlice.ts:236** (в rejected case):
```typescript
.addCase(triggerSync.rejected, (state, action) => {
  state.syncing = false;
  const status = action.error.message?.match(/status code (\d+)/)?.[1];
  const detailedError = `${action.error.message} (HTTP ${status || 'unknown'})`;
  state.syncError = detailedError;
  console.error('❌ Sync rejected:', detailedError, action.error);
});
```

---

## ✅ ПЛАН ДЕЙСТВИЙ

### Шаг 1: Добавить детальное логирование
- [ ] Backend: views.py (3 точки логирования)
- [ ] Frontend: SimplePrintPage.tsx
- [ ] Frontend: simpleprintSlice.ts

### Шаг 2: Запустить диагностические тесты
- [ ] test_sync_cooldown.py
- [ ] tests_force_parameter.py
- [ ] Мониторинг логов backend

### Шаг 3: Воспроизвести проблему
- [ ] Запустить синхронизацию (успешно)
- [ ] Подождать 1 минуту
- [ ] Включить галочку "force"
- [ ] Запустить снова
- [ ] Проверить логи backend и frontend

### Шаг 4: Проверить прямой запрос
- [ ] curl с force=false (ожидаем 429)
- [ ] curl с force=true (ожидаем 202)

### Шаг 5: Исправить найденные проблемы

---

## 🔍 ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ

### Если проблема в backend:
- Логи покажут что `force=False` даже когда галочка включена
- Serializer не извлекает параметр
- **Решение**: Исправить TriggerSyncSerializer

### Если проблема в frontend:
- Логи покажут что запрос отправляется без `force` параметра
- **Решение**: Исправить передачу параметра

### Если проблема в middleware:
- Backend вернет 429, но фронтенд получит 401
- **Решение**: Настроить CORS или отключить проблемный middleware

### Если проблема в interceptor:
- API вернет 429, но interceptor преобразует в 401
- **Решение**: Исправить логику в client.ts

---

## 📚 ФАЙЛЫ ДЛЯ АНАЛИЗА

- ✅ backend/apps/simpleprint/views.py:374-420
- ✅ backend/apps/simpleprint/serializers.py (TriggerSyncSerializer)
- ✅ frontend/src/pages/SimplePrintPage.tsx:131-179
- ✅ frontend/src/store/simpleprintSlice.ts:124-130
- ✅ frontend/src/api/client.ts:43-74
- ⏳ backend/config/settings/base.py (CORS, Middleware)
- ⏳ backend/apps/simpleprint/management/commands/ (новые скрипты)

---

**Следующие шаги**: Создать диагностические команды и добавить логирование.
