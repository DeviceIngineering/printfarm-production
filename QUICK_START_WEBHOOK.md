# ⚡ Quick Start - Webhook Testing Interface

## 🎯 Что проверить (5 минут)

### 1. Открыть страницу
```
http://kemomail3.keenetic.pro:13000/planning-v2
```

### 2. Открыть модальное окно
Кнопка 🐛 (правый верхний угол) → "Отладка API"

### 3. Перейти на 4-ю вкладку
"🔗 Webhook Testing"

### 4. Проверить что работает
- ✅ Статистика: 4 карточки с цифрами
- ✅ Таблица: список событий
- ✅ Тег: "🟢 LIVE" (зеленый)
- ✅ Данные обновляются каждые 5 сек

### 5. Протестировать кнопку
Dropdown "Отправить тест" → выбрать "job.started" → отправить
→ должно появиться новое событие в таблице

---

## 🐛 Если не работает

### Backend проверка:
```bash
curl -H "Authorization: Token 0a8fee03bca2b530a15b1df44d38b304e3f57484" \
  http://kemomail3.keenetic.pro:13000/api/v1/simpleprint/webhook/stats/
```
Должен вернуть JSON.

### Frontend проверка:
1. F12 → Console - есть ошибки?
2. F12 → Network → фильтр "webhook" - запросы идут?

### Пересборка (если нужно):
```bash
cd /Users/dim11/Documents/myProjects/Factory_v3/frontend
npm run build

# Развернуть
cd ..
tar -czf /tmp/frontend-build.tar.gz -C frontend/build .
scp -P 2132 /tmp/frontend-build.tar.gz printfarm@kemomail3.keenetic.pro:/tmp/

ssh -p 2132 printfarm@kemomail3.keenetic.pro "
docker cp /tmp/frontend-build.tar.gz factory_v3-nginx-1:/tmp/ &&
docker exec factory_v3-nginx-1 sh -c 'rm -rf /usr/share/nginx/html/* && cd /usr/share/nginx/html && tar -xzf /tmp/frontend-build.tar.gz' &&
docker restart factory_v3-nginx-1
"

rm /tmp/frontend-build.tar.gz
```

---

## 📁 Ключевые файлы

**Backend** (на сервере):
- `~/factory_v3/backend/apps/simpleprint/views.py`
- `~/factory_v3/backend/apps/simpleprint/urls.py`

**Frontend** (локально):
- `frontend/src/store/webhookSlice.ts`
- `frontend/src/pages/PlanningV2Page/components/WebhookTestingTab/`
- `frontend/src/pages/PlanningV2Page/components/Header/Header.tsx`

---

## ✅ Готово!

**Вкладка работает** = все 5 пунктов выше выполнены
**Полная документация**: `CLAUDE_HANDOFF_WEBHOOK.md`

---

**Дата**: 2025-10-28 | **Статус**: Ready ✅
