# Скрипт развертывания версии 3.1 на удаленном сервере

## 1. Подключение к серверу и обновление кода

```bash
# Подключение к серверу
ssh root@your-server-ip

# Переход в директорию проекта
cd /path/to/printfarm-production

# Остановка контейнеров
docker-compose down

# Обновление кода из репозитория
git fetch --all
git checkout v3.1

# Проверка статуса
git status
git log --oneline -5
```

## 2. Создание резервной копии

```bash
# Создание бэкапа базы данных
docker-compose exec db pg_dump -U printfarm_user printfarm_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Создание бэкапа media файлов
tar -czf media_backup_$(date +%Y%m%d_%H%M%S).tar.gz backend/media/
```

## 3. Применение миграций

```bash
# Запуск только базы данных
docker-compose up -d db redis

# Применение новых миграций (для monitoring app)
docker-compose run --rm backend python manage.py makemigrations monitoring
docker-compose run --rm backend python manage.py migrate

# Сбор статики
docker-compose run --rm backend python manage.py collectstatic --noinput
```

## 4. Запуск обновленной системы

```bash
# Перезапуск всех сервисов
docker-compose up --build -d

# Проверка статуса контейнеров
docker-compose ps

# Проверка логов
docker-compose logs -f --tail=50
```

## 5. Проверка работоспособности

```bash
# Проверка API endpoints
curl -X GET http://localhost:8000/api/v1/products/ | head
curl -X GET http://localhost:8000/api/v1/sync/warehouses/
curl -X GET http://localhost:8000/api/v1/sync/product-groups/

# Проверка health check (если monitoring включен)
# curl -X GET http://localhost:8000/api/v1/monitoring/health/

# Запуск тестов для проверки алгоритма
# docker-compose -f docker-compose.test.yml run --rm test-runner
```

## 6. Настройка мониторинга (опционально)

```bash
# Включение monitoring URLs (если нужно)
# Раскомментировать строку в backend/apps/api/v1/urls.py:
# path('monitoring/', include('apps.monitoring.urls')),

# Запуск setup команды для мониторинга
docker-compose exec backend python manage.py setup_monitoring

# Настройка Celery Beat для периодических задач
docker-compose restart celery-beat
```

## 7. Проверка алгоритма производства

```bash
# Проверка расчета для тестовых товаров
docker-compose exec backend python manage.py shell << EOF
from apps.products.models import Product
from decimal import Decimal

# Проверка товара 375-42108
try:
    product = Product.objects.get(article='375-42108')
    product.current_stock = Decimal('2')
    product.sales_last_2_months = Decimal('10')
    product.update_calculated_fields()
    print(f"375-42108: stock={product.current_stock}, sales={product.sales_last_2_months}, needed={product.production_needed}")
except Product.DoesNotExist:
    print("Товар 375-42108 не найден")

# Проверка товара 381-40801
try:
    product = Product.objects.get(article='381-40801')
    product.current_stock = Decimal('8')
    product.sales_last_2_months = Decimal('2')
    product.update_calculated_fields()
    print(f"381-40801: stock={product.current_stock}, sales={product.sales_last_2_months}, needed={product.production_needed}")
except Product.DoesNotExist:
    print("Товар 381-40801 не найден")
EOF
```

## 8. Откат к предыдущей версии (в случае проблем)

```bash
# Остановка сервисов
docker-compose down

# Возврат к предыдущему коммиту
git checkout main~1

# Восстановление базы из бэкапа (если нужно)
# docker-compose up -d db
# docker-compose exec -T db psql -U printfarm_user printfarm_db < backup_YYYYMMDD_HHMMSS.sql

# Запуск старой версии
docker-compose up --build -d
```

## Примечания

1. **Новые функции в версии 3.1**:
   - Исправленный алгоритм производства для низкооборотных товаров
   - Полный набор тестов
   - Система мониторинга (опционально)
   - CI/CD pipeline через GitHub Actions

2. **Важно**: Система мониторинга по умолчанию отключена в URLs для стабильности. Включайте только после тестирования.

3. **Тестирование**: Запуск production тестов через `./run-production-tests.sh` можно выполнить для полной проверки.

4. **Безопасность**: Все секретные данные должны быть в `.env` файле на сервере.