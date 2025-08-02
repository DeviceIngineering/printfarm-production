#!/bin/bash

# PrintFarm Production - Скрипт диагностики
# Собирает информацию о состоянии системы

echo "🔍 Диагностическая информация PrintFarm Production v4.6"
echo "======================================================="
echo
echo "Дата создания отчета: $(date)"
echo "Пользователь: $(whoami)"
echo "Система: $(lsb_release -d 2>/dev/null || echo 'Неизвестно')"
echo "Архитектура: $(uname -m)"
echo

echo "Docker версия:"
echo "=============="
docker --version 2>/dev/null || echo "Docker не установлен"
echo

echo "Docker Compose версия:"
echo "====================="
docker-compose --version 2>/dev/null || echo "Docker Compose не установлен"
echo

echo "Статус контейнеров:"
echo "==================="
if [[ -f "docker-compose.prod.yml" ]]; then
    docker-compose -f docker-compose.prod.yml ps
else
    echo "Файл docker-compose.prod.yml не найден"
fi
echo

echo "Использование ресурсов контейнерами:"
echo "==================================="
docker stats --no-stream 2>/dev/null || echo "Не удается получить статистику Docker"
echo

echo "Место на диске:"
echo "==============="
df -h
echo

echo "Использование памяти:"
echo "===================="
free -h
echo

echo "Загрузка процессора:"
echo "==================="
top -bn1 | grep "Cpu(s)" || echo "Не удается получить информацию о CPU"
echo

echo "Сетевые подключения:"
echo "==================="
netstat -tlnp 2>/dev/null | grep -E ':(80|443|8000|5432|6379)' || echo "netstat недоступен"
echo

echo "Логи backend (последние 50 строк):"
echo "==================================="
if [[ -f "docker-compose.prod.yml" ]]; then
    docker-compose -f docker-compose.prod.yml logs --tail=50 backend 2>/dev/null || echo "Не удается получить логи backend"
else
    echo "docker-compose.prod.yml не найден"
fi
echo

echo "Логи nginx (последние 20 строк):"
echo "================================="
if [[ -f "docker-compose.prod.yml" ]]; then
    docker-compose -f docker-compose.prod.yml logs --tail=20 nginx 2>/dev/null || echo "Не удается получить логи nginx"
else
    echo "docker-compose.prod.yml не найден"
fi
echo

echo "Проверка доступности API:"
echo "========================="
if command -v curl &> /dev/null; then
    if curl -f -s http://localhost/api/v1/tochka/stats/ &> /dev/null; then
        echo "✅ API доступен"
    else
        echo "❌ API недоступен"
    fi
else
    echo "curl не установлен"
fi
echo

echo "Переменные окружения (.env файл):"
echo "================================="
if [[ -f ".env" ]]; then
    echo "✅ .env файл существует"
    echo "Переменные (без секретов):"
    grep -E '^[A-Z_]+=.+' .env | grep -v -E '(PASSWORD|SECRET|TOKEN)' | head -10
else
    echo "❌ .env файл не найден"
fi
echo

echo "Версия приложения (Git):"
echo "========================"
if [[ -d ".git" ]]; then
    echo "Текущая ветка: $(git branch --show-current 2>/dev/null || echo 'неизвестно')"
    echo "Последний коммит: $(git log -1 --oneline 2>/dev/null || echo 'неизвестно')"
    echo "Статус: $(git status --porcelain 2>/dev/null | wc -l) измененных файлов"
else
    echo "Не Git репозиторий"
fi
echo

echo "======================================================="
echo "Конец диагностического отчета"
echo "Для получения помощи отправьте этот отчет разработчикам"