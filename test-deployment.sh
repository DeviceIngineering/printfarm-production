#\!/bin/bash

# PrintFarm v3.3.4 - Deployment Testing Script
# Usage: ./test-deployment.sh user@server-ip

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
COMPOSE_FILE="docker-compose.server.prod.yml"

# Test results
TESTS_PASSED=0
TESTS_FAILED=0

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
    ((TESTS_PASSED++))
}

fail() {
    echo -e "${RED}❌ $1${NC}"
    ((TESTS_FAILED++))
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

test_containers() {
    log "Testing container status..."
    
    local containers_output
    containers_output=$(ssh "$SERVER" "cd $REMOTE_DIR && docker-compose -f $COMPOSE_FILE ps --format table" 2>/dev/null || echo "ERROR")
    
    if [[ "$containers_output" == "ERROR" ]]; then
        fail "Cannot get container status"
        return 1
    fi
    
    # Expected containers
    local expected_containers=("backend" "frontend" "db" "redis" "nginx" "celery" "celery-beat")
    
    for container in "${expected_containers[@]}"; do
        if echo "$containers_output" | grep -q "$container.*Up\|$container.*running"; then
            success "Container $container is running"
        else
            fail "Container $container is not running"
        fi
    done
}

test_ports() {
    log "Testing port accessibility..."
    
    local ports=(8001 3001 8080 5433 6380)
    
    for port in "${ports[@]}"; do
        if ssh "$SERVER" "timeout 5 bash -c '</dev/tcp/localhost/$port'" &>/dev/null; then
            success "Port $port is accessible"
        else
            fail "Port $port is not accessible"
        fi
    done
}

test_api_endpoints() {
    log "Testing API endpoints..."
    
    # Test system info endpoint
    local system_info
    system_info=$(ssh "$SERVER" "curl -f -s http://localhost:8001/api/v1/settings/system-info/" 2>/dev/null || echo "ERROR")
    
    if [[ "$system_info" == "ERROR" ]]; then
        fail "API system-info endpoint not responding"
    else
        if echo "$system_info" | grep -q '"version"'; then
            success "API system-info endpoint working"
            
            # Extract version
            local version
            version=$(echo "$system_info" | grep -o '"version":"[^"]*"' | cut -d'"' -f4)
            log "System version: $version"
        else
            fail "API system-info endpoint returned invalid data"
        fi
    fi
    
    # Test products endpoint  
    local products_response
    products_response=$(ssh "$SERVER" "curl -f -s http://localhost:8001/api/v1/tochka/products/ | head -100" 2>/dev/null || echo "ERROR")
    
    if [[ "$products_response" == "ERROR" ]]; then
        fail "API products endpoint not responding"
    else
        if echo "$products_response" | grep -q '"results"\|"count"'; then
            success "API products endpoint working"
        else
            fail "API products endpoint returned invalid data"
        fi
    fi
    
    # Test production endpoint
    local production_response
    production_response=$(ssh "$SERVER" "curl -f -s http://localhost:8001/api/v1/tochka/production/ | head -100" 2>/dev/null || echo "ERROR")
    
    if [[ "$production_response" == "ERROR" ]]; then
        fail "API production endpoint not responding"
    else
        if echo "$production_response" | grep -q '"results"\|"count"'; then
            success "API production endpoint working"
        else
            fail "API production endpoint returned invalid data"
        fi
    fi
}

test_frontend() {
    log "Testing frontend accessibility..."
    
    # Test direct frontend port
    local frontend_response
    frontend_response=$(ssh "$SERVER" "curl -f -s http://localhost:3001/ | head -100" 2>/dev/null || echo "ERROR")
    
    if [[ "$frontend_response" == "ERROR" ]]; then
        fail "Frontend not responding on port 3001"
    else
        if echo "$frontend_response" | grep -qi "html\|DOCTYPE\|printfarm"; then
            success "Frontend responding on port 3001"
        else
            fail "Frontend returned unexpected content"
        fi
    fi
    
    # Test nginx proxy
    local nginx_response
    nginx_response=$(ssh "$SERVER" "curl -f -s http://localhost:8080/ | head -100" 2>/dev/null || echo "ERROR")
    
    if [[ "$nginx_response" == "ERROR" ]]; then
        fail "Nginx proxy not responding on port 8080"
    else
        if echo "$nginx_response" | grep -qi "html\|DOCTYPE"; then
            success "Nginx proxy responding on port 8080"
        else
            fail "Nginx proxy returned unexpected content"
        fi
    fi
}

test_database() {
    log "Testing database connectivity..."
    
    # Test if database is accessible from backend
    local db_test
    db_test=$(ssh "$SERVER" "cd $REMOTE_DIR && docker-compose -f $COMPOSE_FILE exec -T backend python -c 'from django.db import connection; connection.cursor().execute(\"SELECT 1\"); print(\"DB_OK\")'" 2>/dev/null || echo "ERROR")
    
    if [[ "$db_test" == *"DB_OK"* ]]; then
        success "Database connectivity working"
    else
        fail "Database connectivity failed"
    fi
    
    # Test product count
    local product_count
    product_count=$(ssh "$SERVER" "cd $REMOTE_DIR && docker-compose -f $COMPOSE_FILE exec -T backend python manage.py shell -c 'from apps.products.models import Product; print(Product.objects.count())'" 2>/dev/null || echo "ERROR")
    
    if [[ "$product_count" =~ ^[0-9]+$ ]]; then
        success "Products in database: $product_count"
    else
        fail "Cannot get product count from database"
    fi
}

test_logs() {
    log "Checking container logs for errors..."
    
    local services=("backend" "frontend" "db" "redis" "nginx")
    
    for service in "${services[@]}"; do
        log "Checking $service logs..."
        
        local error_count
        error_count=$(ssh "$SERVER" "cd $REMOTE_DIR && docker-compose -f $COMPOSE_FILE logs --tail=50 $service 2>/dev/null | grep -i 'error\|exception\|failed' | wc -l" || echo "0")
        
        if [[ "$error_count" -eq 0 ]]; then
            success "$service: No errors in recent logs"
        else
            warning "$service: Found $error_count errors in logs"
            
            # Show recent errors
            ssh "$SERVER" "cd $REMOTE_DIR && docker-compose -f $COMPOSE_FILE logs --tail=10 $service | grep -i 'error\|exception\|failed'" 2>/dev/null || true
        fi
    done
}

test_reserve_functionality() {
    log "Testing reserve stock functionality (critical v3.3.4 feature)..."
    
    # Test if products with reserve are visible in production API
    local products_with_reserve
    products_with_reserve=$(ssh "$SERVER" "curl -s http://localhost:8001/api/v1/tochka/production/ | grep -c '\"reserved_stock\":[^0]' || echo '0'" 2>/dev/null)
    
    if [[ "$products_with_reserve" -gt 0 ]]; then
        success "Found $products_with_reserve products with reserve in production API"
    else
        fail "No products with reserve found in production API - critical v3.3.4 feature not working"
    fi
    
    # Test specific critical product from v3.3.4
    local critical_product
    critical_product=$(ssh "$SERVER" "curl -s http://localhost:8001/api/v1/tochka/production/ | grep '15-43001R' | head -1" 2>/dev/null || echo "")
    
    if [[ -n "$critical_product" ]]; then
        success "Critical product 15-43001R found in production list"
    else
        warning "Critical product 15-43001R not found in production list"
    fi
}

show_summary() {
    echo
    log "=== TEST SUMMARY ==="
    echo -e "${GREEN}✅ Tests Passed: $TESTS_PASSED${NC}"
    echo -e "${RED}❌ Tests Failed: $TESTS_FAILED${NC}"
    
    local total_tests=$((TESTS_PASSED + TESTS_FAILED))
    local success_rate
    
    if [[ $total_tests -gt 0 ]]; then
        success_rate=$((TESTS_PASSED * 100 / total_tests))
        echo "Success Rate: $success_rate%"
    fi
    
    echo
    if [[ $TESTS_FAILED -eq 0 ]]; then
        success "🎉 All tests passed\! Deployment is healthy."
        
        log "=== DEPLOYMENT URLS ==="
        echo "🌐 Main Application: http://$SERVER:8080"
        echo "🔧 Backend API: http://$SERVER:8001/api/v1/"
        echo "⚛️  Frontend: http://$SERVER:3001"
        echo "📊 System Info: http://$SERVER:8001/api/v1/settings/system-info/"
        
        return 0
    else
        fail "Deployment has issues that need attention"
        
        log "=== TROUBLESHOOTING ==="
        echo "• Check container logs: ssh $SERVER 'cd $REMOTE_DIR && docker-compose -f $COMPOSE_FILE logs'"
        echo "• Check container status: ssh $SERVER 'cd $REMOTE_DIR && docker-compose -f $COMPOSE_FILE ps'"
        echo "• Restart services: ssh $SERVER 'cd $REMOTE_DIR && docker-compose -f $COMPOSE_FILE restart'"
        
        return 1
    fi
}

main() {
    if [[ $# -eq 0 ]]; then
        echo "Usage: $0 user@server-ip"
        exit 1
    fi
    
    local SERVER="$1"
    
    log "Starting deployment tests for $SERVER"
    log "Project: $PROJECT_NAME"
    log "Testing PrintFarm v3.3.4 with Reserve Stock Integration"
    
    # Check SSH connectivity first
    if \! ssh -o ConnectTimeout=10 -o BatchMode=yes "$SERVER" "echo 'SSH OK'" &>/dev/null; then
        fail "Cannot connect to server $SERVER via SSH"
        exit 1
    fi
    
    success "SSH connection to $SERVER established"
    
    # Run all tests
    test_containers
    test_ports
    test_api_endpoints
    test_frontend
    test_database
    test_logs
    test_reserve_functionality
    
    # Show summary and exit with appropriate code
    if show_summary; then
        exit 0
    else
        exit 1
    fi
}

main "$@"
TEST_EOF < /dev/null