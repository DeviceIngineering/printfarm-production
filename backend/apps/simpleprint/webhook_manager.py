"""
SimplePrint Webhook Manager

Управление регистрацией и обновлением webhooks в SimplePrint API
"""

import logging
from typing import List, Dict, Optional
from django.conf import settings
from .client import SimplePrintFilesClient

logger = logging.getLogger(__name__)


class SimplePrintWebhookManager:
    """
    Менеджер для настройки webhooks в SimplePrint

    Позволяет:
    - Просматривать зарегистрированные webhooks
    - Создавать новые webhooks
    - Включать/выключать webhooks
    - Тестировать webhooks (manual trigger)
    """

    def __init__(self):
        self.client = SimplePrintFilesClient()
        # Получаем базовый URL из настроек или используем дефолтный
        self.webhook_base_url = getattr(settings, 'SIMPLEPRINT_WEBHOOK_URL', 'http://kemomail3.keenetic.pro:18001')

    def list_webhooks(self) -> List[Dict]:
        """
        Получить список зарегистрированных webhooks

        Returns:
            List[Dict]: Список webhooks
        """
        try:
            response = self.client._make_request('GET', 'webhooks/List')
            return response.get('webhooks', [])
        except Exception as e:
            logger.error(f"Failed to list webhooks: {e}")
            return []

    def register_printer_webhooks(self) -> Dict:
        """
        Зарегистрировать webhooks для событий принтеров

        События для отслеживания:
        - printer.online: принтер стал онлайн
        - printer.offline: принтер ушел в оффлайн
        - job.started: начало печати задания
        - job.completed: завершение печати
        - job.cancelled: отмена задания
        - job.failed: ошибка печати
        - job.progress: обновление прогресса (каждые 10%)
        - queue.changed: изменение очереди

        Returns:
            Dict: Результат регистрации
        """
        webhook_url = f"{self.webhook_base_url}/api/v1/simpleprint/webhook/printers/"

        # События которые хотим отслеживать
        events = [
            'printer.online',
            'printer.offline',
            'job.started',
            'job.completed',
            'job.cancelled',
            'job.failed',
            'job.progress',
            'queue.changed',
        ]

        try:
            # Проверяем существующие webhooks
            existing = self.list_webhooks()
            existing_urls = [w.get('url') for w in existing]

            if webhook_url in existing_urls:
                logger.info(f"Webhook already registered: {webhook_url}")
                return {
                    'status': 'exists',
                    'url': webhook_url,
                    'message': 'Webhook уже зарегистрирован'
                }

            # Регистрируем новый webhook
            data = {
                'url': webhook_url,
                'events': events,
                'enabled': True,
                'description': 'PrintFarm Planning V2 - Printer Events'
            }

            response = self.client._make_request('POST', 'webhooks/CreateOrUpdate', data=data)
            logger.info(f"✅ Webhook registered successfully: {webhook_url}")

            return {
                'status': 'created',
                'url': webhook_url,
                'events': events,
                'message': 'Webhook успешно зарегистрирован',
                'response': response
            }

        except Exception as e:
            logger.error(f"❌ Failed to register webhook: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'message': f'Ошибка регистрации webhook: {str(e)}'
            }

    def enable_webhook(self, webhook_id: str, enabled: bool = True) -> bool:
        """
        Включить/выключить webhook

        Args:
            webhook_id: ID webhook
            enabled: True - включить, False - выключить

        Returns:
            bool: Успешность операции
        """
        try:
            data = {
                'webhook_id': webhook_id,
                'enabled': enabled
            }
            response = self.client._make_request('POST', 'webhooks/SetEnabled', data=data)
            return response.get('status', False)
        except Exception as e:
            logger.error(f"Failed to enable/disable webhook: {e}")
            return False

    def test_webhook(self, webhook_id: str) -> Dict:
        """
        Протестировать webhook (ручной триггер)

        Args:
            webhook_id: ID webhook для тестирования

        Returns:
            Dict: Результат теста
        """
        try:
            data = {'webhook_id': webhook_id}
            response = self.client._make_request('POST', 'webhooks/Trigger', data=data)
            return {
                'status': response.get('status', False),
                'message': 'Webhook успешно отправлен' if response.get('status') else 'Ошибка отправки webhook',
                'response': response
            }
        except Exception as e:
            logger.error(f"Failed to test webhook: {e}")
            return {
                'status': False,
                'error': str(e),
                'message': f'Ошибка тестирования webhook: {str(e)}'
            }

    def delete_webhook(self, webhook_id: str) -> Dict:
        """
        Удалить webhook

        Args:
            webhook_id: ID webhook для удаления

        Returns:
            Dict: Результат удаления
        """
        try:
            data = {'webhook_id': webhook_id}
            response = self.client._make_request('POST', 'webhooks/Delete', data=data)
            return {
                'status': response.get('status', False),
                'message': 'Webhook успешно удален' if response.get('status') else 'Ошибка удаления webhook',
                'response': response
            }
        except Exception as e:
            logger.error(f"Failed to delete webhook: {e}")
            return {
                'status': False,
                'error': str(e),
                'message': f'Ошибка удаления webhook: {str(e)}'
            }
