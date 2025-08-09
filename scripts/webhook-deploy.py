#!/usr/bin/env python3
"""
Webhook endpoint для автоматического развертывания PrintFarm
Принимает webhook'и от GitHub и запускает развертывание
"""

import json
import logging
import subprocess
import hmac
import hashlib
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import time
from datetime import datetime

# Настройки
WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET', 'your-webhook-secret')
WEBHOOK_PORT = int(os.environ.get('WEBHOOK_PORT', '9000'))
DEPLOY_SCRIPT = '/opt/printfarm/scripts/deploy.sh'
LOG_FILE = '/opt/printfarm/logs/webhook.log'
ALLOWED_BRANCHES = ['test_v1', 'main']
DEPLOY_USER = 'printfarm'
MAX_CONCURRENT_DEPLOYS = 1

# Состояние развертываний
active_deploys = set()
deploy_lock = threading.Lock()

# Настройка логирования
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class WebhookHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        """Переопределяем для использования нашего логгера"""
        logger.info(f"{self.address_string()} - {format % args}")

    def do_GET(self):
        """Обработка GET запросов - health check"""
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            status = {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'active_deploys': len(active_deploys),
                'webhook_secret_configured': bool(WEBHOOK_SECRET and WEBHOOK_SECRET != 'your-webhook-secret')
            }
            
            self.wfile.write(json.dumps(status, indent=2).encode())
            return
        
        # Для всех остальных GET запросов
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        """Обработка POST запросов - webhook'и"""
        try:
            if self.path != '/webhook':
                self.send_response(404)
                self.end_headers()
                return

            # Читаем данные
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            # Проверка подписи GitHub
            if not self.verify_signature(post_data):
                logger.warning(f"Invalid signature from {self.client_address[0]}")
                self.send_response(401)
                self.end_headers()
                return

            # Парсим JSON
            try:
                payload = json.loads(post_data.decode('utf-8'))
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON: {e}")
                self.send_response(400)
                self.end_headers()
                return

            # Обрабатываем webhook
            if self.handle_webhook(payload):
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {'status': 'success', 'message': 'Deployment started'}
                self.wfile.write(json.dumps(response).encode())
            else:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {'status': 'ignored', 'message': 'No deployment needed'}
                self.wfile.write(json.dumps(response).encode())

        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            self.send_response(500)
            self.end_headers()

    def verify_signature(self, payload_body):
        """Проверяет подпись GitHub webhook"""
        if not WEBHOOK_SECRET or WEBHOOK_SECRET == 'your-webhook-secret':
            logger.warning("Webhook secret not configured, skipping signature verification")
            return True
            
        signature = self.headers.get('X-Hub-Signature-256')
        if not signature:
            return False

        expected_signature = 'sha256=' + hmac.new(
            WEBHOOK_SECRET.encode(),
            payload_body,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(signature, expected_signature)

    def handle_webhook(self, payload):
        """Обрабатывает webhook от GitHub"""
        try:
            # Проверяем, что это push event
            if payload.get('zen'):  # Ping event
                logger.info("Received GitHub ping event")
                return True
                
            if not payload.get('ref'):
                logger.info("Received non-push event, ignoring")
                return False

            # Извлекаем информацию о push
            branch = payload['ref'].replace('refs/heads/', '')
            repository = payload['repository']['full_name']
            commit = payload['head_commit']['id'][:8] if payload.get('head_commit') else 'unknown'
            
            logger.info(f"Received push to {repository}:{branch} ({commit})")

            # Проверяем, нужно ли развертывать этот branch
            if branch not in ALLOWED_BRANCHES:
                logger.info(f"Branch {branch} not in allowed branches {ALLOWED_BRANCHES}")
                return False

            # Запускаем развертывание в отдельном потоке
            deploy_thread = threading.Thread(
                target=self.run_deployment,
                args=(repository, branch, commit),
                daemon=True
            )
            deploy_thread.start()
            
            return True

        except Exception as e:
            logger.error(f"Error handling webhook: {e}")
            return False

    def run_deployment(self, repository, branch, commit):
        """Запускает процесс развертывания"""
        deploy_id = f"{branch}-{commit}-{int(time.time())}"
        
        with deploy_lock:
            if len(active_deploys) >= MAX_CONCURRENT_DEPLOYS:
                logger.warning(f"Max concurrent deploys reached, skipping {deploy_id}")
                return
            
            active_deploys.add(deploy_id)

        try:
            logger.info(f"Starting deployment {deploy_id}")
            
            # Создаем лог файл для этого развертывания
            deploy_log = f"/opt/printfarm/logs/deploy/webhook-{deploy_id}.log"
            os.makedirs(os.path.dirname(deploy_log), exist_ok=True)
            
            # Команда для развертывания
            cmd = [
                'sudo', 'su', '-', DEPLOY_USER, '-c',
                f'cd /opt/printfarm && ./scripts/deploy.sh > {deploy_log} 2>&1'
            ]
            
            # Запускаем развертывание
            start_time = time.time()
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)  # 10 минут timeout
            duration = time.time() - start_time
            
            if result.returncode == 0:
                logger.info(f"Deployment {deploy_id} completed successfully in {duration:.2f}s")
                
                # Сохраняем статус успешного развертывания
                status = {
                    'status': 'success',
                    'deploy_id': deploy_id,
                    'repository': repository,
                    'branch': branch,
                    'commit': commit,
                    'duration': duration,
                    'timestamp': datetime.now().isoformat(),
                    'log_file': deploy_log
                }
            else:
                logger.error(f"Deployment {deploy_id} failed with code {result.returncode}")
                logger.error(f"Error output: {result.stderr}")
                
                status = {
                    'status': 'failed',
                    'deploy_id': deploy_id,
                    'repository': repository,
                    'branch': branch,
                    'commit': commit,
                    'duration': duration,
                    'error_code': result.returncode,
                    'error': result.stderr,
                    'timestamp': datetime.now().isoformat(),
                    'log_file': deploy_log
                }
            
            # Сохраняем статус
            with open('/opt/printfarm/logs/last_deployment.json', 'w') as f:
                json.dump(status, f, indent=2)
                
        except subprocess.TimeoutExpired:
            logger.error(f"Deployment {deploy_id} timed out")
        except Exception as e:
            logger.error(f"Deployment {deploy_id} failed with exception: {e}")
        finally:
            active_deploys.discard(deploy_id)

def main():
    """Запуск webhook сервера"""
    logger.info(f"Starting webhook server on port {WEBHOOK_PORT}")
    logger.info(f"Deploy script: {DEPLOY_SCRIPT}")
    logger.info(f"Allowed branches: {ALLOWED_BRANCHES}")
    logger.info(f"Webhook secret configured: {bool(WEBHOOK_SECRET and WEBHOOK_SECRET != 'your-webhook-secret')}")
    
    # Проверяем наличие скрипта развертывания
    if not os.path.exists(DEPLOY_SCRIPT):
        logger.error(f"Deploy script not found: {DEPLOY_SCRIPT}")
        sys.exit(1)
    
    # Проверяем права на выполнение
    if not os.access(DEPLOY_SCRIPT, os.X_OK):
        logger.error(f"Deploy script is not executable: {DEPLOY_SCRIPT}")
        sys.exit(1)
    
    try:
        server = HTTPServer(('0.0.0.0', WEBHOOK_PORT), WebhookHandler)
        logger.info(f"Webhook server started successfully on http://0.0.0.0:{WEBHOOK_PORT}")
        logger.info("Endpoints:")
        logger.info("  POST /webhook - GitHub webhook")
        logger.info("  GET /health - Health check")
        
        server.serve_forever()
        
    except KeyboardInterrupt:
        logger.info("Shutting down webhook server")
        server.shutdown()
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()