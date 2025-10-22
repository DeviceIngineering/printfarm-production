"""
SimplePrint Views

Включает webhook endpoint для приема событий от SimplePrint.
"""

import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.utils import timezone

from .models import SimplePrintWebhookEvent, SimplePrintFile, SimplePrintFolder
from .services import SimplePrintSyncService

logger = logging.getLogger(__name__)


class SimplePrintWebhookView(APIView):
    """
    Webhook endpoint для приема событий от SimplePrint

    POST /api/v1/simpleprint/webhook/
    """
    permission_classes = [AllowAny]  # SimplePrint не поддерживает аутентификацию webhooks

    def post(self, request):
        """
        Обработать webhook от SimplePrint

        Ожидаемые события:
        - file_created: создан новый файл
        - file_updated: файл обновлен
        - file_deleted: файл удален
        - folder_created: создана папка
        - folder_deleted: папка удалена
        """
        try:
            payload = request.data
            logger.info(f"Received webhook: {payload}")

            # Определяем тип события
            event_type = self._detect_event_type(payload)

            # Сохраняем webhook событие
            webhook_event = SimplePrintWebhookEvent.objects.create(
                event_type=event_type,
                payload=payload
            )

            # Обрабатываем событие
            try:
                self._process_webhook_event(webhook_event)
                webhook_event.processed = True
                webhook_event.processed_at = timezone.now()
                webhook_event.save()

                logger.info(f"Webhook processed successfully: {event_type}")

            except Exception as e:
                logger.error(f"Failed to process webhook: {e}", exc_info=True)
                webhook_event.processing_error = str(e)
                webhook_event.save()

            return Response({
                'status': 'received',
                'event_type': event_type,
                'message': 'Webhook processed successfully'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Webhook processing failed: {e}", exc_info=True)
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _detect_event_type(self, payload: dict) -> str:
        """
        Определить тип события из payload

        Args:
            payload: данные webhook

        Returns:
            Тип события
        """
        # SimplePrint может отправлять event_type в payload
        if 'event_type' in payload:
            return payload['event_type']

        # Или определяем по структуре данных
        if 'file' in payload:
            if payload.get('action') == 'created':
                return 'file_created'
            elif payload.get('action') == 'updated':
                return 'file_updated'
            elif payload.get('action') == 'deleted':
                return 'file_deleted'

        if 'folder' in payload:
            if payload.get('action') == 'created':
                return 'folder_created'
            elif payload.get('action') == 'deleted':
                return 'folder_deleted'

        return 'unknown'

    def _process_webhook_event(self, webhook_event: SimplePrintWebhookEvent):
        """
        Обработать webhook событие

        Args:
            webhook_event: объект SimplePrintWebhookEvent
        """
        event_type = webhook_event.event_type
        payload = webhook_event.payload

        if event_type == 'file_created':
            self._handle_file_created(payload)
        elif event_type == 'file_updated':
            self._handle_file_updated(payload)
        elif event_type == 'file_deleted':
            self._handle_file_deleted(payload)
        elif event_type == 'folder_created':
            self._handle_folder_created(payload)
        elif event_type == 'folder_deleted':
            self._handle_folder_deleted(payload)
        else:
            logger.warning(f"Unknown event type: {event_type}")

    def _handle_file_created(self, payload: dict):
        """Обработать создание файла"""
        file_id = payload.get('file', {}).get('id')
        if file_id:
            logger.info(f"File created: {file_id}")
            # Запускаем синхронизацию этого файла
            # В идеале здесь должна быть асинхронная задача
            # service = SimplePrintSyncService()
            # service.sync_single_file(file_id)

    def _handle_file_updated(self, payload: dict):
        """Обработать обновление файла"""
        file_id = payload.get('file', {}).get('id')
        if file_id:
            logger.info(f"File updated: {file_id}")
            # Обновляем файл в БД
            try:
                file = SimplePrintFile.objects.get(simpleprint_id=file_id)
                # Обновляем метаданные из payload если доступны
                file.last_synced_at = timezone.now()
                file.save()
            except SimplePrintFile.DoesNotExist:
                logger.warning(f"File {file_id} not found in database")

    def _handle_file_deleted(self, payload: dict):
        """Обработать удаление файла"""
        file_id = payload.get('file', {}).get('id')
        if file_id:
            logger.info(f"File deleted: {file_id}")
            try:
                file = SimplePrintFile.objects.get(simpleprint_id=file_id)
                file.delete()
                logger.info(f"Deleted file {file_id} from database")
            except SimplePrintFile.DoesNotExist:
                logger.warning(f"File {file_id} not found in database")

    def _handle_folder_created(self, payload: dict):
        """Обработать создание папки"""
        folder_id = payload.get('folder', {}).get('id')
        if folder_id:
            logger.info(f"Folder created: {folder_id}")
            # Синхронизируем папку
            # service = SimplePrintSyncService()
            # service.sync_single_folder(folder_id)

    def _handle_folder_deleted(self, payload: dict):
        """Обработать удаление папки"""
        folder_id = payload.get('folder', {}).get('id')
        if folder_id:
            logger.info(f"Folder deleted: {folder_id}")
            try:
                folder = SimplePrintFolder.objects.get(simpleprint_id=folder_id)
                folder.delete()  # CASCADE удалит все файлы в папке
                logger.info(f"Deleted folder {folder_id} from database")
            except SimplePrintFolder.DoesNotExist:
                logger.warning(f"Folder {folder_id} not found in database")
