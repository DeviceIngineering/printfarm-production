#!/bin/bash

# PrintFarm Production Status Script
# Быстрая проверка состояния системы

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

success() {
    echo -e "${GREEN}✅${NC} $1"
}

error() {
    echo -e "${RED}❌${NC} $1"
}

warning() {
    echo -e "${YELLOW}⚠️${NC} $1"
}

info() {
    echo -e "${BLUE}ℹ️${NC} $1"
}

echo -e "${BLUE}🔍 PrintFarm Production Status Check${NC}"
echo "=================================================="

# Версия
if [ -f "VERSION" ]; then
    VERSION=$(cat VERSION)
    info "Версия: $VERSION"
else
    warning "Файл VERSION не найден"
fi

echo ""

# Статус Docker контейнеров
echo -e "${BLUE}📦 Статус контейнеров:${NC}"
if command -v docker-compose &> /dev/null; then
    docker-compose ps
else
    error "docker-compose не найден"
fi

echo ""

# Проверка сервисов
echo -e "${BLUE}🌐 Проверка доступности сервисов:${NC}"

# Backend API
if curl -f -s http://localhost:8000/api/v1/settings/system-info/ > /dev/null 2>&1; then
    success "Backend API (http://localhost:8000)"
else
    error "Backend API недоступен"
fi

# Frontend
if curl -f -s http://localhost:3000/ > /dev/null 2>&1; then
    success "Frontend (http://localhost:3000)"
else
    error "Frontend недоступен"
fi

# Database
if docker-compose exec -T db pg_isready -U printfarm_user > /dev/null 2>&1; then
    success "PostgreSQL база данных"
else
    error "PostgreSQL база данных недоступна"
fi

# Redis
if docker-compose exec -T redis redis-cli ping | grep -q PONG > /dev/null 2>&1; then
    success "Redis"
else
    error "Redis недоступен"
fi

echo ""

# Использование диска
echo -e "${BLUE}💽 Использование диска:${NC}"
df -h . | tail -1 | awk '{print "  Использовано: " $3 " из " $2 " (" $5 ")"}'

# Использование памяти контейнерами
echo ""
echo -e "${BLUE}🧠 Использование памяти контейнерами:${NC}"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" | head -10

echo ""

# Последние логи
echo -e "${BLUE}📜 Последние события (логи):${NC}"
docker-compose logs --tail=5 backend 2>/dev/null | tail -5

echo ""
echo -e "${GREEN}✅ Проверка завершена${NC}"