#!/bin/bash

# PrintFarm - Fix media conflicts and update script
# Исправление конфликтов media файлов и обновление до v3.1

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ] || [ ! -d "backend" ]; then
    error "Не найден docker-compose.yml или директория backend"
    error "Запустите скрипт из корневой директории проекта PrintFarm"
    exit 1
fi

log "🔧 Исправление конфликтов media файлов..."

# Create backup of current media files before resolving conflicts
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
log "📦 Создание бэкапа текущих media файлов..."

if [ -d "backend/media" ]; then
    tar -czf "media_conflict_backup_${BACKUP_DATE}.tar.gz" backend/media/
    log "✅ Бэкап создан: media_conflict_backup_${BACKUP_DATE}.tar.gz"
fi

# Move conflicting files to a safe location
log "🚚 Перемещение конфликтующих файлов..."
mkdir -p "backup_media_conflicts_${BACKUP_DATE}"

# List of conflicting files from git error
CONFLICTING_FILES=(
    "backend/media/products/252-41411__WhatsApp_Image_2024-07-16_at_20.01.01.jpeg"
    "backend/media/products/283-41742_WhatsApp_Image_2025-07-18_at_11.12.40.jpeg"
    "backend/media/products/527-52721_WhatsApp_Image_2025-04-03_at_15.47.41.jpeg"
    "backend/media/products/527-52721_WhatsApp_Image_2025-04-03_at_15.48.16.jpeg"
    "backend/media/products/650-51736_WhatsApp_Image_2025-07-14_at_15.16.42.jpeg"
    "backend/media/products/654-52609_WhatsApp_Image_2025-07-14_at_15.41.40.jpeg"
    "backend/media/products/BATMAN161_Снимок_экрана_2023-11-11_173236.png"
    "backend/media/products/N422-11-161_WhatsApp_Image_2025-04-10_at_15.46.08.jpeg"
    "backend/media/products/scull-P_WhatsApp_Image_2023-11-11_at_14.22.29.jpeg"
    "backend/media/products/thumbnails/thumb_252-41411__WhatsApp_Image_2024-07-16_at_20.01.01.jpeg"
    "backend/media/products/thumbnails/thumb_283-41742_WhatsApp_Image_2025-07-18_at_11.12.40.jpeg"
    "backend/media/products/thumbnails/thumb_527-52721_WhatsApp_Image_2025-04-03_at_15.47.41.jpeg"
    "backend/media/products/thumbnails/thumb_527-52721_WhatsApp_Image_2025-04-03_at_15.48.16.jpeg"
    "backend/media/products/thumbnails/thumb_650-51736_WhatsApp_Image_2025-07-14_at_15.16.42.jpeg"
    "backend/media/products/thumbnails/thumb_654-52609_WhatsApp_Image_2025-07-14_at_15.41.40.jpeg"
    "backend/media/products/thumbnails/thumb_BATMAN161_Снимок_экрана_2023-11-11_173236.png"
    "backend/media/products/thumbnails/thumb_N422-11-161_WhatsApp_Image_2025-04-10_at_15.46.08.jpeg"
    "backend/media/products/thumbnails/thumb_scull-P_WhatsApp_Image_2023-11-11_at_14.22.29.jpeg"
)

# Move each conflicting file
for file in "${CONFLICTING_FILES[@]}"; do
    if [ -f "$file" ]; then
        # Create directory structure in backup
        backup_dir="backup_media_conflicts_${BACKUP_DATE}/$(dirname "$file")"
        mkdir -p "$backup_dir"
        
        # Move the file
        mv "$file" "$backup_dir/"
        log "✅ Перемещен: $file"
    else
        info "Файл не найден (возможно уже удален): $file"
    fi
done

# Now try to pull again
log "📥 Повторная попытка обновления кода..."
git pull origin main

log "✅ Код успешно обновлен!"

# Show current status
log "📋 Текущее состояние репозитория:"
git status

log "📊 Последние коммиты:"
git log --oneline -5

info "🔧 Конфликты разрешены. Теперь можно запускать update-server.sh"

# Check if update script exists
if [ -f "update-server.sh" ]; then
    log "✅ Скрипт update-server.sh найден"
    chmod +x update-server.sh
    log "🚀 Запуск автоматического обновления..."
    ./update-server.sh
else
    error "❌ Файл update-server.sh не найден после обновления"
    info "Попробуйте запустить: git checkout v3.1"
fi