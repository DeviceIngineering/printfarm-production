#!/bin/bash

echo "=== PrintFarm Server Diagnostics ==="
echo "Time: $(date)"
echo ""

echo "=== 1. Container Status ==="
docker-compose -f docker-compose.server.yml ps
echo ""

echo "=== 2. Nginx Logs (last 30 lines) ==="
docker-compose -f docker-compose.server.yml logs nginx --tail=30
echo ""

echo "=== 3. Frontend Logs (last 30 lines) ==="
docker-compose -f docker-compose.server.yml logs frontend --tail=30
echo ""

echo "=== 4. Backend Logs (last 30 lines) ==="
docker-compose -f docker-compose.server.yml logs backend --tail=30
echo ""

echo "=== 5. Check Backend Port ==="
docker-compose -f docker-compose.server.yml exec -T backend sh -c "netstat -tlnp 2>/dev/null || ss -tlnp" || echo "Backend container not running"
echo ""

echo "=== 6. Check Frontend Port ==="
docker-compose -f docker-compose.server.yml exec -T frontend sh -c "netstat -tlnp 2>/dev/null || ss -tlnp" || echo "Frontend container not running"
echo ""

echo "=== 7. Test Frontend Direct Access ==="
docker-compose -f docker-compose.server.yml exec -T frontend curl -s http://localhost:3000 | head -20 || echo "Frontend not responding"
echo ""

echo "=== 8. Test Backend Direct Access ==="
docker-compose -f docker-compose.server.yml exec -T backend python -c "import requests; r=requests.get('http://localhost:8000/api/v1/products/stats/'); print(f'Status: {r.status_code}'); print(r.text[:200])" 2>/dev/null || echo "Backend not responding"
echo ""

echo "=== 9. Docker Network Status ==="
docker network ls
echo ""

echo "=== 10. Container Resource Usage ==="
docker stats --no-stream
echo ""

echo "=== Diagnostics Complete ==="