#\!/bin/bash

# PrintFarm v3.3.4 - Rollback Script
# Usage: ./rollback.sh user@server-ip [backup-name]

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
PROJECT_NAME="printfarm-production"
REMOTE_DIR="/opt/$PROJECT_NAME"
BACKUP_DIR="/opt/backups/$PROJECT_NAME"
COMPOSE_FILE="docker-compose.server.prod.yml"

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

show_help() {
    cat << EOF
PrintFarm Production Rollback Script

Usage: $0 user@server-ip [backup-name]

EXAMPLES:
    $0 root@192.168.1.100                    # Rollback to latest backup
    $0 user@myserver.com backup-20250814     # Rollback to specific backup

DESCRIPTION:
    This script allows you to rollback to a previous deployment.
    If no backup name is specified, it will use the most recent backup.

EOF
}

list_backups() {
    log "Available backups on $SERVER:"
    
    local backups
    backups=$(ssh "$SERVER" "ls -la $BACKUP_DIR/*.tar.gz 2>/dev/null | sort -k9" || echo "")
    
    if [[ -z "$backups" ]]; then
        warning "No backups found in $BACKUP_DIR"
        return 1
    fi
    
    echo "$backups"
    return 0
}

get_latest_backup() {
    local latest_backup
    latest_backup=$(ssh "$SERVER" "ls -t $BACKUP_DIR/*.tar.gz 2>/dev/null | head -1" || echo "")
    
    if [[ -n "$latest_backup" ]]; then
        basename "$latest_backup" .tar.gz
    else
        echo ""
    fi
}

validate_backup() {
    local backup_name="$1"
    
    if ssh "$SERVER" "test -f $BACKUP_DIR/$backup_name.tar.gz"; then
        success "Backup $backup_name.tar.gz found"
        return 0
    else
        error "Backup $backup_name.tar.gz not found"
        return 1
    fi
}

create_pre_rollback_backup() {
    log "Creating pre-rollback backup..."
    
    local backup_name="pre-rollback-$(date +%Y%m%d-%H%M%S)"
    
    ssh "$SERVER" "
        if [ -d $REMOTE_DIR ]; then
            cd $REMOTE_DIR
            if [ -f $COMPOSE_FILE ]; then
                docker-compose -f $COMPOSE_FILE down || true
            fi
            tar -czf $BACKUP_DIR/$backup_name.tar.gz . 2>/dev/null || true
        fi
    "
    
    success "Pre-rollback backup created: $backup_name.tar.gz"
}

stop_current_services() {
    log "Stopping current services..."
    
    ssh "$SERVER" "
        if [ -d $REMOTE_DIR ] && [ -f $REMOTE_DIR/$COMPOSE_FILE ]; then
            cd $REMOTE_DIR
            docker-compose -f $COMPOSE_FILE down --remove-orphans || true
        fi
    "
    
    success "Services stopped"
}

restore_backup() {
    local backup_name="$1"
    
    log "Restoring backup: $backup_name.tar.gz"
    
    ssh "$SERVER" "
        # Create fresh directory
        rm -rf $REMOTE_DIR.old || true
        if [ -d $REMOTE_DIR ]; then
            mv $REMOTE_DIR $REMOTE_DIR.old
        fi
        mkdir -p $REMOTE_DIR
        
        # Extract backup
        cd $REMOTE_DIR
        tar -xzf $BACKUP_DIR/$backup_name.tar.gz
        
        # Set permissions
        chown -R \$USER:docker . 2>/dev/null || chown -R \$USER .
    "
    
    success "Backup restored"
}

start_services() {
    log "Starting services from restored backup..."
    
    ssh "$SERVER" "
        cd $REMOTE_DIR
        
        if [ -f $COMPOSE_FILE ]; then
            docker-compose -f $COMPOSE_FILE up -d
        else
            echo 'Warning: No compose file found in backup, trying alternatives...'
            
            # Try different compose file names
            for compose_file in docker-compose.prod.yml docker-compose.yml; do
                if [ -f \$compose_file ]; then
                    echo \"Using \$compose_file\"
                    docker-compose -f \$compose_file up -d
                    break
                fi
            done
        fi
    "
    
    success "Services started"
}

wait_for_services() {
    log "Waiting for services to be ready..."
    
    local max_attempts=20
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        log "Attempt $attempt/$max_attempts: Checking services..."
        
        if ssh "$SERVER" "curl -f -s http://localhost:8001/api/v1/settings/system-info/ > /dev/null" 2>/dev/null; then
            success "Services are ready\!"
            return 0
        fi
        
        sleep 10
        ((attempt++))
    done
    
    warning "Services may not be fully ready yet"
    return 1
}

verify_rollback() {
    log "Verifying rollback..."
    
    # Check container status
    local running_containers
    running_containers=$(ssh "$SERVER" "cd $REMOTE_DIR && docker-compose -f $COMPOSE_FILE ps --services --filter 'status=running' | wc -l" 2>/dev/null || echo "0")
    
    if [[ "$running_containers" -gt 0 ]]; then
        success "$running_containers containers are running"
    else
        warning "No containers appear to be running"
    fi
    
    # Check API response
    local api_response
    api_response=$(ssh "$SERVER" "curl -s http://localhost:8001/api/v1/settings/system-info/" 2>/dev/null || echo "ERROR")
    
    if [[ "$api_response" \!= "ERROR" ]] && echo "$api_response" | grep -q '"version"'; then
        local version
        version=$(echo "$api_response" | grep -o '"version":"[^"]*"' | cut -d'"' -f4)
        success "API responding with version: $version"
    else
        warning "API not responding properly"
    fi
    
    # Show deployment URLs
    log "Rollback completed\! Service URLs:"
    echo "🌐 Main Application: http://$SERVER:8080"
    echo "🔧 Backend API: http://$SERVER:8001/api/v1/"
    echo "⚛️  Frontend: http://$SERVER:3001"
}

cleanup_old_deployment() {
    log "Cleaning up old deployment files..."
    
    ssh "$SERVER" "
        if [ -d $REMOTE_DIR.old ]; then
            rm -rf $REMOTE_DIR.old
        fi
    " || warning "Could not clean up old deployment files"
}

main() {
    local SERVER=""
    local BACKUP_NAME=""
    
    # Parse arguments
    case $# in
        0)
            show_help
            exit 1
            ;;
        1)
            SERVER="$1"
            ;;
        2)
            SERVER="$1"
            BACKUP_NAME="$2"
            ;;
        *)
            error "Too many arguments"
            show_help
            exit 1
            ;;
    esac
    
    # Validate SSH connection
    if \! ssh -o ConnectTimeout=10 -o BatchMode=yes "$SERVER" "echo 'SSH OK'" &>/dev/null; then
        error "Cannot connect to server $SERVER via SSH"
        exit 1
    fi
    
    success "SSH connection to $SERVER established"
    
    # List available backups
    if \! list_backups; then
        error "No backups available for rollback"
        exit 1
    fi
    
    # Determine backup to use
    if [[ -z "$BACKUP_NAME" ]]; then
        BACKUP_NAME=$(get_latest_backup)
        if [[ -z "$BACKUP_NAME" ]]; then
            error "No backups found"
            exit 1
        fi
        log "Using latest backup: $BACKUP_NAME"
    else
        log "Using specified backup: $BACKUP_NAME"
    fi
    
    # Validate backup exists
    if \! validate_backup "$BACKUP_NAME"; then
        error "Backup validation failed"
        exit 1
    fi
    
    # Confirm rollback
    warning "This will rollback the deployment to: $BACKUP_NAME.tar.gz"
    warning "Current deployment will be backed up before rollback"
    echo -n "Continue with rollback? [y/N] "
    read -r response
    
    if [[ \! "$response" =~ ^[Yy]$ ]]; then
        log "Rollback cancelled"
        exit 0
    fi
    
    # Execute rollback steps
    create_pre_rollback_backup
    stop_current_services
    restore_backup "$BACKUP_NAME"
    start_services
    
    if wait_for_services; then
        verify_rollback
        cleanup_old_deployment
        success "🎉 Rollback completed successfully\!"
    else
        warning "Rollback completed but services may need manual attention"
        warning "Check service status with: ssh $SERVER 'cd $REMOTE_DIR && docker-compose -f $COMPOSE_FILE ps'"
    fi
}

main "$@"
ROLLBACK_EOF < /dev/null