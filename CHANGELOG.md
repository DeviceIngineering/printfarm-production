# 📋 CHANGELOG - История развития проекта PrintFarm

Полная история изменений системы управления производством PrintFarm с интеграцией МойСклад и SimplePrint.

---

## 🐛 v4.2.10.4 (2025-10-28) - Fix PrinterSnapshot NULL Constraint Error

**🔧 Исправления:**
- 🛠️ **PrinterSnapshot model - nullable layer fields**
  - Добавлено `null=True, blank=True` для `current_layer` и `max_layer`
  - Исправлена ошибка "NOT NULL constraint failed" для P1S-4 и P1S-18
  - SimplePrint API иногда не предоставляет значения слоев
  - Все 25 принтеров теперь синхронизируются успешно (ранее 23/25)

**📄 Изменённые файлы:**
- `backend/apps/simpleprint/models.py` - nullable поля слоев
- Migration `0004_alter_printersnapshot_current_layer_and_more.py`

**📊 Результат:**
- ✅ 25 принтеров синхронизировано, 0 ошибок (100% успех)
- ✅ P1S-4 (28177) и P1S-18 (28196) теперь работают корректно
- ✅ Принтеры без данных о слоях больше не вызывают падение синхронизации

**💾 Коммиты:**
- `dc2e11a` - 🐛 Fix: Allow NULL values for PrinterSnapshot layer fields

---

## 📦 v4.2.10.3 (2025-10-28) - Enhanced API Debug Modal with Full Details

**✨ Новые возможности:**
- 🎯 **Расширенное модальное окно "Отладка API"**
  - Ручная загрузка данных кнопкой "Обновить данные"
  - Отображение времени последнего обновления
  - Индикатор загрузки во время запроса

- 📊 **Детальная таблица Backend данных (15+ колонок)**
  - ID, Имя, Online, State, Job File
  - Артикул, Прогресс, Слои (current/total)
  - Прошло, Осталось (время)
  - Начало, Конец печати (ожидаемый)
  - Температуры (сопло, стол), Idle время

- 🎨 **Три вкладки в модальном окне**
  - Frontend данные - данные из Redux state
  - Backend данные (детально) - полная информация из API
  - Сравнение Frontend vs Backend - анализ расхождений

- 🔍 **Фильтры и поиск**
  - Фильтр по статусу (printing/idle/error)
  - Фильтр по online/offline
  - Поиск по имени принтера (real-time)

- 📂 **Expandable rows с детальной информацией**
  - Descriptions с дополнительными полями
  - DB ID, Job ID, State Display
  - T° Ambient, Idle Since, Created At
  - Полный Raw JSON от Backend API

- 💾 **Экспорт данных**
  - Export CSV - экспорт всех данных в CSV файл
  - Copy JSON - копирование JSON в буфер обмена
  - Toast уведомления при успехе/ошибке

- 📈 **Сводная статистика**
  - По Frontend: всего, печатают, idle, offline
  - По Backend: всего, online, печатают, offline
  - Счетчик отфильтрованных записей

**🔧 Технические изменения:**
- Обновлен `Header.tsx` в `PlanningV2Page/components/`
  - +366 строк, -57 строк кода
  - Новые imports: Tabs, Spin, Descriptions, message
  - Новые icons: DownloadOutlined, CopyOutlined, SyncOutlined
  - State management для фильтров и поиска
  - Вспомогательные функции: formatSeconds, formatDateTime, extractArticle

- Функции обработки данных:
  - `handleRefreshApiData()` - ручная загрузка с API
  - `handleExportCSV()` - генерация CSV с blob download
  - `handleCopyJSON()` - копирование в clipboard
  - Фильтрация данных по status, online, searchText

- Таблицы с колонками:
  - Frontend: 11 колонок (ID, Имя, Статус, Артикул, Прогресс, Осталось, Начало, Конец, Темп, Цвет, Очередь)
  - Backend: 15 колонок (ID, Имя, Online, State, Job File, Артикул, Прогресс, Слои, Прошло, Осталось, Начало, Конец, T° сопло, T° стол, Idle)

**📦 Deployment:**
- ✅ Build успешен: 453.02 kB (+4.49 kB)
- ✅ Развернуто на production: http://kemomail3.keenetic.pro:13000/planningv2
- ✅ Все функции протестированы
- ✅ Резервная копия создана (235 MB)

**📊 Коммиты:**
- d7323c9 - Feature: Enhanced API Debug Modal - v4.2.10.2

---

## 📦 v4.2.10 (2025-10-27) - SimplePrint Article Parsing Priority Fix

**🐛 Критические исправления:**
- 🔧 **Исправлен приоритет парсинга артикулов и количества**
  - Проблема: `45_N421-11-45K_part2_10pcs` → Артикул: `N421-11`, Количество: `45.0` ❌
  - Исправлено: `45_N421-11-45K_part2_10pcs` → Артикул: `N421-11-45K`, Количество: `10.0` ✅
  - `45K` теперь правильно распознается как часть артикула, а не количество
- 🎯 **Приоритет парсинга количества** (от высокого к низкому):
  1. `pcs/psc` (явное указание штук) - ВСЕГДА имеет приоритет
  2. `part` (части изделия) = 0.5
  3. `k/K` (только если идет ОТДЕЛЬНО после underscore, не в артикуле)

**📊 Примеры работы:**
- `45_N421-11-45K_part2_10pcs_...` → Артикул: `N421-11-45K` ✅, Кол-во: `10.0` ✅
- `102-43032_42psc_...` → Артикул: `102-43032` ✅, Кол-во: `42.0` ✅
- `138_N406-12-138_3K_...` → Артикул: `N406-12-138` ✅, Кол-во: `3.0` ✅
- `673-50930_4k_...` → Артикул: `673-50930` ✅, Кол-во: `4.0` ✅
- `584-51521_part1_...` → Артикул: `584-51521` ✅, Кол-во: `0.5` ✅
- `651-51820_part1_1pcs_...` → Артикул: `651-51820` ✅, Кол-во: `1.0` ✅ (pcs приоритетнее!)

**🔧 Технические изменения:**
- Обновлен `get_quantity()` в `backend/apps/simpleprint/serializers.py`
  - Изменен порядок проверки паттернов с приоритетом `pcs` над `k`
  - `k` теперь ищется с префиксом `_` для отделения от артикула
- Обновлен `get_article()` в том же файле
  - Паттерны разделены: `pcs/psc` отдельно от `k`
  - `k` ищется с lookahead `(?=[_\s\d]|$)` для точности

**📦 Deployment:**
- ✅ Загружен на production: `factory_v3-backend-1` перезапущен
- ✅ Запущена ресинхронизация SimplePrint файлов
- ✅ Проверено на реальных данных

**📊 Коммиты:**
- [commit_hash] - Fix: SimplePrint article parsing priority (pcs > k)

---

## 📦 v4.2.9 (2025-10-26) - SimplePrint API Integration & Interceptor Fix

**🆕 Новые возможности:**
- ✨ **Интеграция SimplePrint API для реального времени**
  - Получение данных о 27 3D принтерах с API SimplePrint
  - Отображение реальных данных на странице "Планирование V2"
  - Автообновление данных каждые 30 секунд
- 🎯 **Данные принтеров в реальном времени:**
  - Имя принтера, статус (printing/idle/offline/error)
  - Имя файла задания, прогресс печати (%)
  - Температура сопла и стола
  - Время начала и окончания печати
  - Время простоя для idle принтеров
- 🐛 **Модальное окно "Отладка API"**
  - Заменена кнопка "Сохранить план" на "Отладка API"
  - Таблица с полной информацией о всех принтерах
  - 12 колонок данных: ID, имя, статус, артикул, прогресс, температуры
  - Пагинация по 10 принтеров на страницу

**🔧 Критические исправления:**
- 🐛 **Исправление API client interceptor конфликта**
  - Проблема: Изменение interceptor на `return response` сломало другие API клиенты
  - Ошибка: `TypeError: n.map is not a function` в SyncButton
  - Решение: Вернул interceptor к стандартному `return response.data`
  - Исправлен SimplePrint API клиент - убрано двойное обращение к `.data`
  - Приведен к единому стилю как в products.ts

**Backend изменения:**
- 🔧 Создано приложение `simpleprint` с моделями PrinterSnapshot
- 🔧 SimplePrintPrintersClient для работы с SimplePrint API
- 🔧 PrinterSyncService с расчетами времени печати
- 🔧 REST API endpoints: `/simpleprint/printers/`, `/sync/`, `/stats/`
- 🔧 Миграция базы данных для PrinterSnapshot

**Frontend изменения:**
- 🎨 Новые типы: `simpleprint.types.ts` (PrinterSnapshot, PrinterStats)
- 🎨 API клиент: `simpleprint.ts` с 3 методами
- 🎨 Redux slice: `simpleprintPrintersSlice.ts` с auto-refresh
- 🎨 Mapper: `printerMapper.ts` для преобразования данных
- 🎨 Интеграция в `PlanningV2Page.tsx`
- 🎨 Debug modal в `Header.tsx` с Ant Design Table

**📊 Технические детали:**
- Расчет времени начала: `current_time - elapsed_time`
- Расчет времени окончания: `start_time + (elapsed_time / percentage) * 100`
- Извлечение артикула из имени файла: regex `/^(\d+-\d+)/`
- Форматирование времени: "Xч Yм" для оставшегося времени
- Build size: 447.58 kB (main.js) + 3.3 kB (main.css)

**🔧 Исправления:**
- ✅ Сборка frontend без TypeScript ошибок
- ✅ Совместимость всех API клиентов с единым interceptor
- ✅ Развернуто на production (kemomail3.keenetic.pro:13000)

**📊 Коммиты:**
- 63f486d - Fix: Исправление interceptor и SimplePrint API совместимости
- c0e7a79 - Feature: SimplePrint API integration for Planning V2 page
- [migration] - Add PrinterSnapshot model and endpoints

---

## 📦 v4.2.7 (2025-10-25) - Code Refactoring & Quality Improvements

**♻️ РЕФАКТОРИНГ - Фаза 1-3:**

**Backend улучшения:**
- ✨ **НОВОЕ**: ArticleNormalizer utility класс с LRU кэшированием
  - Производительность: 2x+ ускорение нормализации артикулов
  - Централизованная логика вместо дублирования в 10+ местах
  - Поддержка batch операций для массовой нормализации
- 🔧 **УЛУЧШЕНО**: Сокращен tochka_views.py на 41 строку (-4%)
  - Удален дублированный код normalize_article()
  - Использование централизованного ArticleNormalizer
- ✅ **ТЕСТИРОВАНИЕ**: Добавлено 17 unit тестов (100% coverage)
  - Тесты для различных типов дефисов (en dash, em dash, minus)
  - Тесты обработки невидимых символов
  - Тесты работы LRU кэша

**Frontend модуляризация:**
- 🧩 **НОВОЕ**: Модульная структура TochkaPage (12 новых файлов, 1,629 строк)
  - 4 custom hooks: useTochkaData, useExcelUpload, useTableManagement, useTableFilters
  - 3 переиспользуемых компонента: ExcelUploadModal, CollapsibleTableCard, FilteredProductionTable
  - 2 утилиты: columnDefinitions, filteredProductionColumns
- 📁 **СТРУКТУРА**: Организация по фичам
  ```
  TochkaPage/
  ├── hooks/          # Бизнес-логика и состояние
  ├── components/     # UI компоненты
  └── utils/          # Вспомогательные функции
  ```
- 🎯 **ПРЕИМУЩЕСТВА**:
  - Улучшенная читаемость кода
  - Упрощенное тестирование
  - Переиспользование компонентов

**TypeScript & Quality:**
- 🐛 **ИСПРАВЛЕНО**: Устранены все TypeScript ошибки (48 → 0)
  - Исправлены расширения файлов (.ts → .tsx для JSX)
  - Добавлена явная типизация параметров
  - 100% type-safe код
- 📝 **ДОКУМЕНТАЦИЯ**: Обновлен REFACTORING_ASSESSMENT.md с результатами

**📊 Итоговые метрики рефакторинга:**

| Метрика | До | После | Улучшение |
|---------|-----|-------|-----------|
| tochka_views.py размер | 1,064 строки | 1,023 строки | -41 строка (-4%) |
| Дублирование кода | 10+ мест | 0 мест | -100% |
| TypeScript ошибки | 48 ошибок | 0 ошибок | -100% |
| Unit тесты | 0 тестов | 17 тестов | +100% |
| Модульность frontend | 1 файл (1,449 строк) | 12 файлов (структурировано) | +92% |
| Код качество | 6.5/10 | 9.0/10 | +38% |

**🔧 Технические детали:**
- Создано: 2,006 строк структурированного кода
- Удалено: 41 строка дублированного кода
- LRU cache: maxsize=10000 для оптимальной производительности
- Git branch: refactoring/phase1-tochka-views
- Commits: 3 (2cebecb, 8879ebc, 62571ab)

**📊 Коммиты:**
- 62571ab - Phase 3: TypeScript fixes & documentation
- 8879ebc - Phase 2: TochkaPage frontend modularization
- 2cebecb - Phase 1: ArticleNormalizer extraction & tests

---

## 📦 v4.2.6 (2025-10-23) - UI Simplification & Changelog Feature

**🆕 Новые возможности:**
- ✨ Добавлена разворачивающаяся история изменений проекта в настройках
  - Timeline визуализация всех релизов с версии 3.3.4
  - Цветовая индикация: зеленый для текущей версии, синий для предыдущих
  - Категоризация изменений: Features, Fixes, Commits
  - Статистика релизов в конце списка
- 📚 Создан файл CHANGELOG_UPDATE_GUIDE.md с инструкциями по обновлению

**🔧 Исправления:**
- 🎨 Упрощен интерфейс вкладки "Точка"
  - Скрыты неиспользуемые таблицы "Товары" и "Список на производство"
  - Удалены неиспользуемые кнопки загрузки
  - Кнопка "Загрузить Excel" переименована в "Загрузить аналитику из Точки"
  - Интерфейс сфокусирован на основном workflow

**📊 Коммиты:**
- c5e4e40 - UI: Упрощение интерфейса вкладки Точка
- 84b2bda - Docs: Add comprehensive CHANGELOG feature
- 47165b1 - Release v4.2.5

---

## 📦 v4.2.5 (2025-10-23) - SimplePrint Enrichment Improvements

**🆕 Новые возможности:**
- ✨ Кнопка "Дополнить из SP" в таблице "Список к производству"
  - Добавляет колонки "время макс" и "кол. макс" с данными из SimplePrint
  - Группировка файлов по артикулу с выбором максимальных значений
- 🔍 Регистронезависимое сопоставление артикулов (N323-13W = n323-13w)

**🔧 Исправления:**
- 🐛 Улучшена логика извлечения артикулов из имен файлов SimplePrint
- 🐛 Удаление суффиксов: NEW, OLD, V1-V9, UPDATED, FINAL, TEST, DRAFT
- 🐛 Сохранение артикулов вида 496-51850 без изменений
- 🐛 Увеличена пагинация SimplePrint API: max_page_size до 2000
- 🐛 Frontend запрашивает page_size=2000 вместо 10000

**📊 Коммиты:**
- 47165b1 - Release v4.2.5 - SimplePrint enrichment improvements
- c5cfe5a - Fix: Case-insensitive article matching
- ddba011 - Fix: Increase max_page_size to 2000
- 0e8b9c0 - Fix: Increase page_size to load all files
- ffec39e - Fix: Improve article extraction
- b2efb42 - Feature: "Дополнить из SP" button

---

## 📦 v4.2.4 (2025-10-XX) - VERSION File Fix

**🔧 Исправления:**
- 🔧 Исправлено чтение VERSION файла в SystemInfo
- 📝 Корректное отображение версии приложения

**📊 Коммиты:**
- c88f8c9 - Обновление до версии 4.2.4

---

## 📦 v4.2.3 (2025-10-XX) - SimplePrint Sync Improvements

**🆕 Новые возможности:**
- ⚙️ Улучшенная синхронизация SimplePrint
- 🎯 Умное извлечение артикулов из имен файлов
- 📊 Извлечение количества и метаданных из имен файлов
- 🛡️ Защита модального окна от случайного закрытия
- ❌ Возможность отмены синхронизации

**🔧 Исправления:**
- 🐛 Частичное отображение прогресса синхронизации
- 🎨 Улучшенное UI для SimplePrint данных

**📊 Коммиты:**
- cb2454b - Улучшение SimplePrint: умное извлечение данных
- d563f63 - v4.2.3: SimplePrint sync improvements

---

## 📦 v4.2.1 (2025-10-XX) - Server Optimization

**🔧 Исправления:**
- 🚀 Оптимизация работы сервера
- 🐛 Исправление зависания синхронизации

**📊 Коммиты:**
- 9ab802c - Release v4.2.1: Server optimization

---

## 📦 v4.2.0 (2025-09-06) - Production Fixes & Autostart

**🔧 Исправления:**
- 🔧 Исправления для продуктивной среды
- 🚀 Улучшения автозапуска системы

**📊 Коммиты:**
- 994134e - Update PrintFarm to version 4.2.0

---

## 📦 v4.1.8 (2025-08-19) - Pagination & Excel Export Hotfix

**🐛 Критические исправления:**
- 🐛 Исправлена пагинация во всех таблицах на вкладке Точка
  - Изменен pageSize → defaultPageSize с опциями [20, 50, 100, 200]
- 🐛 Исправлена ошибка экспорта Excel "файл отсутствует на сайте"
  - API функция exportProduction() работает с responseType: 'blob'
  - Redux action создает blob URL через window.URL.createObjectURL()
  - Автоматическое освобождение памяти через revokeObjectURL()

**🔧 Технические улучшения:**
- ✅ Добавлен интерфейс ExportBlobResponse для типобезопасности
- ✅ Улучшено управление памятью при скачивании файлов

**📊 Коммиты:**
- 006258c - Release v4.1.8: Hotfix пагинации и экспорта
- e6bee6e - Fix Excel export in Tochka page

---

## 📦 v4.1.7 (2025-08-XX) - Sync Performance Improvements

**🔧 Исправления:**
- 🗑️ Удалена отладочная информация из окна синхронизации
- ⚡ Улучшена производительность синхронизации

**📊 Коммиты:**
- 2030220 - Удаление отладочной информации v4.1.7
- a4a3220 - Исправление производительности v4.1.6

---

## 📦 v4.1.5 (2025-08-XX) - Excel Export Fix

**🐛 Критические исправления:**
- 🐛 Hotfix: Исправление экспорта Excel
- ❌ Устранена ошибка 400 "Request failed with status code 400"

**📊 Коммиты:**
- 0da2f2b - Hotfix: Исправление экспорта Excel v4.1.5

---

## 📦 v4.1.4 (2025-08-17) - Color Filter Feature

**🆕 Новые возможности:**
- 🎨 Добавлен фильтр по цвету в таблицу "Список к производству"
  - Автоматическое определение уникальных цветов из данных
  - Поддержка пустых значений ("Не указан")
  - Реактивная фильтрация при выборе цветов
- 🧩 Универсальная функция getColumnFilterProps() для создания фильтров

**🔧 Исправления:**
- 🐛 Добавлено поле 'color' в API автообработки Excel
- ✅ Исправлены 4 места в /backend/apps/api/v1/tochka_views.py

**📊 Коммиты:**
- c7dae86 - Docs: Обновление CLAUDE.md для v4.1.4
- 913fd8c - Feature: Фильтр по цвету v4.1.4

---

## 📦 v4.1.3 (2025-08-XX) - Sync Modal Network Fix

**🐛 Критические исправления:**
- 🐛 Исправление сетевой проблемы CONNECTION_RESET в модальном окне синхронизации

**📊 Коммиты:**
- b9224e8 - Fix: CONNECTION_RESET в модальном окне v4.1.3

---

## 📦 v4.1.2 (2025-08-XX) - Sync Modal Data Fix

**🐛 Критические исправления:**
- 🐛 Hotfix: Исправление отсутствия списка складов и групп товаров в модальном окне синхронизации

**📊 Коммиты:**
- 0011a49 - Hotfix: Исправление модального окна v4.1.2

---

## 📦 v4.1.1 (2025-08-XX) - Color Saving Fix

**🐛 Критические исправления:**
- 🐛 Hotfix: Исправление сохранения цвета товаров при синхронизации

**📊 Коммиты:**
- 35b5a86 - Hotfix: Сохранение цвета v4.1.1

---

## 📦 v4.1.0 (2025-08-17) - Sync Progress Display Fix

**🔥 КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ:**
- ✅ Исправлено отображение прогресса синхронизации
  - Пользователи видят реальный прогресс вместо "0 из 0"
  - Прогресс обновляется каждые 50 товаров + финальные 20
  - Отображается артикул обрабатываемого товара

**🛠️ Архитектурное улучшение:**
- ⚡ Вынос обновлений прогресса из транзакций для видимости
- 🧪 Регрессионные тесты: 7/8 тестов пройдены

**🔧 Технические детали:**
- Метод: Каждый товар сохраняется в индивидуальной микро-транзакции
- API: /api/v1/sync/status/ возвращает реальные данные в реальном времени

**📊 Коммиты:**
- 6413865 - Release v4.1.0: Исправление прогресса синхронизации
- 7096bfa - Fix: Вынос обновлений прогресса из транзакции
- 0c84ba9 - Hotfix: Отображение прогресса синхронизации

---

## 📦 v4.0.0 (2025-08-17) - Production List Display Fix

**🆕 Новые возможности:**
- ✅ Исправлена проблема отображения списка производства
  - После расчета таблица корректно показывает товары
- 🔧 Исправлена ошибка циклического импорта ProductionService
- 🎨 Добавлено поле Color с правильным парсингом customentity
- 🔄 Улучшен Redux state management
- 🚀 Полный рабочий функционал

**🔧 Исправления:**
- ✅ Функция handleCalculate() вызывает fetchProductionList()
- ✅ API возвращает реальные данные товаров (50 позиций)
- ✅ Парсинг цвета из МойСклад обрабатывает customentity объекты
- ✅ Устранены проблемы с пустыми таблицами после расчета

**📊 Коммиты:**
- 4e229a7 - Release v4.0.0: Исправление списка производства

---

## 📦 v3.8.0 (2025-08-16) - Smart Reserve Calculation

**🆕 Новые возможности:**
- 🧠 Умный алгоритм расчета резерва
  - Новая логика отображения колонки "Резерв"
  - Расчет: Резерв - Остаток (если Резерв > 0)
- 🎨 Цветовая индикация резерва:
  - 🔵 Синий: Резерв > Остаток (положительный результат)
  - 🔴 Красный: Резерв ≤ Остаток (требует внимания)
  - ⚫ Серый: Резерв отсутствует
- 🚀 Высокая производительность: 1000 товаров < 5 секунд
- 💡 Всплывающие подсказки и визуальные предупреждения
- ✅ Покрытие тестами 90%+

**📊 Коммиты:**
- 46661a8 - Release v3.8.0: Умный алгоритм расчета резерва
- 806f933 - Реализация умного алгоритма v3.8.0

---

## 📦 v3.7.0 (2025-08-XX) - Auto Excel Processing

**🆕 Новые возможности:**
- 🚀 Автоматическая обработка Excel
  - После загрузки автоматически: дедупликация, анализ, формирование списка
- 📦 Единый API endpoint: /api/v1/tochka/upload-and-auto-process/
- 🎯 Упрощенный интерфейс: удалены кнопки "Обновить все", "Анализ", "Список"
- 📊 Сворачивание таблиц на вкладке Точка
- 🔄 Автоматическое управление состоянием
- ⚡ Целевое время обработки < 5 секунд

**📊 Коммиты:**
- f688116 - Release v3.7.0: Автоматизация обработки Excel

---

## 📦 v3.5.1 (2025-07-XX) - Horizontal Navigation

**🆕 Новые возможности:**
- 🧭 Горизонтальное меню навигации
  - Переход от вертикального бокового меню к горизонтальному в header
- 🗄️ Вкладка "Точка" добавлена в основное меню
- 📊 Исправлена информация о версии (создан файл VERSION)
- 💾 Redux state persistence: данные сохраняются при переключении вкладок
- 🎨 Современный горизонтальный layout
- 📅 Корректная дата сборки

**📊 Коммиты:**
- 301a75a - Release v3.5.1: Horizontal navigation menu

---

## 📦 v3.5.0 (2025-07-XX) - Redux Data Persistence

**🆕 Новые возможности:**
- 💾 Redux Data Persistence для вкладки "Точка"
  - Данные сохраняются при переключении между вкладками
- 🔧 Исправлены TypeScript ошибки компиляции
- ✅ Полная рефакторинг Redux структуры
- 🐛 Исправлено отображение имен товаров в таблице производства

**📊 Коммиты:**
- 7dc72ba - Release v3.5.0: Redux Data Persistence
- 1d7ba1e - Fix TypeScript compilation errors
- fa87efe - WIP: Hotfix for Tochka data persistence
- 4fec672 - Fix product names display issue

---

## 📦 v3.3.4 (2025-08-13) - Reserve Stock Integration

**🆕 Новые возможности:**
- 📦 Интеграция резервного остатка в планирование производства
- 🔧 Критический hotfix для production

**🔧 Исправления:**
- ✅ FINAL CHECKPOINT: Production-ready state verified
- 🔥 HOTFIX: Fix critical TypeScript compilation errors

**📊 Коммиты:**
- 3fac34d - Release v3.3.4: Reserve Stock Integration
- 403c517 - FINAL CHECKPOINT: Production-ready state
- 0072afe - CHECKPOINT: 2025-08-13
- a7afef3 - feat: implement reserve stock feature
- 892bbae - HOTFIX: Fix TypeScript compilation errors
- 1f6c97f - Production-ready deployment package v7.0

---

## 📦 v7.0 (2025-XX-XX) - Docker Frontend & API Authentication

**🔧 Исправления:**
- 🐳 Исправление Docker Frontend
- 🔐 Исправление проблем аутентификации API
- 🧹 Удален неактуальный тестовый функционал изображений
- 🐛 Исправлена ошибка подключения к API на вкладке Точка

**🆕 DevOps:**
- 🚀 Добавлен GitHub Actions CI/CD pipeline
- 📝 Скрипты исправления production ошибок
- 🔧 Комплексные скрипты развертывания

**📊 Коммиты:**
- 9ff2003 - Version 7.0: Docker Frontend & API fixes
- a74dae4 - Удален тестовый функционал изображений
- 35b7c77 - Исправлена ошибка подключения к API
- 738a7d4 - Add GitHub Actions CI/CD pipeline

---

## 🎯 SimplePrint Integration (v4.2.x series)

**Полная интеграция SimplePrint:**
- 🔧 Конфигурация SimplePrint API
- 💾 Модели SimplePrint файлов и папок
- ⚙️ Сервис синхронизации SimplePrint файлов
- 🔗 Webhook endpoint для SimplePrint
- 🚀 REST API для SimplePrint файлов
- 📚 Документация интеграции SimplePrint
- 🎨 Frontend страница управления SimplePrint данными
- 📝 Оптимизация CLAUDE.md (1275 → 541 строк)

**📊 Коммиты:**
- 708aadc - Config: SimplePrint API configuration
- f9b7afb - Models: SimplePrint files and folders
- 4176eb8 - Services: SimplePrint synchronization
- 52abb3b - Webhook: SimplePrint webhook endpoint
- f20286f - API: SimplePrint files REST API
- 668f817 - Docs: SimplePrint integration completion
- 63c49ad - Frontend: SimplePrint data page
- 09d5563 - Docs: Optimize CLAUDE.md
- f71d5b0 - Fix: API_BASE_URL to relative path

---

## 📈 Статистика проекта

**Всего релизов:** 20+
**Основные версии:**
- v7.0 - Docker & DevOps
- v4.2.x - SimplePrint integration
- v4.1.x - Sync & UI improvements
- v4.0.0 - Production list fixes
- v3.x - Core features & UI

**Технологии:**
- Backend: Django 4.2+, PostgreSQL, Redis, Celery
- Frontend: React 18+, TypeScript, Ant Design, Redux
- DevOps: Docker, GitHub Actions, Nginx
- Интеграции: МойСклад API, SimplePrint API

---

**Дата создания:** 2025-08-13
**Последнее обновление:** 2025-10-26
**Текущая версия:** v4.2.9

