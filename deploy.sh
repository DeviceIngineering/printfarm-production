#\!/bin/bash

# PrintFarm v3.3.4 - Production Deployment Script
# Usage: ./deploy.sh user@server-ip [--dry-run] [--force]

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="printfarm-production"
REMOTE_DIR="/opt/$PROJECT_NAME"
COMPOSE_FILE="docker-compose.server.prod.yml"
ENV_FILE=".env.prod"
BACKUP_DIR="/opt/backups/$PROJECT_NAME"
PORTS_TO_CHECK=(8001 3001 8080 5433 6380)

# Default values
DRY_RUN=false
FORCE=false
SERVER=""

# Functions
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

Usage: $0 user@server-ip [OPTIONS]

OPTIONS:
    --dry-run       Show what would be done without executing
    --force         Skip confirmation prompts
    --help          Show this help message

EXAMPLES:
    $0 root@192.168.1.100
    $0 user@myserver.com --dry-run
    $0 deploy@prod.example.com --force

PORTS USED:
    Backend API:    8001  (was 8000, changed due to conflict)
    Frontend:       3001  (was 3000, separated for clarity)
    Nginx:          8080  (was 80, easier access)
    PostgreSQL:     5433  (was 5432, avoiding conflicts)
    Redis:          6380  (was 6379, avoiding conflicts)

EOF
}

check_dependencies() {
    log "Checking local dependencies..."
    
    if \! command -v docker &> /dev/null; then
        error "Docker is not installed locally"
        exit 1
    fi
    
    if \! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed locally"
        exit 1
    fi
    
    if \! command -v rsync &> /dev/null; then
        error "rsync is not installed"
        exit 1
    fi
    
    success "Local dependencies check passed"
}

check_server_dependencies() {
    log "Checking server dependencies on $SERVER..."
    
    if \! ssh -o ConnectTimeout=10 -o BatchMode=yes "$SERVER" "echo 'SSH connection successful'" &> /dev/null; then
        error "Cannot connect to server $SERVER via SSH"
        error "Please check SSH key authentication or connection details"
        exit 1
    fi
    
    if \! ssh "$SERVER" "docker --version" &> /dev/null; then
        error "Docker is not installed on the server"
        exit 1
    fi
    
    if \! ssh "$SERVER" "docker-compose --version" &> /dev/null; then
        error "Docker Compose is not installed on the server"
        exit 1
    fi
    
    success "Server dependencies check passed"
}

check_ports() {
    log "Checking if required ports are available on $SERVER..."
    
    for port in "${PORTS_TO_CHECK[@]}"; do
        if ssh "$SERVER" "ss -tlnp | grep :$port" &> /dev/null; then
            if [[ "$FORCE" == false ]]; then
                error "Port $port is already in use on the server"
                warning "Use --force to ignore port conflicts"
                exit 1
            else
                warning "Port $port is in use but continuing due to --force flag"
            fi
        else
            success "Port $port is available"
        fi
    done
}

sync_files() {
    log "Syncing project files to $SERVER..."
    
    local sync_items=(
        "backend/"
        "frontend/"
        "docker/"
        "$COMPOSE_FILE"
        "$ENV_FILE"
        "VERSION"
    )
    
    cat > /tmp/rsync_exclude << EOF
.git/
__pycache__/
*.pyc
node_modules/
.env.local
.DS_Store
*.log
EOF
    
    for item in "${sync_items[@]}"; do
        if [ -e "$item" ]; then
            log "Syncing $item..."
            rsync -avz --exclude-from=/tmp/rsync_exclude \
                  --delete "$item" "$SERVER:$REMOTE_DIR/"
        else
            warning "File/directory $item not found, skipping"
        fi
    done
    
    success "File sync completed"
}

deploy() {
    log "Deploying to $SERVER..."
    
    ssh "$SERVER" "
        mkdir -p $REMOTE_DIR
        cd $REMOTE_DIR
        
        # Stop old containers
        if [ -f $COMPOSE_FILE ]; then
            docker-compose -f $COMPOSE_FILE down || true
        fi
        
        # Build and start new containers
        docker-compose -f $COMPOSE_FILE build --no-cache
        docker-compose -f $COMPOSE_FILE up -d
    "
    
    success "Deployment completed"
}

wait_for_services() {
    log "Waiting for services to be ready..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        log "Attempt $attempt/$max_attempts: Checking services..."
        
        if ssh "$SERVER" "curl -f -s http://localhost:8001/api/v1/settings/system-info/ > /dev/null"; then
            success "Services are ready\!"
            return 0
        fi
        
        sleep 10
        ((attempt++))
    done
    
    error "Services did not become ready"
    return 1
}

show_status() {
    log "Deployment Status:"
    
    ssh "$SERVER" "
        cd $REMOTE_DIR
        echo '=== Container Status ==='
        docker-compose -f $COMPOSE_FILE ps
        
        echo
        echo '=== Service URLs ==='
        echo 'Main App: http://$SERVER:8080'
        echo 'Backend API: http://$SERVER:8001'
        echo 'Frontend: http://$SERVER:3001'
        
        echo
        echo '=== Health Check ==='
        curl -s http://localhost:8001/api/v1/settings/system-info/ | head -50 || echo 'API not responding'
    "
}

main() {
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
                if [ -z "$SERVER" ]; then
                    SERVER="$1"
                else
                    error "Unknown option: $1"
                    exit 1
                fi
                shift
                ;;
        esac
    done
    
    if [ -z "$SERVER" ]; then
        error "Server address is required"
        show_help
        exit 1
    fi
    
    if [ \! -f "$COMPOSE_FILE" ]; then
        error "Compose file $COMPOSE_FILE not found"
        exit 1
    fi
    
    log "Starting deployment to $SERVER"
    
    if [ "$DRY_RUN" = true ]; then
        warning "DRY RUN MODE - No changes will be made"
        log "Would deploy to $SERVER using $COMPOSE_FILE"
        exit 0
    fi
    
    if [ "$FORCE" = false ]; then
        echo -n "Continue with deployment? [y/N] "
        read -r response
        if [[ \! "$response" =~ ^[Yy]$ ]]; then
            log "Deployment cancelled"
            exit 0
        fi
    fi
    
    check_dependencies
    check_server_dependencies  
    check_ports
    sync_files
    deploy
    
    if wait_for_services; then
        success "🎉 Deployment successful\!"
        show_status
    else
        error "Deployment completed but services not healthy"
        exit 1
    fi
}

main "$@"
DEPLOY_EOF < /dev/null