# 🚨 RECOVERY PLAN - Frontend Crash

**Дата:** 2025-10-28 17:56
**Проблема:** Frontend делает запросы к localhost вместо относительных URL
**Версия:** v4.4.0
**Bundle:** main.b5ea7d21.js (BROKEN)

---

## 📋 Диагностика проблемы

### Симптомы
✅ **Страницы загружаются**, UI отображается корректно
❌ **Данные не загружаются** - "Нет данных" на всех страницах
❌ **Settings показывает** "Ошибка загрузки настроек"

### Причина
Frontend делает запросы к **неправильному URL:**
```
❌ http://localhost:8000/api/v1/products/
✅ /api/v1/products/ (относительный)
```

### Network Requests (из browser)
```json
{
  "total_requests": 11,
  "api_calls": 8,
  "failed_requests": 9,
  "api_urls": [
    {"url": "http://localhost:8000/api/v1/products/", "status": 0},
    {"url": "http://localhost:8000/api/v1/sync/status/", "status": 0}
  ]
}
```

### Backend Status
✅ **Backend работает нормально:**
```bash
curl /api/v1/products/stats/
# {"total_products": 692, "production_needed_items": 215}

curl /api/v1/settings/system-info/
# {"version": "v4.4.0"}
```

### Root Cause Analysis
При сборке frontend (main.b5ea7d21.js) переменная окружения **REACT_APP_API_URL не была подставлена** корректно:

**Файл:** `frontend/src/utils/constants.ts`
```typescript
export const API_BASE_URL = process.env.REACT_APP_API_URL || '/api/v1';
```

**Файл:** `frontend/.env.production`
```
REACT_APP_API_URL=/api/v1
REACT_APP_MEDIA_URL=/media/
```

**Проблема:** При выполнении `npm run build` переменная **не подставилась**, webpack использовал fallback `/api/v1`, но почему-то в bundle попал `http://localhost:8000`.

---

## 🔧 ВАРИАНТЫ ВОССТАНОВЛЕНИЯ

### ⭐ ВАРИАНТ 1: Откат на предыдущий рабочий bundle (БЫСТРО)

**Pros:**
- ✅ Быстро (5 минут)
- ✅ Гарантированно работает
- ✅ Минимальный риск

**Cons:**
- ❌ Потеряем исправления webhookSlice (дубли URL)
- ❌ Webhook Testing tab будет делать `/api/v1/api/v1/` запросы

**Шаги:**
1. Найти последний рабочий bundle из резервной копии
2. Задеплоить старый bundle (main.e174116f.js или предыдущий)
3. Проверить работоспособность

**Команды:**
```bash
# 1. Найти backup с рабочим frontend
ssh -p 2132 printfarm@kemomail3.keenetic.pro "ls -lht ~/backups/ | head -10"

# 2. Восстановить из backup (пример)
ssh -p 2132 printfarm@kemomail3.keenetic.pro "
cd /tmp &&
tar -xzf ~/backups/factory_v3_webhook_working_TIMESTAMP.tar.gz frontend/build &&
docker cp frontend/build/. factory_v3-nginx-1:/usr/share/nginx/html/ &&
docker restart factory_v3-nginx-1
"

# 3. Проверить
curl http://kemomail3.keenetic.pro:13000/ | grep main
```

---

### ⭐⭐ ВАРИАНТ 2: Пересборка с правильным .env (СРЕДНЕ)

**Pros:**
- ✅ Чистое решение
- ✅ Сохраняем все исправления
- ✅ Webhook Testing будет работать без дублей

**Cons:**
- ⚠️ Нужно 10-15 минут на сборку
- ⚠️ Риск повторения проблемы

**Шаги:**
1. Убедиться что `.env.production` правильный
2. Очистить cache `rm -rf node_modules/.cache`
3. Пересобрать с явным указанием переменной
4. Задеплоить и проверить

**Команды:**
```bash
# 1. Проверить .env.production
cat frontend/.env.production
# Должно быть: REACT_APP_API_URL=/api/v1

# 2. Очистить cache и пересобрать
cd frontend
rm -rf node_modules/.cache build
npm run build

# 3. Проверить что bundle использует правильный URL
grep -o 'localhost:8000' build/static/js/main.*.js
# Должно быть: пусто (ничего не найдено)

# 4. Деплой
tar -czf /tmp/frontend-fixed.tar.gz -C build .
scp -P 2132 /tmp/frontend-fixed.tar.gz printfarm@kemomail3.keenetic.pro:/tmp/
ssh -p 2132 printfarm@kemomail3.keenetic.pro "
docker cp /tmp/frontend-fixed.tar.gz factory_v3-nginx-1:/tmp/ &&
docker exec factory_v3-nginx-1 sh -c 'rm -rf /usr/share/nginx/html/* && cd /usr/share/nginx/html && tar -xzf /tmp/frontend-fixed.tar.gz' &&
docker restart factory_v3-nginx-1
"
```

---

### ⭐⭐⭐ ВАРИАНТ 3: Быстрый фикс через sed (ОЧЕНЬ БЫСТРО, НО ГРЯЗНО)

**Pros:**
- ✅ Очень быстро (2 минуты)
- ✅ Минимальные изменения

**Cons:**
- ❌ Грязный хак
- ❌ Может сломать source maps
- ❌ Не рекомендуется для production

**Команды:**
```bash
ssh -p 2132 printfarm@kemomail3.keenetic.pro "
docker exec factory_v3-nginx-1 sh -c '
sed -i \"s|http://localhost:8000/api/v1|/api/v1|g\" /usr/share/nginx/html/static/js/main.*.js
' &&
docker restart factory_v3-nginx-1
"
```

---

## 📊 РЕКОМЕНДАЦИЯ

**ВАРИАНТ 1** (откат) - если нужно быстро восстановить работу
**ВАРИАНТ 2** (пересборка) - если есть 15 минут на правильное решение

---

## ✅ Проверочный чеклист после восстановления

- [ ] Главная страница показывает данные
- [ ] `/products` показывает список товаров
- [ ] `/simpleprint` показывает файлы
- [ ] `/settings` показывает настройки
- [ ] `/planningv2` работает
- [ ] Webhook Testing tab работает (если нужен)
- [ ] Network requests идут к `/api/v1/` а не `localhost:8000`
- [ ] Backend логи без ошибок
- [ ] Создана резервная копия

---

## 🎯 Следующие шаги после восстановления

1. Выяснить почему `process.env.REACT_APP_API_URL` не подставился
2. Проверить конфигурацию webpack/create-react-app
3. Добавить pre-deploy проверку bundle на localhost references
4. Обновить документацию по деплою

---

---

## ✅ РЕШЕНИЕ ВЫПОЛНЕНО

**Дата выполнения:** 2025-10-28 22:28
**Выбранный вариант:** Вариант 2 (пересборка с явным указанием env)
**Статус:** ✅ Проблема полностью решена

### Выполненные шаги:

1. **Очистка кэша:**
   ```bash
   rm -rf build node_modules/.cache .eslintcache
   ```

2. **Исправление исходных файлов:**
   - `src/store/webhookSlice.ts:14` - изменен fallback с `http://localhost:8000` на `/api/v1`
   - `src/utils/analytics.ts:53` - изменен fallback с `http://localhost:8001/api/v1` на `/api/v1`

3. **Пересборка с явным указанием переменной:**
   ```bash
   REACT_APP_API_URL=/api/v1 npm run build
   ```

4. **Верификация bundle:**
   - Старый bundle `main.b5ea7d21.js`: 4 вхождения localhost:8000 ❌
   - Новый bundle `main.e174116f.js`: 0 вхождений localhost:8000 ✅

5. **Деплой:**
   ```bash
   tar -czf /tmp/frontend-clean-build.tar.gz -C build .
   scp -P 2132 /tmp/frontend-clean-build.tar.gz printfarm@kemomail3.keenetic.pro:/tmp/
   docker cp /tmp/frontend-clean-build.tar.gz factory_v3-nginx-1:/tmp/
   docker exec factory_v3-nginx-1 sh -c 'rm -rf /usr/share/nginx/html/* && cd /usr/share/nginx/html && tar -xzf /tmp/frontend-clean-build.tar.gz'
   docker restart factory_v3-nginx-1
   ```

6. **Проверка API:**
   - ✅ `/api/v1/products/stats/` - 692 товара
   - ✅ `/api/v1/settings/system-info/` - v4.4.0
   - ✅ `/api/v1/sync/status/` - работает нормально

7. **Резервная копия:**
   - Создан backup: `factory_v3_recovery_fixed_20251028_222839.tar.gz` (64MB)

### Root Cause (Корневая причина)

Проблема была в том, что webpack не подставлял переменную окружения `REACT_APP_API_URL` из файла `.env.production` во время обычной сборки `npm run build`.

**Решение:** Явно указывать переменную в командной строке:
```bash
REACT_APP_API_URL=/api/v1 npm run build
```

### Рекомендации для будущего:

1. **Обновить скрипты сборки в `package.json`:**
   ```json
   "build": "REACT_APP_API_URL=/api/v1 react-scripts build"
   ```

2. **Добавить pre-deploy проверку:**
   ```bash
   # Проверка bundle перед деплоем
   if grep -q 'localhost:8000' build/static/js/main.*.js; then
     echo "❌ ERROR: Bundle содержит localhost references!"
     exit 1
   fi
   ```

3. **Документировать правильную команду сборки** в README.md

---

**Статус:** ✅ Проблема решена, система восстановлена
**Автор:** Claude Code
**Timestamp:** 2025-10-28 22:28
