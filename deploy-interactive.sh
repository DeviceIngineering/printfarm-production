#!/bin/bash

# PrintFarm v3.3.4 - Interactive Deployment Script
# For servers requiring password authentication

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

# Project configuration
PROJECT_NAME="printfarm-production"
REMOTE_DIR="/opt/$PROJECT_NAME"
COMPOSE_FILE="docker-compose.server.prod.yml"
ENV_FILE=".env.prod"

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

show_deployment_info() {
    cat << INFO_EOF

🚀 PrintFarm v3.3.4 Production Deployment

📍 Target Server:
   Host: $SERVER_HOST:$SERVER_PORT
   User: $SERVER_USER  
   Local IP: $SERVER_IP
   Password: 1qaz2wsX

🔧 Services will be deployed on:
   Main App (Nginx):  http://$SERVER_IP:8080
   Backend API:       http://$SERVER_IP:8001/api/v1/
   Frontend:          http://$SERVER_IP:3001
   Database (PostgreSQL): Port 5433
   Redis:             Port 6380

📁 Files to deploy:
   • Docker Compose: $COMPOSE_FILE
   • Environment: $ENV_FILE
   • Backend code (Django)
   • Frontend code (React)
   • Docker configurations

INFO_EOF
}

manual_deployment_steps() {
    cat << MANUAL_EOF

📋 Manual Deployment Steps:

1. Connect to server:
   ssh -p $SERVER_PORT $SERVER_USER@$SERVER_HOST
   (Password: 1qaz2wsX)

2. Install Docker (if not installed):
   curl -fsSL https://get.docker.com | sudo sh
   sudo usermod -aG docker \$USER
   # Logout and login again

3. Install Docker Compose:
   sudo curl -L "https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-\$(uname -s)-\$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose

4. Create project directory:
   sudo mkdir -p $REMOTE_DIR
   sudo chown -R \$USER $REMOTE_DIR
   cd $REMOTE_DIR

5. Upload files using scp:
   # From your local machine:
   scp -P $SERVER_PORT $COMPOSE_FILE $SERVER_USER@$SERVER_HOST:$REMOTE_DIR/
   scp -P $SERVER_PORT $ENV_FILE $SERVER_USER@$SERVER_HOST:$REMOTE_DIR/
   scp -rP $SERVER_PORT backend/ $SERVER_USER@$SERVER_HOST:$REMOTE_DIR/
   scp -rP $SERVER_PORT frontend/ $SERVER_USER@$SERVER_HOST:$REMOTE_DIR/
   scp -rP $SERVER_PORT docker/ $SERVER_USER@$SERVER_HOST:$REMOTE_DIR/
   scp -P $SERVER_PORT VERSION $SERVER_USER@$SERVER_HOST:$REMOTE_DIR/

6. Deploy on server:
   cd $REMOTE_DIR
   docker-compose -f $COMPOSE_FILE up -d --build

7. Check deployment:
   docker-compose -f $COMPOSE_FILE ps
   curl http://localhost:8001/api/v1/settings/system-info/

MANUAL_EOF
}

check_files() {
    log "Checking required files..."
    
    local missing_files=()
    
    for file in "$COMPOSE_FILE" "$ENV_FILE" "backend" "frontend" "docker" "VERSION"; do
        if [ ! -e "$file" ]; then
            missing_files+=("$file")
        fi
    done
    
    if [ ${#missing_files[@]} -gt 0 ]; then
        error "Missing required files:"
        for file in "${missing_files[@]}"; do
            echo "  ❌ $file"
        done
        exit 1
    fi
    
    success "All required files present"
}

test_ssh_connection() {
    log "Testing SSH connection..."
    echo
    warning "Please enter password when prompted: 1qaz2wsX"
    echo
    
    if ssh -o ConnectTimeout=15 -p $SERVER_PORT $SERVER_USER@$SERVER_HOST "echo 'SSH connection successful!' && whoami && pwd && uname -a"; then
        success "SSH connection established"
        return 0
    else
        error "SSH connection failed"
        return 1
    fi
}

create_upload_script() {
    log "Creating file upload script..."
    
    cat > upload-files.sh << UPLOAD_EOF
#!/bin/bash

# Upload all project files to server
echo "Uploading files to $SERVER_HOST:$SERVER_PORT..."
echo "Password: 1qaz2wsX"
echo

# Upload compose and env files
scp -P $SERVER_PORT $COMPOSE_FILE $SERVER_USER@$SERVER_HOST:$REMOTE_DIR/
scp -P $SERVER_PORT $ENV_FILE $SERVER_USER@$SERVER_HOST:$REMOTE_DIR/
scp -P $SERVER_PORT VERSION $SERVER_USER@$SERVER_HOST:$REMOTE_DIR/

# Upload directories
scp -rP $SERVER_PORT backend/ $SERVER_USER@$SERVER_HOST:$REMOTE_DIR/
scp -rP $SERVER_PORT frontend/ $SERVER_USER@$SERVER_HOST:$REMOTE_DIR/  
scp -rP $SERVER_PORT docker/ $SERVER_USER@$SERVER_HOST:$REMOTE_DIR/

echo "Files uploaded successfully!"
UPLOAD_EOF
    
    chmod +x upload-files.sh
    success "Upload script created: upload-files.sh"
}

create_server_deploy_script() {
    log "Creating server deployment script..."
    
    cat > server-deploy.sh << SERVER_EOF
#!/bin/bash

# Run this script on the server after uploading files

set -e

cd $REMOTE_DIR

echo "🚀 Starting PrintFarm deployment..."

# Stop old containers
if [ -f $COMPOSE_FILE ]; then
    echo "Stopping old containers..."
    docker-compose -f $COMPOSE_FILE down || true
fi

# Clean up old images
echo "Cleaning up..."
docker system prune -f || true

# Build and start containers
echo "Building new images..."
docker-compose -f $COMPOSE_FILE build --no-cache

echo "Starting containers..."
docker-compose -f $COMPOSE_FILE up -d

echo "Waiting for services to start..."
sleep 30

# Check status
echo "Container status:"
docker-compose -f $COMPOSE_FILE ps

echo "Testing API..."
curl -s http://localhost:8001/api/v1/settings/system-info/ || echo "API not yet ready"

echo "🎉 Deployment completed!"
echo
echo "Access URLs:"
echo "  Main App: http://$SERVER_IP:8080"
echo "  Backend API: http://$SERVER_IP:8001/api/v1/"
echo "  Frontend: http://$SERVER_IP:3001"

SERVER_EOF
    
    success "Server deployment script created: server-deploy.sh"
}

main() {
    echo "🚀 PrintFarm v3.3.4 Interactive Deployment"
    echo "========================================="
    echo
    
    show_deployment_info
    
    echo
    warning "This script will help you deploy PrintFarm to your server."
    warning "Since we need password authentication, this will be semi-automated."
    echo
    
    echo -n "Continue with deployment? [y/N] "
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        log "Deployment cancelled"
        exit 0
    fi
    
    # Check local files
    check_files
    
    # Test SSH connection  
    if ! test_ssh_connection; then
        error "Cannot connect to server"
        manual_deployment_steps
        exit 1
    fi
    
    echo
    log "Connection successful! Preparing deployment scripts..."
    
    # Create helper scripts
    create_upload_script
    create_server_deploy_script
    
    echo
    success "🎯 Ready for deployment!"
    echo
    log "Next steps:"
    echo "1. Run: ./upload-files.sh (upload files to server)"
    echo "2. SSH to server: ssh -p $SERVER_PORT $SERVER_USER@$SERVER_HOST"  
    echo "3. On server run: cd $REMOTE_DIR && bash server-deploy.sh"
    echo
    log "Or use manual deployment steps shown above"
    
    echo
    echo -n "Run upload script now? [y/N] "
    read -r upload_response
    if [[ "$upload_response" =~ ^[Yy]$ ]]; then
        log "Starting file upload..."
        ./upload-files.sh
        
        echo
        success "Files uploaded! Now connect to server and run deployment:"
        echo "ssh -p $SERVER_PORT $SERVER_USER@$SERVER_HOST"
        echo "cd $REMOTE_DIR && bash server-deploy.sh"
    fi
}

main "$@"