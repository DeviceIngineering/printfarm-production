/**
 * Changelog data for PrintFarm system
 * Generated from CHANGELOG.md
 */

export interface ChangelogEntry {
  version: string;
  date: string;
  title: string;
  features?: string[];
  fixes?: string[];
  commits?: string[];
}

export const CHANGELOG: ChangelogEntry[] = [
  {
    version: "4.2.5",
    date: "2025-10-23",
    title: "SimplePrint Enrichment Improvements",
    features: [
      "Кнопка \"Дополнить из SP\" в таблице \"Список к производству\"",
      "Добавляет колонки \"время макс\" и \"кол. макс\" с данными из SimplePrint",
      "Группировка файлов по артикулу с выбором максимальных значений",
      "Регистронезависимое сопоставление артикулов (N323-13W = n323-13w)"
    ],
    fixes: [
      "Улучшена логика извлечения артикулов из имен файлов SimplePrint",
      "Удаление суффиксов: NEW, OLD, V1-V9, UPDATED, FINAL, TEST, DRAFT",
      "Сохранение артикулов вида 496-51850 без изменений",
      "Увеличена пагинация SimplePrint API: max_page_size до 2000",
      "Frontend запрашивает page_size=2000 вместо 10000"
    ],
    commits: [
      "47165b1 - Release v4.2.5 - SimplePrint enrichment improvements",
      "c5cfe5a - Fix: Case-insensitive article matching",
      "ddba011 - Fix: Increase max_page_size to 2000"
    ]
  },
  {
    version: "4.2.4",
    date: "2025-10-XX",
    title: "VERSION File Fix",
    fixes: [
      "Исправлено чтение VERSION файла в SystemInfo",
      "Корректное отображение версии приложения"
    ],
    commits: [
      "c88f8c9 - Обновление до версии 4.2.4"
    ]
  },
  {
    version: "4.2.3",
    date: "2025-10-XX",
    title: "SimplePrint Sync Improvements",
    features: [
      "Улучшенная синхронизация SimplePrint",
      "Умное извлечение артикулов из имен файлов",
      "Извлечение количества и метаданных из имен файлов",
      "Защита модального окна от случайного закрытия",
      "Возможность отмены синхронизации"
    ],
    fixes: [
      "Частичное отображение прогресса синхронизации",
      "Улучшенное UI для SimplePrint данных"
    ],
    commits: [
      "cb2454b - Улучшение SimplePrint: умное извлечение данных",
      "d563f63 - v4.2.3: SimplePrint sync improvements"
    ]
  },
  {
    version: "4.2.1",
    date: "2025-10-XX",
    title: "Server Optimization",
    fixes: [
      "Оптимизация работы сервера",
      "Исправление зависания синхронизации"
    ],
    commits: [
      "9ab802c - Release v4.2.1: Server optimization"
    ]
  },
  {
    version: "4.2.0",
    date: "2025-09-06",
    title: "Production Fixes & Autostart",
    fixes: [
      "Исправления для продуктивной среды",
      "Улучшения автозапуска системы"
    ],
    commits: [
      "994134e - Update PrintFarm to version 4.2.0"
    ]
  },
  {
    version: "4.1.8",
    date: "2025-08-19",
    title: "Pagination & Excel Export Hotfix",
    fixes: [
      "Исправлена пагинация во всех таблицах на вкладке Точка",
      "Изменен pageSize → defaultPageSize с опциями [20, 50, 100, 200]",
      "Исправлена ошибка экспорта Excel \"файл отсутствует на сайте\"",
      "API функция exportProduction() работает с responseType: 'blob'",
      "Redux action создает blob URL через window.URL.createObjectURL()",
      "Автоматическое освобождение памяти через revokeObjectURL()",
      "Добавлен интерфейс ExportBlobResponse для типобезопасности",
      "Улучшено управление памятью при скачивании файлов"
    ],
    commits: [
      "006258c - Release v4.1.8: Hotfix пагинации и экспорта",
      "e6bee6e - Fix Excel export in Tochka page"
    ]
  },
  {
    version: "4.1.4",
    date: "2025-08-17",
    title: "Color Filter Feature",
    features: [
      "Добавлен фильтр по цвету в таблицу \"Список к производству\"",
      "Автоматическое определение уникальных цветов из данных",
      "Поддержка пустых значений (\"Не указан\")",
      "Реактивная фильтрация при выборе цветов",
      "Универсальная функция getColumnFilterProps() для создания фильтров"
    ],
    fixes: [
      "Добавлено поле 'color' в API автообработки Excel",
      "Исправлены 4 места в /backend/apps/api/v1/tochka_views.py"
    ],
    commits: [
      "913fd8c - Feature: Фильтр по цвету v4.1.4"
    ]
  },
  {
    version: "4.1.0",
    date: "2025-08-17",
    title: "Sync Progress Display Fix",
    features: [
      "Исправлено отображение прогресса синхронизации",
      "Пользователи видят реальный прогресс вместо \"0 из 0\"",
      "Прогресс обновляется каждые 50 товаров + финальные 20",
      "Отображается артикул обрабатываемого товара",
      "Вынос обновлений прогресса из транзакций для видимости",
      "Регрессионные тесты: 7/8 тестов пройдены",
      "API /api/v1/sync/status/ возвращает реальные данные в реальном времени"
    ],
    commits: [
      "6413865 - Release v4.1.0: Исправление прогресса синхронизации",
      "7096bfa - Fix: Вынос обновлений прогресса из транзакции"
    ]
  },
  {
    version: "4.0.0",
    date: "2025-08-17",
    title: "Production List Display Fix",
    features: [
      "Исправлена проблема отображения списка производства",
      "После расчета таблица корректно показывает товары",
      "Исправлена ошибка циклического импорта ProductionService",
      "Добавлено поле Color с правильным парсингом customentity",
      "Улучшен Redux state management",
      "Полный рабочий функционал"
    ],
    fixes: [
      "Функция handleCalculate() вызывает fetchProductionList()",
      "API возвращает реальные данные товаров (50 позиций)",
      "Парсинг цвета из МойСклад обрабатывает customentity объекты",
      "Устранены проблемы с пустыми таблицами после расчета"
    ],
    commits: [
      "4e229a7 - Release v4.0.0: Исправление списка производства"
    ]
  },
  {
    version: "3.8.0",
    date: "2025-08-16",
    title: "Smart Reserve Calculation",
    features: [
      "Умный алгоритм расчета резерва",
      "Новая логика отображения колонки \"Резерв\"",
      "Расчет: Резерв - Остаток (если Резерв > 0)",
      "Цветовая индикация: Синий (Резерв > Остаток), Красный (Резерв ≤ Остаток), Серый (отсутствует)",
      "Высокая производительность: 1000 товаров < 5 секунд",
      "Всплывающие подсказки и визуальные предупреждения",
      "Покрытие тестами 90%+"
    ],
    commits: [
      "46661a8 - Release v3.8.0: Умный алгоритм расчета резерва",
      "806f933 - Реализация умного алгоритма v3.8.0"
    ]
  },
  {
    version: "3.7.0",
    date: "2025-08-XX",
    title: "Auto Excel Processing",
    features: [
      "Автоматическая обработка Excel",
      "После загрузки автоматически: дедупликация, анализ, формирование списка",
      "Единый API endpoint: /api/v1/tochka/upload-and-auto-process/",
      "Упрощенный интерфейс: удалены кнопки \"Обновить все\", \"Анализ\", \"Список\"",
      "Сворачивание таблиц на вкладке Точка",
      "Автоматическое управление состоянием",
      "Целевое время обработки < 5 секунд"
    ],
    commits: [
      "f688116 - Release v3.7.0: Автоматизация обработки Excel"
    ]
  },
  {
    version: "3.5.1",
    date: "2025-07-XX",
    title: "Horizontal Navigation",
    features: [
      "Горизонтальное меню навигации",
      "Переход от вертикального бокового меню к горизонтальному в header",
      "Вкладка \"Точка\" добавлена в основное меню",
      "Исправлена информация о версии (создан файл VERSION)",
      "Redux state persistence: данные сохраняются при переключении вкладок",
      "Современный горизонтальный layout",
      "Корректная дата сборки"
    ],
    commits: [
      "301a75a - Release v3.5.1: Horizontal navigation menu"
    ]
  },
  {
    version: "3.5.0",
    date: "2025-07-XX",
    title: "Redux Data Persistence",
    features: [
      "Redux Data Persistence для вкладки \"Точка\"",
      "Данные сохраняются при переключении между вкладками",
      "Исправлены TypeScript ошибки компиляции",
      "Полная рефакторинг Redux структуры",
      "Исправлено отображение имен товаров в таблице производства"
    ],
    commits: [
      "7dc72ba - Release v3.5.0: Redux Data Persistence",
      "1d7ba1e - Fix TypeScript compilation errors"
    ]
  },
  {
    version: "3.3.4",
    date: "2025-08-13",
    title: "Reserve Stock Integration",
    features: [
      "Интеграция резервного остатка в планирование производства",
      "Критический hotfix для production",
      "FINAL CHECKPOINT: Production-ready state verified",
      "HOTFIX: Fix critical TypeScript compilation errors"
    ],
    commits: [
      "3fac34d - Release v3.3.4: Reserve Stock Integration",
      "403c517 - FINAL CHECKPOINT: Production-ready state",
      "a7afef3 - feat: implement reserve stock feature"
    ]
  },
  {
    version: "7.0",
    date: "2025-XX-XX",
    title: "Docker Frontend & API Authentication",
    features: [
      "Исправление Docker Frontend",
      "Исправление проблем аутентификации API",
      "Удален неактуальный тестовый функционал изображений",
      "Исправлена ошибка подключения к API на вкладке Точка",
      "Добавлен GitHub Actions CI/CD pipeline",
      "Скрипты исправления production ошибок",
      "Комплексные скрипты развертывания"
    ],
    commits: [
      "9ff2003 - Version 7.0: Docker Frontend & API fixes",
      "738a7d4 - Add GitHub Actions CI/CD pipeline"
    ]
  }
];
