# 🤝 Передача проекта: Webhook Integration для Planning V2

**Дата**: 2025-10-28
**Статус**: Backend готов (100%), Frontend развернут (100%)
**Задача**: Проверить работоспособность и протестировать UI

---

## 📋 Краткое описание

Реализована система real-time мониторинга webhook событий от SimplePrint в модальном окне "Отладка API" на странице Planning V2.

---

## 🎯 Что уже сделано

### Backend (100% ✅)

**Файлы обновлены на сервере**:
- `backend/apps/simpleprint/views.py` - 4 новых API views
- `backend/apps/simpleprint/urls.py` - 4 новых URL patterns
- `backend/apps/simpleprint/serializers.py` - serializers для webhook

**API Endpoints (все работают)**:
```
GET  /api/v1/simpleprint/webhook/events/    # Список событий
GET  /api/v1/simpleprint/webhook/stats/     # Статистика
POST /api/v1/simpleprint/webhook/test-trigger/  # Тест
DELETE /api/v1/simpleprint/webhook/events/clear/ # Очистка
```

**Тест**:
```bash
curl -H "Authorization: Token 0a8fee03bca2b530a15b1df44d38b304e3f57484" \
  http://kemomail3.keenetic.pro:13000/api/v1/simpleprint/webhook/stats/
```

Должен вернуть JSON с статистикой.

---

### Frontend (100% ✅)

**Файлы созданы/обновлены**:

1. **Redux slice**:
   - `frontend/src/store/webhookSlice.ts` - создан
   - `frontend/src/store/index.ts` - обновлен (добавлен webhook reducer)

2. **Компонент**:
   - `frontend/src/pages/PlanningV2Page/components/WebhookTestingTab/WebhookTestingTab.tsx` - создан
   - `frontend/src/pages/PlanningV2Page/components/WebhookTestingTab/WebhookTestingTab.css` - создан

3. **Интеграция**:
   - `frontend/src/pages/PlanningV2Page/components/Header/Header.tsx` - обновлен (добавлена 4-я вкладка)

**Статус сборки**:
- ✅ `npm run build` выполнен успешно
- ✅ Frontend развернут на сервере (nginx перезапущен)

---

## 🧪 Задача для проверки

### Шаг 1: Открыть страницу в браузере

```
URL: http://kemomail3.keenetic.pro:13000/planning-v2
```

### Шаг 2: Открыть модальное окно "Отладка API"

- Найти кнопку с иконкой 🐛 (Bug) в правом верхнем углу
- Нажать на неё
- Модальное окно должно открыться

### Шаг 3: Проверить 4-ю вкладку

В модальном окне должны быть 4 вкладки:
1. Frontend данные
2. Backend данные (детально)
3. Сравнение Frontend vs Backend
4. **🔗 Webhook Testing** ← нужно проверить эту!

### Шаг 4: Протестировать функции

На вкладке "🔗 Webhook Testing" должно быть:

**Статистика (4 карточки)**:
- Всего событий: ~8
- Обработано: 8/8
- За последний час: ~8
- Ошибок: 0

**События по типам** (цветные теги):
- job_started: 2
- job_completed: 1
- job_failed: 1
- и т.д.

**Кнопки управления**:
- ✅ "Обновить" - должна обновлять данные
- ✅ "Отправить тест" (dropdown) - выбрать событие и отправить
- ✅ "Очистить старые" - удаление событий > 7 дней
- ✅ "🟢 LIVE" / "Остановить" - переключатель auto-refresh

**Таблица событий**:
- Колонки: Время, Событие, Printer ID, Job ID, Статус
- Пагинация: 10/20/50 событий
- Должна обновляться каждые 5 секунд автоматически

---

## 🐛 Возможные проблемы и решения

### Проблема 1: Вкладка не отображается

**Проверить**:
```bash
# На локальной машине
cat frontend/src/pages/PlanningV2Page/components/Header/Header.tsx | grep "Webhook Testing"

# Должно найти строку:
# <TabPane tab="🔗 Webhook Testing" key="4">
```

**Если нет** - добавить вручную в Header.tsx после TabPane key="3":

```typescript
            {/* Вкладка 4: Webhook Testing */}
            <TabPane tab="🔗 Webhook Testing" key="4">
              <WebhookTestingTab />
            </TabPane>
```

И пересобрать:
```bash
cd frontend
npm run build
# Развернуть (команды ниже)
```

---

### Проблема 2: Ошибка при открытии вкладки

**Открыть консоль браузера** (F12) и посмотреть ошибки.

**Возможные ошибки**:

**А) "Cannot find module 'webhookSlice'"**

Проверить файл существует:
```bash
ls -la frontend/src/store/webhookSlice.ts
```

Если нет - создать из `WEBHOOK_FRONTEND_IMPLEMENTATION.md` (код там есть).

**Б) "useSelector/useDispatch not found"**

Убедиться что импорты правильные в WebhookTestingTab.tsx:
```typescript
import { useDispatch, useSelector } from 'react-redux';
import type { AppDispatch } from '../../../../store';
```

**В) API 401 Unauthorized**

Проверить токен в localStorage браузера:
```javascript
// В консоли браузера
localStorage.getItem('auth_token')
```

Должен быть: `0a8fee03bca2b530a15b1df44d38b304e3f57484`

---

### Проблема 3: Данные не загружаются

**Проверить API endpoint**:
```bash
curl -H "Authorization: Token 0a8fee03bca2b530a15b1df44d38b304e3f57484" \
  http://kemomail3.keenetic.pro:13000/api/v1/simpleprint/webhook/stats/
```

**Если 500 ошибка** - проверить логи backend:
```bash
ssh -p 2132 printfarm@kemomail3.keenetic.pro \
  'docker logs --tail 50 factory_v3-backend-1' | grep -i error
```

**Если 404** - проверить URLs:
```bash
ssh -p 2132 printfarm@kemomail3.keenetic.pro \
  'cat ~/factory_v3/backend/apps/simpleprint/urls.py' | grep webhook
```

Должно быть 4 URL с 'webhook/':
- webhook/events/
- webhook/stats/
- webhook/test-trigger/
- webhook/events/clear/

---

### Проблема 4: Auto-refresh не работает

**Проверить в коде WebhookTestingTab.tsx**:

```typescript
useEffect(() => {
  if (autoRefresh) {
    // ... должен быть setInterval с 5000ms
  }
}, [autoRefresh, dispatch]);
```

Проверить в браузере: должен быть тег "🟢 LIVE".

---

## 🔧 Команды для пересборки (если нужно)

### Локальная машина:

```bash
# 1. Перейти в директорию
cd /Users/dim11/Documents/myProjects/Factory_v3/frontend

# 2. Собрать
npm run build

# 3. Создать архив
cd ..
tar -czf /tmp/frontend-build.tar.gz -C frontend/build .

# 4. Загрузить на сервер
scp -P 2132 /tmp/frontend-build.tar.gz printfarm@kemomail3.keenetic.pro:/tmp/

# 5. Развернуть (SSH)
ssh -p 2132 printfarm@kemomail3.keenetic.pro "
docker cp /tmp/frontend-build.tar.gz factory_v3-nginx-1:/tmp/ &&
docker exec factory_v3-nginx-1 sh -c 'rm -rf /usr/share/nginx/html/* && cd /usr/share/nginx/html && tar -xzf /tmp/frontend-build.tar.gz' &&
docker restart factory_v3-nginx-1
"

# 6. Очистить
rm /tmp/frontend-build.tar.gz
```

---

## 📁 Структура файлов

```
Factory_v3/
├── backend/
│   └── apps/
│       └── simpleprint/
│           ├── views.py                    # ✅ Обновлен (+268 строк)
│           ├── urls.py                     # ✅ Обновлен (+4 URL)
│           ├── serializers.py              # ✅ Обновлен
│           └── models.py                   # ✅ (модели созданы ранее)
│
└── frontend/
    └── src/
        ├── store/
        │   ├── webhookSlice.ts             # ✅ Создан
        │   └── index.ts                    # ✅ Обновлен
        │
        └── pages/
            └── PlanningV2Page/
                └── components/
                    ├── Header/
                    │   └── Header.tsx      # ✅ Обновлен (+8 строк)
                    │
                    └── WebhookTestingTab/  # ✅ Создан
                        ├── WebhookTestingTab.tsx
                        └── WebhookTestingTab.css
```

---

## 📊 Ожидаемое поведение

### Нормальная работа:

1. **При открытии вкладки**:
   - Spinner на 1-2 секунды
   - Загружается статистика (4 карточки)
   - Загружается таблица событий
   - Тег показывает "🟢 LIVE"

2. **Каждые 5 секунд**:
   - Данные автоматически обновляются
   - Без перезагрузки страницы
   - Без мерцания

3. **При нажатии "Обновить"**:
   - Кнопка показывает spinner
   - Данные обновляются
   - Появляется уведомление "Данные обновлены"

4. **При выборе "Отправить тест"**:
   - Выбрать событие из dropdown
   - Появляется уведомление "Тестовый webhook job.started отправлен"
   - Через 0.5 сек таблица обновляется
   - В таблице появляется новое событие (первая строка)

5. **При нажатии "Очистить старые"**:
   - Появляется уведомление "Старые события удалены"
   - Счетчик "Всего событий" может уменьшиться

6. **При нажатии "Остановить"**:
   - Тег меняется на "⚪ Остановлено"
   - Auto-refresh прекращается
   - Кнопка меняется на "Запустить"

---

## 🎯 Критерии успеха

### Минимальные требования (Must Have):
- ✅ Вкладка "🔗 Webhook Testing" отображается
- ✅ Статистика загружается и показывает данные
- ✅ Таблица событий отображается с данными
- ✅ Кнопка "Обновить" работает

### Полная функциональность (Should Have):
- ✅ Auto-refresh работает (данные обновляются каждые 5 сек)
- ✅ "Отправить тест" создает новое событие
- ✅ "Очистить старые" удаляет события
- ✅ Переключатель LIVE/Остановлено работает

---

## 📞 Если что-то не работает

### Порядок диагностики:

1. **Проверить Backend API**:
   ```bash
   curl -H "Authorization: Token 0a8fee03bca2b530a15b1df44d38b304e3f57484" \
     http://kemomail3.keenetic.pro:13000/api/v1/simpleprint/webhook/stats/
   ```
   Должен вернуть JSON с данными.

2. **Проверить консоль браузера** (F12 → Console):
   - Есть ли ошибки JavaScript?
   - Есть ли ошибки API (401/404/500)?

3. **Проверить Network tab** (F12 → Network):
   - Отправляются ли запросы к `/api/v1/simpleprint/webhook/`?
   - Какой статус код?
   - Какой ответ?

4. **Проверить Redux DevTools** (если установлены):
   - Есть ли `webhook` state?
   - Вызываются ли actions (fetchWebhookStats, fetchWebhookEvents)?
   - Какие данные в state?

5. **Проверить файлы на сервере**:
   ```bash
   ssh -p 2132 printfarm@kemomail3.keenetic.pro

   # Backend файлы
   ls -la ~/factory_v3/backend/apps/simpleprint/views.py
   ls -la ~/factory_v3/backend/apps/simpleprint/urls.py

   # Проверить nginx
   docker exec factory_v3-nginx-1 ls -la /usr/share/nginx/html/
   ```

---

## 📚 Дополнительная документация

**Если нужны детали**:
- `WEBHOOK_IMPLEMENTATION_COMPLETE.md` - полный отчет
- `WEBHOOK_FRONTEND_IMPLEMENTATION.md` - код Frontend
- `WEBHOOK_TEST_RESULTS.md` - результаты тестов Backend
- `SIMPLEPRINT_UI_SETUP.md` - настройка SimplePrint

**Все файлы в директории**:
```
/Users/dim11/Documents/myProjects/Factory_v3/
```

---

## ✅ Чеклист для проверки

- [ ] Открыл Planning V2 страницу
- [ ] Нажал кнопку "Отладка API" (🐛)
- [ ] Увидел 4 вкладки в модальном окне
- [ ] Перешел на вкладку "🔗 Webhook Testing"
- [ ] Статистика загрузилась (4 карточки с цифрами)
- [ ] Таблица событий отобразилась
- [ ] Нажал "Обновить" - данные обновились
- [ ] Выбрал событие в dropdown "Отправить тест" - событие создалось
- [ ] Тег показывает "🟢 LIVE"
- [ ] Данные обновляются каждые 5 секунд
- [ ] Нажал "Остановить" - auto-refresh остановился
- [ ] Все работает без ошибок в консоли

---

## 🚀 Финальный тест

**Полный цикл**:

1. Открыть вкладку → данные загружаются ✅
2. Выбрать "job.started" → отправить ✅
3. Подождать 5 секунд → таблица обновилась автоматически ✅
4. Новое событие в первой строке таблицы ✅
5. Счетчик "Всего событий" увеличился на 1 ✅

**Если все 5 пунктов работают - интеграция успешна! 🎉**

---

**Версия**: v4.3.0
**Дата**: 2025-10-28
**Статус**: Ready for Testing ✅
