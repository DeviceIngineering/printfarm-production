"""
SimplePrint Views

Включает webhook endpoint и REST API endpoints для SimplePrint.
"""

import logging
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework import filters
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

from .models import SimplePrintWebhookEvent, SimplePrintFile, SimplePrintFolder, SimplePrintSync
from .services import SimplePrintSyncService
from .serializers import (
    SimplePrintFileSerializer, SimplePrintFileListSerializer,
    SimplePrintFolderSerializer, SimplePrintFolderListSerializer,
    SimplePrintSyncSerializer, SimplePrintWebhookEventSerializer,
    SyncStatsSerializer, TriggerSyncSerializer
)

logger = logging.getLogger(__name__)


class SimplePrintFilePagination(PageNumberPagination):
    """Custom pagination с возможностью изменения page_size"""
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 500


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


class SimplePrintFileViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для просмотра файлов SimplePrint

    GET /api/v1/simpleprint/files/ - список файлов
    GET /api/v1/simpleprint/files/{id}/ - детали файла
    GET /api/v1/simpleprint/files/stats/ - статистика файлов
    """
    queryset = SimplePrintFile.objects.select_related('folder').all()
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = SimplePrintFilePagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['folder', 'file_type', 'ext']
    search_fields = ['name', 'simpleprint_id']
    ordering_fields = ['name', 'size', 'created_at_sp', 'last_synced_at']
    ordering = ['-created_at_sp']

    def get_serializer_class(self):
        """Выбрать serializer в зависимости от action"""
        if self.action == 'list':
            return SimplePrintFileListSerializer
        return SimplePrintFileSerializer

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Статистика по файлам"""
        total_files = self.get_queryset().count()
        total_size = sum(f.size for f in self.get_queryset())

        # Группировка по типам
        by_type = {}
        for file in self.get_queryset():
            file_type = file.file_type or 'unknown'
            if file_type not in by_type:
                by_type[file_type] = {'count': 0, 'size': 0}
            by_type[file_type]['count'] += 1
            by_type[file_type]['size'] += file.size

        return Response({
            'total_files': total_files,
            'total_size': total_size,
            'by_type': by_type
        })


class SimplePrintFolderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для просмотра папок SimplePrint

    GET /api/v1/simpleprint/folders/ - список папок
    GET /api/v1/simpleprint/folders/{id}/ - детали папки
    GET /api/v1/simpleprint/folders/{id}/files/ - файлы в папке
    """
    queryset = SimplePrintFolder.objects.all()
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['parent', 'depth']
    search_fields = ['name', 'simpleprint_id']
    ordering_fields = ['name', 'depth', 'files_count', 'last_synced_at']
    ordering = ['depth', 'name']

    def get_serializer_class(self):
        """Выбрать serializer в зависимости от action"""
        if self.action == 'list':
            return SimplePrintFolderListSerializer
        return SimplePrintFolderSerializer

    @action(detail=True, methods=['get'])
    def files(self, request, pk=None):
        """Получить файлы в папке"""
        folder = self.get_object()
        files = folder.files.all()
        serializer = SimplePrintFileListSerializer(files, many=True)
        return Response(serializer.data)


class SimplePrintSyncViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для просмотра истории синхронизаций

    GET /api/v1/simpleprint/sync/ - история синхронизаций
    GET /api/v1/simpleprint/sync/{id}/ - детали синхронизации
    POST /api/v1/simpleprint/sync/trigger/ - запустить синхронизацию
    GET /api/v1/simpleprint/sync/stats/ - статистика синхронизации
    """
    queryset = SimplePrintSync.objects.all()
    serializer_class = SimplePrintSyncSerializer
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]
    ordering = ['-started_at']

    @action(detail=False, methods=['post'])
    def trigger(self, request):
        """
        Запустить синхронизацию

        Body:
        {
            "full_sync": false,  // полная синхронизация с удалением
            "force": false       // принудительная синхронизация
        }
        """
        serializer = TriggerSyncSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        full_sync = serializer.validated_data.get('full_sync', False)
        force = serializer.validated_data.get('force', False)

        # Проверяем последнюю синхронизацию
        service = SimplePrintSyncService()
        stats = service.get_sync_stats()

        if stats['last_sync'] and not force:
            time_since_last = timezone.now() - stats['last_sync']
            if time_since_last.total_seconds() < 300:  # 5 минут
                return Response({
                    'status': 'rejected',
                    'message': f'Последняя синхронизация была {int(time_since_last.total_seconds())} секунд назад. Используйте force=true для принудительной синхронизации.',
                    'last_sync': stats['last_sync']
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)

        try:
            # Запускаем асинхронную задачу синхронизации
            from .tasks import sync_simpleprint_task

            task = sync_simpleprint_task.delay(full_sync=full_sync)

            return Response({
                'status': 'started',
                'task_id': task.id,
                'message': 'Синхронизация запущена в фоновом режиме'
            }, status=status.HTTP_202_ACCEPTED)

        except Exception as e:
            logger.error(f"Failed to start sync: {e}", exc_info=True)
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Статистика синхронизации"""
        service = SimplePrintSyncService()
        stats = service.get_sync_stats()

        serializer = SyncStatsSerializer(stats)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='status/(?P<task_id>[^/.]+)')
    def task_status(self, request, task_id=None):
        """
        Получить статус задачи синхронизации

        GET /api/v1/simpleprint/sync/status/{task_id}/
        """
        from celery.result import AsyncResult

        task = AsyncResult(task_id)

        response_data = {
            'task_id': task_id,
            'state': task.state,
            'ready': task.ready(),
        }

        if task.ready():
            if task.successful():
                response_data['result'] = task.result
                # Получаем полные данные синхронизации
                if 'sync_id' in task.result:
                    try:
                        sync_log = SimplePrintSync.objects.get(id=task.result['sync_id'])
                        response_data['sync_log'] = SimplePrintSyncSerializer(sync_log).data
                    except SimplePrintSync.DoesNotExist:
                        pass
            else:
                response_data['error'] = str(task.info)
        else:
            # Проверяем последнюю синхронизацию для прогресса
            latest_sync = SimplePrintSync.objects.filter(status='pending').first()
            if latest_sync:
                response_data['progress'] = {
                    'total_files': latest_sync.total_files,
                    'synced_files': latest_sync.synced_files,
                    'total_folders': latest_sync.total_folders,
                    'synced_folders': latest_sync.synced_folders,
                }

        return Response(response_data)

    @action(detail=False, methods=['post'], url_path='cancel')
    def cancel_sync(self, request):
        """
        Отменить задачу синхронизации

        POST /api/v1/simpleprint/sync/cancel/
        Body: {"task_id": "..."}
        """
        from celery.result import AsyncResult

        task_id = request.data.get('task_id')
        if not task_id:
            return Response({
                'status': 'error',
                'message': 'task_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            task = AsyncResult(task_id)

            logger.info(f"Attempting to cancel task: {task_id}, state: {task.state}")

            # Отменяем задачу
            task.revoke(terminate=True, signal='SIGKILL')

            # Обновляем статус синхронизации в БД
            try:
                latest_sync = SimplePrintSync.objects.filter(status='pending').first()
                if latest_sync:
                    latest_sync.status = 'cancelled'
                    latest_sync.finished_at = timezone.now()
                    latest_sync.save()
                    logger.info(f"Updated sync log {latest_sync.id} status to cancelled")
            except Exception as e:
                logger.error(f"Failed to update sync log: {e}")

            return Response({
                'status': 'cancelled',
                'task_id': task_id,
                'message': 'Задача синхронизации отменена'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Failed to cancel task {task_id}: {e}", exc_info=True)
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
