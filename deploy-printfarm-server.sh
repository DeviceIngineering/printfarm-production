#!/bin/bash

# PrintFarm v3.3.4 - Deployment Script for kemomail3.keenetic.pro
# Specialized for: printfarm@kemomail3.keenetic.pro:2131

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Server configuration
SERVER_HOST="kemomail3.keenetic.pro"
SERVER_USER="printfarm"
SERVER_PORT="2131"
SERVER_IP="192.168.1.98"
SSH_OPTS="-o ConnectTimeout=15 -o ServerAliveInterval=60 -p $SERVER_PORT"

# Project configuration
PROJECT_NAME="printfarm-production"
REMOTE_DIR="/opt/$PROJECT_NAME"
COMPOSE_FILE="docker-compose.server.prod.yml"
ENV_FILE=".env.prod"
BACKUP_DIR="/opt/backups/$PROJECT_NAME"
PORTS_TO_CHECK=(8001 3001 8080 5433 6380)

# Default values
DRY_RUN=false
FORCE=false

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
PrintFarm Production Deployment Script

Usage: $0 [OPTIONS]

OPTIONS:
    --dry-run       Show what would be done without executing
    --force         Skip confirmation prompts
    --help          Show this help message

TARGET SERVER:
    Host: $SERVER_HOST
    User: $SERVER_USER
    Port: $SERVER_PORT
    Local IP: $SERVER_IP

SERVICE PORTS:
    Backend API:    8001
    Frontend:       3001  
    Nginx:          8080
    PostgreSQL:     5433
    Redis:          6380

EXAMPLES:
    $0                      # Interactive deployment
    $0 --dry-run           # Test run
    $0 --force             # Skip confirmations

EOF
}

ssh_exec() {
    ssh $SSH_OPTS "$SERVER_USER@$SERVER_HOST" "$1"
}

rsync_files() {
    local src="$1"
    local dst="$2"
    rsync -avz --delete -e "ssh $SSH_OPTS" "$src" "$SERVER_USER@$SERVER_HOST:$dst"
}

check_dependencies() {
    log "Checking local dependencies..."
    
    for cmd in docker docker-compose rsync ssh; do
        if ! command -v $cmd &> /dev/null; then
            error "$cmd is not installed"
            exit 1
        fi
    done
    
    success "Local dependencies OK"
}

check_ssh_connection() {
    log "Testing SSH connection to $SERVER_HOST:$SERVER_PORT..."
    
    if ssh_exec "echo 'SSH connection successful' && whoami && uname -a"; then
        success "SSH connection established"
    else
        error "Cannot connect to server"
        error "Try manually: ssh -p $SERVER_PORT $SERVER_USER@$SERVER_HOST"
        exit 1
    fi
}

check_server_requirements() {
    log "Checking server requirements..."
    
    # Check Docker
    if ssh_exec "docker --version" >/dev/null 2>&1; then
        success "Docker is installed"
    else
        error "Docker is not installed on server"
        log "Installing Docker..."
        ssh_exec "curl -fsSL https://get.docker.com | sudo sh && sudo usermod -aG docker \$USER"
        warning "Please logout and login again on server, then re-run deployment"
        exit 1
    fi
    
    # Check Docker Compose
    if ssh_exec "docker-compose --version" >/dev/null 2>&1; then
        success "Docker Compose is installed"
    else
        error "Docker Compose not found, installing..."
        ssh_exec 'sudo curl -L "https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose && sudo chmod +x /usr/local/bin/docker-compose'
    fi
}

check_ports() {
    log "Checking port availability..."
    
    for port in "${PORTS_TO_CHECK[@]}"; do
        if ssh_exec "ss -tlnp | grep :$port" >/dev/null 2>&1; then
            if [[ "$FORCE" == false ]]; then
                error "Port $port is in use"
                warning "Use --force to ignore or change ports in compose file"
                exit 1
            else
                warning "Port $port is in use (continuing with --force)"
            fi
        else
            success "Port $port is available"
        fi
    done
}

prepare_env_file() {
    log "Preparing environment file for server..."
    
    if [ ! -f "$ENV_FILE" ]; then
        error "Environment file $ENV_FILE not found"
        log "Creating from template..."
        
        cat > "$ENV_FILE" << ENV_TEMPLATE
# PrintFarm v3.3.4 Production Environment
SECRET_KEY=$(openssl rand -base64 32)
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,$SERVER_IP,$SERVER_HOST

# Database
POSTGRES_DB=printfarm_production
POSTGRES_USER=printfarm_user
POSTGRES_PASSWORD=$(openssl rand -base64 16)
DATABASE_URL=postgresql://printfarm_user:$(openssl rand -base64 16)@db:5432/printfarm_production

# Redis
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Frontend
REACT_APP_API_URL=http://$SERVER_IP:8001/api/v1
NODE_ENV=production

# MoySklad (UPDATE THESE!)
MOYSKLAD_TOKEN=f9be4985f5e3488716c040ca52b8e04c7c0f9e0b
MOYSKLAD_DEFAULT_WAREHOUSE=241ed919-a631-11ee-0a80-07a9000bb947

# PrintFarm
PRINTFARM_VERSION=3.3.4
ENABLE_RESERVE_STOCK=true
ENV_TEMPLATE
        
        success "Environment file created: $ENV_FILE"
        warning "Please review and update MoySklad settings in $ENV_FILE"
    fi
}

create_backup() {
    log "Creating backup..."
    
    ssh_exec "mkdir -p $BACKUP_DIR"
    
    if ssh_exec "test -d $REMOTE_DIR"; then
        local backup_name="backup-$(date +%Y%m%d-%H%M%S)"
        ssh_exec "cd $REMOTE_DIR && tar -czf $BACKUP_DIR/$backup_name.tar.gz . 2>/dev/null || true"
        success "Backup created: $backup_name.tar.gz"
    else
        log "No existing deployment to backup"
    fi
}

sync_project() {
    log "Syncing project files..."
    
    # Prepare server directory
    ssh_exec "sudo mkdir -p $REMOTE_DIR && sudo chown -R \$USER $REMOTE_DIR"
    
    # Sync files
    local files_to_sync=(
        "backend/"
        "frontend/"  
        "docker/"
        "$COMPOSE_FILE"
        "$ENV_FILE"
        "VERSION"
    )
    
    for item in "${files_to_sync[@]}"; do
        if [ -e "$item" ]; then
            log "Syncing $item..."
            rsync_files "$item" "$REMOTE_DIR/"
        else
            warning "$item not found, skipping"
        fi
    done
    
    success "Project files synced"
}

deploy_containers() {
    log "Deploying Docker containers..."
    
    ssh_exec "
        cd $REMOTE_DIR
        
        # Stop old containers
        if [ -f $COMPOSE_FILE ]; then
            docker-compose -f $COMPOSE_FILE down --remove-orphans || true
        fi
        
        # Clean up
        docker system prune -f || true
        
        # Build and start
        docker-compose -f $COMPOSE_FILE build --no-cache
        docker-compose -f $COMPOSE_FILE up -d
    "
    
    success "Containers deployed"
}

wait_for_services() {
    log "Waiting for services to start..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        log "Checking services... ($attempt/$max_attempts)"
        
        if ssh_exec "curl -f -s http://localhost:8001/api/v1/settings/system-info/ > /dev/null"; then
            success "Services are ready!"
            return 0
        fi
        
        sleep 10
        ((attempt++))
    done
    
    warning "Services may need more time to start"
    return 1
}

show_deployment_info() {
    log "Deployment completed!"
    
    ssh_exec "
        cd $REMOTE_DIR
        echo '=== Container Status ==='
        docker-compose -f $COMPOSE_FILE ps
    "
    
    echo
    success "🎉 PrintFarm v3.3.4 deployed successfully!"
    echo
    log "=== Access URLs ==="
    echo "🌐 Main Application: http://$SERVER_IP:8080"
    echo "🔧 Backend API: http://$SERVER_IP:8001/api/v1/"
    echo "⚛️ Frontend: http://$SERVER_IP:3001"
    echo "📊 System Info: http://$SERVER_IP:8001/api/v1/settings/system-info/"
    echo
    log "SSH Access: ssh -p $SERVER_PORT $SERVER_USER@$SERVER_HOST"
}

main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --force)
                FORCE=true
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    log "Starting PrintFarm v3.3.4 deployment to $SERVER_HOST"
    
    if [ "$DRY_RUN" = true ]; then
        warning "DRY RUN MODE - No actual changes will be made"
        log "Would perform deployment to $SERVER_HOST:$SERVER_PORT"
        log "Target directory: $REMOTE_DIR"
        log "Compose file: $COMPOSE_FILE"
        exit 0
    fi
    
    # Confirm deployment
    if [ "$FORCE" = false ]; then
        echo
        warning "This will deploy PrintFarm v3.3.4 to:"
        echo "  Server: $SERVER_HOST:$SERVER_PORT ($SERVER_IP)"
        echo "  User: $SERVER_USER"
        echo "  Directory: $REMOTE_DIR"
        echo
        echo -n "Continue? [y/N] "
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            log "Deployment cancelled"
            exit 0
        fi
    fi
    
    # Execute deployment
    check_dependencies
    check_ssh_connection
    check_server_requirements
    check_ports
    prepare_env_file
    create_backup
    sync_project
    deploy_containers
    
    if wait_for_services; then
        show_deployment_info
    else
        warning "Deployment completed but services need manual verification"
        log "Check status: ssh -p $SERVER_PORT $SERVER_USER@$SERVER_HOST 'cd $REMOTE_DIR && docker-compose -f $COMPOSE_FILE logs'"
    fi
}

main "$@"