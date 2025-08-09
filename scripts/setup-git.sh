#!/bin/bash

# Скрипт для подготовки Git репозитория и первоначальной загрузки

echo "=========================================="
echo "Подготовка Git репозитория"
echo "=========================================="

# Проверка, что мы в правильной директории
if [ ! -f "CLAUDE.md" ]; then
    echo "Ошибка: Запустите скрипт из корневой директории проекта (где есть CLAUDE.md)"
    exit 1
fi

# Инициализация Git репозитория если еще не создан
if [ ! -d ".git" ]; then
    echo "Инициализация Git репозитория..."
    git init
    git branch -M main
else
    echo "Git репозиторий уже существует"
fi

# Создание .gitignore если не существует
if [ ! -f ".gitignore" ]; then
    echo "Создание .gitignore..."
    cat > .gitignore << 'EOF'
# Environment files
.env
.env.local
.env.prod
.env.*.local

# Database
*.sqlite3
*.db

# Logs
logs/
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Dependencies
node_modules/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Docker
.dockerignore

# Media files
media/
static/

# Backups
backups/
*.sql

# Local development
docker-compose.override.yml
EOF
fi

# Добавление всех файлов
echo "Добавление файлов в Git..."
git add .

# Коммит изменений
echo "Создание коммита..."
git commit -m "Initial commit: PrintFarm Production System

- Added deployment scripts and Docker configs
- Production-ready setup with security considerations
- Complete documentation for server deployment" || echo "Нет изменений для коммита"

echo ""
echo "=========================================="
echo "Git репозиторий подготовлен!"
echo "=========================================="
echo ""
echo "Следующие шаги:"
echo ""
echo "1. Создайте репозиторий на GitHub:"
echo "   - Перейдите на https://github.com/new"
echo "   - Назовите репозиторий: printfarm-production"
echo "   - Сделайте его приватным"
echo "   - НЕ добавляйте README, .gitignore или лицензию"
echo ""
echo "2. Подключите удаленный репозиторий:"
echo "   git remote add origin https://github.com/ВАШЕ_ИМЯ/printfarm-production.git"
echo ""
echo "3. Загрузите код:"
echo "   git push -u origin main"
echo ""
echo "4. Обновите URL в scripts/deploy.sh"
echo ""
echo "Текущий статус Git:"
git status --porcelain
echo ""
git log --oneline -n 3 2>/dev/null || echo "Коммитов пока нет"