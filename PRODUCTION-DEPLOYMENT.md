# PrintFarm Production Deployment Guide

## 🚀 Production Testing & CI/CD Implementation

Этот документ описывает полноценную систему production тестирования, CI/CD pipeline и мониторинга для PrintFarm.

---

## 📋 Содержание

1. [Docker Production Testing](#docker-production-testing)
2. [CI/CD Pipeline (GitHub Actions)](#cicd-pipeline)
3. [Monitoring & Alerts System](#monitoring--alerts-system)
4. [Health Checks](#health-checks)
5. [Deployment Commands](#deployment-commands)
6. [Troubleshooting](#troubleshooting)

---

## 🐳 Docker Production Testing

### Файлы конфигурации:
- `docker-compose.test.yml` - Тестовая среда с PostgreSQL и Redis
- `run-production-tests.sh` - Скрипт для запуска production тестов

### Запуск тестов:

```bash
# Полный набор тестов
./run-production-tests.sh all

# Только unit тесты
./run-production-tests.sh unit

# Только интеграционные тесты
./run-production-tests.sh integration

# Анализ покрытия кода
./run-production-tests.sh coverage

# Тесты производительности
./run-production-tests.sh performance

# Health checks
./run-production-tests.sh health
```

### Особенности тестовой среды:
- ✅ Изолированная PostgreSQL база данных
- ✅ Отдельный Redis для тестов
- ✅ Health checks для всех сервисов
- ✅ Автоматическая очистка после тестов
- ✅ Генерация отчетов в `test-reports/`

---

## 🔄 CI/CD Pipeline

### GitHub Actions Workflows:

#### 1. Основной CI Pipeline (`.github/workflows/ci.yml`)

**Триггеры:**
- Push в `main`, `develop`, `feature/*`
- Pull requests в `main`, `develop`  
- Ежедневно в 6:00 UTC

**Этапы:**
1. **Code Quality & Security**
   - Black форматирование
   - isort сортировка импортов
   - flake8 линтинг
   - Bandit безопасность
   - Safety проверка зависимостей

2. **Test Suite**
   - Unit тесты алгоритма
   - API тесты
   - Scenario тесты
   - Покрытие кода (Codecov)

3. **Docker Integration**
   - Сборка Docker образов
   - Интеграционные тесты в контейнерах

4. **Performance Testing** (только main branch)
   - Нагрузочные тесты с 1000+ товаров
   - Проверка времени выполнения алгоритма

5. **Algorithm Change Detection**
   - Автоматическое обнаружение изменений в алгоритме
   - Регрессионные тесты при изменениях
   - Уведомления в PR

6. **Deployment**
   - Staging: автоматически из `develop`
   - Production: автоматически из `main`

#### 2. Мониторинг Pipeline (`.github/workflows/monitoring.yml`)

**Триггеры:**
- Каждые 6 часов
- Ручной запуск

**Проверки:**
- ✅ Health check API endpoints
- ✅ Database и Redis connectivity  
- ✅ Algorithm regression tests
- ✅ Performance benchmarks
- ✅ Data integrity checks

---

## 📊 Monitoring & Alerts System

### Компоненты системы:

#### 1. Модели мониторинга (`apps/monitoring/models.py`)
- `AlgorithmExecution` - Трекинг выполнения алгоритма
- `AlgorithmBaseline` - Базовые тест-кейсы для регрессии
- `AlgorithmAlert` - Система алертов
- `SystemHealth` - Метрики здоровья системы
- `ProductionListAudit` - Аудит изменений списков производства

#### 2. Сервисы мониторинга (`apps/monitoring/services.py`)
- `AlgorithmMonitor` - Мониторинг алгоритма и регрессионные тесты
- `SystemHealthMonitor` - Мониторинг системного здоровья

#### 3. API Endpoints (`/api/v1/monitoring/`)
- `GET /health/` - Базовый health check для load balancers
- `GET /health/detailed/` - Детальные метрики системы
- `POST /algorithm/regression-test/` - Ручной запуск регрессионных тестов
- `GET /dashboard/` - Данные для monitoring dashboard
- `POST /webhook/alert/` - Webhook для внешних алертов

#### 4. Celery Tasks (Периодические задачи)
- **Каждые 5 минут:** Сбор метрик здоровья системы
- **Каждый час:** Регрессионные тесты алгоритма
- **Каждые 4 часа:** Анализ трендов производительности
- **Ежедневно в 9:00:** Отчет о мониторинге
- **Ежедневно в 2:00:** Очистка старых данных мониторинга

### Типы алертов:

#### 🚨 Critical Alerts
- Algorithm regression detected
- API response time > 2 seconds
- Memory usage > 95%
- System health score < 50%

#### ⚠️ Warning Alerts
- Performance degradation trends
- High error rates
- Resource usage approaching limits

#### 📧 Notification Channels
- Slack webhooks
- Email alerts
- GitHub PR comments (для изменений алгоритма)

---

## 💓 Health Checks

### Endpoints для мониторинга:

```bash
# Базовый health check (для load balancers)
curl http://your-domain.com/api/v1/monitoring/health/

# Детальные метрики
curl http://your-domain.com/api/v1/monitoring/health/detailed/

# Dashboard данные
curl http://your-domain.com/api/v1/monitoring/dashboard/
```

### Проверяемые компоненты:
- ✅ API response time
- ✅ Database connectivity & performance  
- ✅ Redis connectivity & memory usage
- ✅ System resources (CPU, Memory, Disk)
- ✅ Algorithm execution performance
- ✅ Production calculation accuracy

---

## 🛠 Deployment Commands

### Инициализация мониторинга:

```bash
# Создать базовые тест-кейсы
python manage.py setup_monitoring --create-baselines

# Запустить health check
python manage.py setup_monitoring --run-health-check

# Запустить регрессионные тесты  
python manage.py setup_monitoring --run-regression-test
```

### Production тестирование:

```bash
# Полное тестирование с Docker
./run-production-tests.sh all

# Только критичные тесты
./run-production-tests.sh unit && ./run-production-tests.sh integration
```

### Мониторинг в production:

```bash
# Запуск Celery worker для мониторинга
celery -A config worker -l info -Q monitoring

# Запуск Celery beat для периодических задач
celery -A config beat -l info
```

---

## 🔧 Configuration

### Environment Variables:

```bash
# Мониторинг и алерты
SLACK_WEBHOOK_URL=https://hooks.slack.com/your-webhook
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/your-webhook
EMAIL_ALERTS_ENABLED=true
ALERT_EMAIL_RECIPIENTS=alerts@company.com,dev-team@company.com

# Health checks
HEALTH_CHECK_TIMEOUT=30
PERFORMANCE_THRESHOLD_MS=1000
MEMORY_ALERT_THRESHOLD=80

# Algorithm monitoring
ALGORITHM_REGRESSION_ENABLED=true
BASELINE_TEST_FREQUENCY=3600  # seconds
```

### Slack Integration:

```bash
# Настройка Slack webhook для алертов
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
```

---

## 🚨 Alert Examples

### Algorithm Regression Alert:
```json
{
  "severity": "critical",
  "title": "Algorithm Regression Detected",
  "description": "Production algorithm calculation changed for test case 375-42108",
  "details": {
    "test_case": "375-42108",
    "expected_production": 8,
    "actual_production": 6,
    "difference": -2
  }
}
```

### Performance Degradation Alert:
```json
{
  "severity": "medium", 
  "title": "Algorithm Performance Degradation",
  "description": "Batch recalculation time increased from 5.2s to 8.7s",
  "details": {
    "execution_type": "batch_recalculation",
    "old_average": 5.2,
    "new_average": 8.7,
    "degradation_percent": 67.3
  }
}
```

---

## 📈 Monitoring Dashboard

### Key Metrics:
- **System Health Score** (0-100%)
- **Algorithm Execution Time** trends
- **API Response Times**
- **Active Alerts** count
- **Production Calculation Accuracy**
- **Resource Usage** (CPU, Memory, Disk)

### Access:
```bash
# API endpoint для dashboard данных
GET /api/v1/monitoring/dashboard/

# Health check для load balancers
GET /api/v1/monitoring/health/
```

---

## 🔍 Troubleshooting

### Common Issues:

#### 1. Tests failing in CI
```bash
# Check logs
docker-compose -f docker-compose.test.yml logs backend-test

# Run locally
./run-production-tests.sh unit
```

#### 2. Algorithm regression detected
```bash
# Check baseline tests
python manage.py setup_monitoring --run-regression-test

# Update baselines if algorithm intentionally changed
python manage.py setup_monitoring --create-baselines
```

#### 3. Performance alerts
```bash
# Check recent executions
curl http://your-domain.com/api/v1/monitoring/dashboard/

# Run performance test
./run-production-tests.sh performance
```

#### 4. Health check failures
```bash
# Detailed health info
curl http://your-domain.com/api/v1/monitoring/health/detailed/

# Manual health check
python manage.py setup_monitoring --run-health-check
```

---

## 📚 Files Reference

### Docker & Testing:
- `docker-compose.test.yml` - Test environment
- `run-production-tests.sh` - Production test runner

### CI/CD:
- `.github/workflows/ci.yml` - Main CI pipeline
- `.github/workflows/monitoring.yml` - Monitoring pipeline

### Monitoring System:
- `apps/monitoring/models.py` - Data models
- `apps/monitoring/services.py` - Business logic
- `apps/monitoring/views.py` - API endpoints
- `apps/monitoring/tasks.py` - Celery tasks
- `apps/monitoring/management/commands/setup_monitoring.py` - Setup command

### Configuration:
- `config/celery_monitoring.py` - Celery beat schedule
- `config/settings/test.py` - Test settings

---

## ✅ Production Readiness Checklist

- [x] **Docker Production Testing** - Полная изоляция и воспроизводимость
- [x] **CI/CD Pipeline** - Автоматические тесты и deployment
- [x] **Algorithm Monitoring** - Регрессионные тесты и change detection
- [x] **Performance Monitoring** - Трекинг производительности во времени
- [x] **Health Checks** - Мониторинг всех компонентов системы
- [x] **Alert System** - Уведомления о критичных изменениях
- [x] **Automated Reports** - Ежедневные отчеты о состоянии системы
- [x] **Data Integrity** - Проверка корректности расчетов
- [x] **Rollback Strategy** - Возможность быстрого отката при проблемах

**🎉 Система готова к production deployment!**