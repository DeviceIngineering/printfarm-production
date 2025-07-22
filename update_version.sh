#!/bin/bash

# Скрипт для обновления версии PrintFarm
# Usage: ./update_version.sh 3.1.2

set -e

VERSION=$1
CURRENT_DIR=$(pwd)

if [ -z "$VERSION" ]; then
    echo "❌ Использование: $0 <version>"
    echo "   Пример: $0 3.1.2"
    exit 1
fi

echo "🚀 Обновление версии PrintFarm до $VERSION"
echo "================================================"

# Функция для логирования
log() {
    echo "✅ $1"
}

warn() {
    echo "⚠️  $1"
}

# 1. Обновить файл VERSION
log "Обновление файла VERSION..."
echo "$VERSION" > VERSION

# 2. Обновить CLAUDE.md
log "Обновление документации CLAUDE.md..."
sed -i.bak "s/Версия [0-9]\+\.[0-9]\+\.[0-9]\+/Версия $VERSION/g" CLAUDE.md
sed -i.bak "s/v[0-9]\+\.[0-9]\+\.[0-9]\+/v$VERSION/g" CLAUDE.md
rm CLAUDE.md.bak 2>/dev/null || true

# 3. Обновить package.json во frontend
if [ -f "frontend/package.json" ]; then
    log "Обновление frontend/package.json..."
    sed -i.bak "s/\"version\": \"[0-9]\+\.[0-9]\+\.[0-9]\+\"/\"version\": \"$VERSION\"/g" frontend/package.json
    rm frontend/package.json.bak 2>/dev/null || true
fi

# 4. Проверить API
log "Проверка API системы..."
if command -v curl &> /dev/null; then
    if curl -s http://localhost:8000/api/v1/settings/system-info/ > /dev/null 2>&1; then
        API_VERSION=$(curl -s http://localhost:8000/api/v1/settings/system-info/ | python3 -c "import sys, json; print(json.load(sys.stdin)['version'])" 2>/dev/null || echo "unknown")
        log "Версия через API: $API_VERSION"
    else
        warn "Django сервер не запущен для проверки API"
    fi
else
    warn "curl не найден, пропускаем проверку API"
fi

# 5. Добавить изменения в git
log "Добавление изменений в git..."
git add VERSION CLAUDE.md frontend/package.json 2>/dev/null || true

# 6. Создать коммит
log "Создание коммита..."
git commit -m "🏷️ Обновление версии до $VERSION

✨ Изменения:
- Версия обновлена с помощью скрипта update_version.sh
- Обновлены VERSION, CLAUDE.md, package.json

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>" || warn "Нет изменений для коммита"

# 7. Создать git tag
log "Создание git tag v$VERSION..."
git tag -d "v$VERSION" 2>/dev/null || true
git tag -a "v$VERSION" -m "PrintFarm v$VERSION

🎯 Релиз версии $VERSION
- Автоматическое обновление версии
- Полнофункциональная система настроек
- Интеграция с MoySklad API
- Веб-интерфейс для управления

📋 Для обновления на сервере:
1. git pull origin main
2. git checkout v$VERSION
3. python backend/manage.py migrate
4. docker-compose restart

🔧 Доступ к настройкам:
- Веб: http://localhost:3000/settings  
- API: http://localhost:8000/api/v1/settings/summary/"

echo ""
log "🎉 Версия $VERSION успешно создана!"
log "📝 Команды для публикации:"
echo "   git push origin main"
echo "   git push origin v$VERSION"
echo ""
log "🌐 Проверка версии:"
echo "   curl http://localhost:8000/api/v1/settings/system-info/"
echo ""