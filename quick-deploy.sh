#!/bin/bash

# PrintFarm v3.3.4 - Quick Deploy Script
# Automated deployment to kemomail3.keenetic.pro:2131

echo "🚀 PrintFarm v3.3.4 Quick Deployment"
echo "===================================="

# Server details
SERVER="printfarm@kemomail3.keenetic.pro"
PORT="2131"
SERVER_IP="192.168.1.98"
REMOTE_DIR="/opt/printfarm-production"
COMPOSE_FILE="docker-compose.server.prod.yml"

echo
echo "📍 Target: $SERVER:$PORT"
echo "📁 Directory: $REMOTE_DIR"
echo "🔐 Password: 1qaz2wsX"
echo

echo -n "Proceed with deployment? [y/N] "
read -r response
if [[ ! "$response" =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled"
    exit 0
fi

echo
echo "📦 Step 1: Creating project directory on server..."
ssh -p $PORT $SERVER "sudo mkdir -p $REMOTE_DIR && sudo chown -R \$USER $REMOTE_DIR"

echo "📤 Step 2: Uploading configuration files..."
scp -P $PORT $COMPOSE_FILE $SERVER:$REMOTE_DIR/
scp -P $PORT .env.prod $SERVER:$REMOTE_DIR/
scp -P $PORT VERSION $SERVER:$REMOTE_DIR/

echo "📤 Step 3: Uploading application code..."
scp -rP $PORT backend/ $SERVER:$REMOTE_DIR/
scp -rP $PORT frontend/ $SERVER:$REMOTE_DIR/
scp -rP $PORT docker/ $SERVER:$REMOTE_DIR/

echo "🚀 Step 4: Deploying on server..."
ssh -p $PORT $SERVER "
    cd $REMOTE_DIR
    echo '🛑 Stopping old containers...'
    docker-compose -f $COMPOSE_FILE down --remove-orphans 2>/dev/null || true
    
    echo '🧹 Cleaning up old images...'
    docker system prune -f 2>/dev/null || true
    
    echo '🏗️ Building new images...'
    docker-compose -f $COMPOSE_FILE build --no-cache
    
    echo '🚀 Starting containers...'
    docker-compose -f $COMPOSE_FILE up -d
    
    echo '⏳ Waiting for services to start...'
    sleep 30
    
    echo '📊 Container status:'
    docker-compose -f $COMPOSE_FILE ps
    
    echo '🌐 Testing API...'
    curl -s http://localhost:8001/api/v1/settings/system-info/ | head -100 || echo 'API starting...'
"

echo
echo "✅ Deployment completed!"
echo
echo "🌐 Access URLs:"
echo "   Main App:    http://$SERVER_IP:8080"
echo "   Backend API: http://$SERVER_IP:8001/api/v1/"
echo "   Frontend:    http://$SERVER_IP:3001"
echo
echo "🔧 SSH Access: ssh -p $PORT $SERVER"
echo
echo "🧪 Test deployment:"
echo "   curl http://$SERVER_IP:8001/api/v1/settings/system-info/"
echo
echo "🎉 PrintFarm v3.3.4 deployed successfully!"