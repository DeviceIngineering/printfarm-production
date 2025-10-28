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
from django.conf import settings

from .models import SimplePrintWebhookEvent, SimplePrintFile, SimplePrintFolder, SimplePrintSync, PrinterSnapshot
from .services import SimplePrintSyncService, PrinterSyncService
from .serializers import (
    SimplePrintFileSerializer, SimplePrintFileListSerializer,
    SimplePrintFolderSerializer, SimplePrintFolderListSerializer,
    SimplePrintSyncSerializer, SimplePrintWebhookEventSerializer,
    SyncStatsSerializer, TriggerSyncSerializer,
    PrinterSnapshotSerializer, PrinterSyncResultSerializer, PrinterStatsSerializer,
    PrinterWebhookEventSerializer
)

logger = logging.getLogger(__name__)


class SimplePrintFilePagination(PageNumberPagination):
    """Custom pagination с возможностью изменения page_size"""
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 2000  # Увеличено для загрузки всех файлов (1587 на 2025-10-23)


class SimplePrintWebhookView(APIView):
    """
    Webhook endpoint для приема событий от SimplePrint

    POST /api/v1/simpleprint/webhook/

    Формат payload от SimplePrint:
    {
        "webhook_id": int,
        "event": string,      # например: "job.started", "job.finished"
        "timestamp": int,     # Unix timestamp
        "data": object       # данные события (job, printer, user, и т.д.)
    }

    Поддерживаемые события:
    - job.started: печать началась
    - job.finished: печать завершена
    - job.paused: печать на паузе
    - job.resumed: печать возобновлена
    - job.failed: печать провалена
    - queue.item_added: добавлен элемент в очередь
    - queue.item_deleted: удален элемент из очереди
    - queue.item_moved: перемещен элемент в очереди
    - file.created: файл создан (старый формат)
    - file.deleted: файл удален (старый формат)
    """
    permission_classes = [AllowAny]  # SimplePrint webhooks не используют auth

    def post(self, request):
        """
        Обработать webhook от SimplePrint

        SimplePrint отправляет:
        - Header: X-SP-Token (опционально, если настроен secret)
        - Body: JSON с полями webhook_id, event, timestamp, data
        """
        try:
            payload = request.data

            # Проверяем secret token если настроен
            expected_token = getattr(settings, 'SIMPLEPRINT_WEBHOOK_SECRET', None)
            if expected_token:
                received_token = request.headers.get('X-SP-Token') or request.headers.get('X-Sp-Token')
                if received_token != expected_token:
                    logger.warning(f"Invalid webhook token received")
                    return Response({
                        'status': 'error',
                        'message': 'Invalid token'
                    }, status=status.HTTP_401_UNAUTHORIZED)

            # Извлекаем поля SimplePrint
            webhook_id = payload.get('webhook_id')
            event = payload.get('event', 'unknown')
            timestamp = payload.get('timestamp')
            data = payload.get('data', {})

            logger.info(f"📨 Received SimplePrint webhook: event={event}, webhook_id={webhook_id}, timestamp={timestamp}")

            # Маппинг событий SimplePrint к нашим типам
            event_mapping = {
                # Тестовое событие
                'test': 'test',
                # События заданий печати
                'job.started': 'job_started',
                'job.finished': 'job_completed',
                'job.done': 'job_completed',  # Альтернативное название для job.finished
                'job.paused': 'job_paused',
                'job.resumed': 'job_resumed',
                'job.failed': 'job_failed',
                'job.bed_cleared': 'job_completed',  # Стол очищен = задание завершено
                # События очереди
                'queue.changed': 'queue_changed',
                'queue.add_item': 'queue_changed',  # Альтернативное название
                'queue.item_added': 'queue_changed',
                'queue.item_deleted': 'queue_changed',
                'queue.item_moved': 'queue_changed',
                # События принтера
                'printer.online': 'printer_online',
                'printer.offline': 'printer_offline',
                'printer.state_changed': 'printer_state_changed',
                'printer.material_changed': 'printer_state_changed',  # Изменение материала
                # События файлов
                'file.created': 'file_created',
                'file.deleted': 'file_deleted',
            }

            our_event_type = event_mapping.get(event, 'unknown')

            # Сохраняем webhook событие
            from .models import PrinterWebhookEvent

            # Извлекаем printer_id и job_id из data
            printer_id = None
            job_id = None

            if 'job' in data and isinstance(data['job'], dict):
                job_id = str(data['job'].get('id', ''))
                printer_id = str(data['job'].get('printer_id', ''))

            webhook_event = PrinterWebhookEvent.objects.create(
                event_type=our_event_type,
                printer_id=printer_id,
                job_id=job_id,
                payload=payload
            )

            # Обрабатываем событие
            try:
                self._process_webhook_event(webhook_event, event, data)
                webhook_event.processed = True
                webhook_event.processed_at = timezone.now()
                webhook_event.save()

                logger.info(f"✅ Webhook processed successfully: {event}")

            except Exception as e:
                logger.error(f"❌ Failed to process webhook: {e}", exc_info=True)
                webhook_event.processing_error = str(e)
                webhook_event.save()

            return Response({
                'status': 'received',
                'event': event,
                'message': 'Webhook processed successfully'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"❌ Webhook processing failed: {e}", exc_info=True)
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _process_webhook_event(self, webhook_event, event: str, data: dict):
        """
        Обработать webhook событие SimplePrint

        Args:
            webhook_event: объект PrinterWebhookEvent
            event: тип события от SimplePrint (job.started, и т.д.)
            data: данные события
        """
        # Тестовое событие от SimplePrint
        if event == 'test':
            logger.info(f"✅ Test webhook received successfully")
            return

        # Обработка событий печати
        if event.startswith('job.'):
            self._handle_job_event(event, data)

        # Обработка событий очереди
        elif event.startswith('queue.'):
            self._handle_queue_event(event, data)

        # Обработка событий принтера
        elif event.startswith('printer.'):
            self._handle_printer_event(event, data)

        # Старый формат - файлы
        elif event.startswith('file.'):
            self._handle_file_event(event, data)

        else:
            logger.warning(f"⚠️ Unknown event type: {event}")

    def _handle_job_event(self, event: str, data: dict):
        """Обработать событие задания"""
        job_data = data.get('job', {})
        if not job_data:
            return

        from .models import PrintJob, PrinterSnapshot

        job_id = str(job_data.get('id', ''))
        printer_id = str(job_data.get('printer_id', ''))

        logger.info(f"🖨️ Processing job event: {event} for job_id={job_id}, printer_id={printer_id}")

        # Обновляем или создаем запись задания
        if event == 'job.started':
            PrintJob.objects.update_or_create(
                job_id=job_id,
                defaults={
                    'printer_id': printer_id,
                    'printer_name': job_data.get('printer_name', ''),
                    'file_name': job_data.get('file_name', ''),
                    'status': 'printing',
                    'started_at': timezone.now(),
                    'raw_data': job_data
                }
            )

        elif event == 'job.finished':
            PrintJob.objects.filter(job_id=job_id).update(
                status='completed',
                completed_at=timezone.now(),
                success=True,
                percentage=100
            )

        elif event == 'job.failed':
            PrintJob.objects.filter(job_id=job_id).update(
                status='failed',
                completed_at=timezone.now(),
                success=False,
                error_message=job_data.get('error', '')
            )

    def _handle_queue_event(self, event: str, data: dict):
        """Обработать событие очереди"""
        logger.info(f"📋 Processing queue event: {event}")
        # TODO: Реализовать обработку очереди

    def _handle_printer_event(self, event: str, data: dict):
        """Обработать событие принтера"""
        logger.info(f"🖨️ Processing printer event: {event}")
        # TODO: Реализовать обработку принтера

    def _handle_file_event(self, event: str, data: dict):
        """Обработать событие файла (старый формат)"""
        logger.info(f"📁 Processing file event: {event}")
        # Оставляем старую логику для совместимости

    def _detect_event_type(self, payload: dict) -> str:
        """
        DEPRECATED: Старый метод определения типа события
        Оставлен для обратной совместимости
        """
        # SimplePrint новый формат использует поле 'event'
        if 'event' in payload:
            return payload['event']

        # Старый формат
        if 'event_type' in payload:
            return payload['event_type']

        # Fallback - старая логика
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

        # Логируем полученные параметры
        logger.info(f"🔍 Sync trigger request: full_sync={full_sync}, force={force}, user={request.user.username}")

        # Проверяем последнюю синхронизацию
        service = SimplePrintSyncService()
        stats = service.get_sync_stats()

        # Логируем статистику для диагностики
        logger.info(f"📊 Stats: last_sync={stats.get('last_sync')}, status={stats.get('last_sync_status')}")

        if stats['last_sync'] and not force:
            time_since_last = timezone.now() - stats['last_sync']
            seconds_since_last = int(time_since_last.total_seconds())

            if time_since_last.total_seconds() < 300:  # 5 минут
                logger.warning(f"⏱️ Cooldown ACTIVE: {seconds_since_last}s < 300s. Returning 429. Force={force}")
                return Response({
                    'status': 'rejected',
                    'message': f'Последняя синхронизация была {seconds_since_last} секунд назад. Используйте force=true для принудительной синхронизации.',
                    'last_sync': stats['last_sync']
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)
            else:
                logger.info(f"✅ Cooldown passed: {seconds_since_last}s >= 300s")

        try:
            # Запускаем асинхронную задачу синхронизации
            from .tasks import sync_simpleprint_task

            task = sync_simpleprint_task.delay(full_sync=full_sync)

            logger.info(f"✅ Sync started: task_id={task.id}, full_sync={full_sync}")

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


class PrinterSyncView(APIView):
    """
    API для синхронизации принтеров из SimplePrint
    """
    permission_classes = [AllowAny]  # TODO: Add authentication

    def post(self, request):
        """Запустить синхронизацию принтеров"""
        try:
            service = PrinterSyncService()
            results = service.sync_printers()

            serializer = PrinterSyncResultSerializer(results)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Printer sync failed: {e}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PrinterSnapshotsView(APIView):
    """
    API для получения снимков принтеров
    """
    permission_classes = [AllowAny]  # TODO: Add authentication

    def get(self, request):
        """Получить последние снимки всех принтеров (с кэшированием)"""
        try:
            service = PrinterSyncService()

            # Пытаемся получить из кэша или БД
            snapshots = service.get_latest_snapshots()

            if not snapshots:
                # Если нет данных, пробуем синхронизировать
                logger.info("No snapshots found, attempting sync...")
                try:
                    service.sync_printers()
                    snapshots = service.get_latest_snapshots()
                except Exception as sync_error:
                    logger.warning(f"Sync failed: {sync_error}")
                    # Возвращаем пустой массив если синхронизация не удалась
                    return Response([], status=status.HTTP_200_OK)

            serializer = PrinterSnapshotSerializer(snapshots, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Failed to fetch printer snapshots: {e}", exc_info=True)
            # В случае ошибки возвращаем пустой массив
            return Response([], status=status.HTTP_200_OK)


class PrinterStatsView(APIView):
    """
    API для получения статистики принтеров
    """
    permission_classes = [AllowAny]  # TODO: Add authentication

    def get(self, request):
        """Получить статистику принтеров"""
        try:
            service = PrinterSyncService()
            stats = service.get_printer_stats()

            serializer = PrinterStatsSerializer(stats)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Failed to fetch printer stats: {e}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ============================================================================
# Webhook Testing API Views
# ============================================================================

class WebhookEventsListView(APIView):
    """
    API для получения списка webhook событий

    GET /api/v1/simpleprint/webhook/events/

    Query параметры:
    - limit: количество событий (default: 20, max: 100)
    - event_type: фильтр по типу события
    - printer_id: фильтр по принтеру
    - processed: фильтр по статусу обработки (true/false)
    """
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Получить список webhook событий"""
        try:
            from .models import PrinterWebhookEvent

            # Параметры запроса
            limit = int(request.query_params.get('limit', 20))
            limit = min(limit, 100)  # Максимум 100

            event_type = request.query_params.get('event_type')
            printer_id = request.query_params.get('printer_id')
            processed = request.query_params.get('processed')

            # Базовый queryset
            queryset = PrinterWebhookEvent.objects.all()

            # Фильтры
            if event_type:
                queryset = queryset.filter(event_type=event_type)
            if printer_id:
                queryset = queryset.filter(printer_id=printer_id)
            if processed is not None:
                processed_bool = processed.lower() == 'true'
                queryset = queryset.filter(processed=processed_bool)

            # Сортировка по времени (последние первыми)
            queryset = queryset.order_by('-received_at')[:limit]

            serializer = PrinterWebhookEventSerializer(queryset, many=True)

            return Response({
                'count': queryset.count(),
                'events': serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Failed to fetch webhook events: {e}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class WebhookStatsView(APIView):
    """
    API для получения статистики webhook событий

    GET /api/v1/simpleprint/webhook/stats/

    Возвращает:
    - total: общее количество событий
    - processed: количество обработанных
    - errors: количество с ошибками
    - by_type: статистика по типам событий
    - last_hour: события за последний час
    - last_24h: события за последние 24 часа
    """
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Получить статистику webhook событий"""
        try:
            from .models import PrinterWebhookEvent
            from django.db.models import Count, Q
            from datetime import timedelta

            now = timezone.now()
            one_hour_ago = now - timedelta(hours=1)
            one_day_ago = now - timedelta(hours=24)

            # Общая статистика
            total = PrinterWebhookEvent.objects.count()
            processed = PrinterWebhookEvent.objects.filter(processed=True).count()
            errors = PrinterWebhookEvent.objects.filter(
                processing_error__isnull=False
            ).count()

            # Статистика по типам событий
            by_type = {}
            type_stats = PrinterWebhookEvent.objects.values('event_type').annotate(
                count=Count('id')
            ).order_by('-count')

            for stat in type_stats:
                by_type[stat['event_type']] = stat['count']

            # События за последний час
            last_hour = PrinterWebhookEvent.objects.filter(
                received_at__gte=one_hour_ago
            ).count()

            # События за последние 24 часа
            last_24h = PrinterWebhookEvent.objects.filter(
                received_at__gte=one_day_ago
            ).count()

            # Последнее событие
            last_event = PrinterWebhookEvent.objects.order_by('-received_at').first()
            last_event_time = last_event.received_at if last_event else None

            return Response({
                'total': total,
                'processed': processed,
                'errors': errors,
                'by_type': by_type,
                'last_hour': last_hour,
                'last_24h': last_24h,
                'last_event_at': last_event_time,
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Failed to fetch webhook stats: {e}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class WebhookTestTriggerView(APIView):
    """
    API для отправки тестового webhook события

    POST /api/v1/simpleprint/webhook/test-trigger/

    Body:
    {
        "event_type": "job.started" | "job.finished" | "printer.state_changed" | etc.
    }
    """
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Отправить тестовый webhook"""
        try:
            import requests
            import time

            event_type = request.data.get('event_type', 'test')

            # Создаем тестовый payload в формате SimplePrint
            test_payload = {
                'webhook_id': 999999,
                'event': event_type,
                'timestamp': int(time.time()),
                'data': {
                    'test': True,
                    'triggered_by': 'frontend_ui',
                    'user': request.user.username if request.user else 'anonymous'
                }
            }

            # Добавляем специфичные для события данные
            if event_type.startswith('job.'):
                test_payload['data']['job'] = {
                    'id': f'test_job_{int(time.time())}',
                    'name': 'test_model.gcode',
                    'started': int(time.time()),
                }
                test_payload['data']['printer'] = {
                    'id': 'test_printer_001',
                    'name': 'Test Printer #1'
                }
            elif event_type.startswith('printer.'):
                test_payload['data']['printer'] = {
                    'id': 'test_printer_001',
                    'name': 'Test Printer #1',
                    'state': 'operational'
                }
            elif event_type.startswith('queue.'):
                test_payload['data']['printer'] = {
                    'id': 'test_printer_001',
                    'name': 'Test Printer #1'
                }
                test_payload['data']['queue'] = {
                    'id': 'test_queue_001',
                    'items': []
                }

            # Отправляем на наш webhook endpoint
            webhook_url = request.build_absolute_uri('/api/v1/simpleprint/webhook/')

            response = requests.post(
                webhook_url,
                json=test_payload,
                timeout=5
            )

            return Response({
                'status': 'sent',
                'webhook_url': webhook_url,
                'payload': test_payload,
                'response_status': response.status_code,
                'response_data': response.json() if response.ok else response.text
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Failed to trigger test webhook: {e}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class WebhookClearOldEventsView(APIView):
    """
    API для очистки старых webhook событий

    DELETE /api/v1/simpleprint/webhook/events/clear/

    Query параметры:
    - days: удалить события старше N дней (default: 7)
    """
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        """Очистить старые webhook события"""
        try:
            from .models import PrinterWebhookEvent
            from datetime import timedelta

            days = int(request.query_params.get('days', 7))
            cutoff_date = timezone.now() - timedelta(days=days)

            # Удаляем только обработанные события без ошибок
            deleted_count, _ = PrinterWebhookEvent.objects.filter(
                received_at__lt=cutoff_date,
                processed=True,
                processing_error__isnull=True
            ).delete()

            return Response({
                'status': 'success',
                'deleted_count': deleted_count,
                'cutoff_date': cutoff_date,
                'message': f'Deleted {deleted_count} events older than {days} days'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Failed to clear old webhook events: {e}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
