"""
SimplePrint Synchronization Service

Сервис для синхронизации файлов и папок из SimplePrint в локальную БД.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from .client import SimplePrintFilesClient, SimplePrintAPIError
from .models import SimplePrintFolder, SimplePrintFile, SimplePrintSync

logger = logging.getLogger(__name__)


class SimplePrintSyncService:
    """
    Сервис для синхронизации данных из SimplePrint
    """

    def __init__(self):
        """Инициализация сервиса"""
        self.client = SimplePrintFilesClient()

    def sync_all_files(self, full_sync: bool = False) -> SimplePrintSync:
        """
        Синхронизировать все файлы и папки из SimplePrint

        Args:
            full_sync: Полная синхронизация (удалить отсутствующие файлы)

        Returns:
            Объект SimplePrintSync с результатами синхронизации
        """
        # Создаем запись о синхронизации
        sync_log = SimplePrintSync.objects.create(status='pending')

        try:
            logger.info("Starting SimplePrint synchronization")

            # Проверяем подключение
            if not self.client.test_connection():
                raise SimplePrintAPIError("Connection test failed")

            # Получаем все данные рекурсивно
            logger.info("Fetching all files and folders from SimplePrint...")
            data = self.client.get_all_files_recursive()

            all_folders = data['all_folders']
            all_files = data['all_files']

            sync_log.total_folders = len(all_folders)
            sync_log.total_files = len(all_files)
            sync_log.save()

            logger.info(f"Fetched {len(all_folders)} folders and {len(all_files)} files")

            # Синхронизируем папки
            logger.info("Synchronizing folders...")
            synced_folders = self._sync_folders(all_folders)
            sync_log.synced_folders = synced_folders
            sync_log.save()

            # Синхронизируем файлы
            logger.info("Synchronizing files...")
            synced_files = self._sync_files(all_files)
            sync_log.synced_files = synced_files
            sync_log.save()

            # Удаляем отсутствующие файлы (если full_sync)
            deleted_files = 0
            if full_sync:
                logger.info("Cleaning up deleted files...")
                deleted_files = self._cleanup_deleted_files(all_files)
                sync_log.deleted_files = deleted_files
                sync_log.save()

            # Завершаем синхронизацию
            sync_log.status = 'success'
            sync_log.finished_at = timezone.now()
            sync_log.save()

            logger.info(
                f"Synchronization completed: "
                f"{synced_folders} folders, {synced_files} files, {deleted_files} deleted"
            )

            return sync_log

        except Exception as e:
            logger.error(f"Synchronization failed: {e}", exc_info=True)

            sync_log.status = 'failed'
            sync_log.error_details = str(e)
            sync_log.finished_at = timezone.now()
            sync_log.save()

            raise

    def _sync_folders(self, folders_data: List[Dict]) -> int:
        """
        Синхронизировать папки

        Args:
            folders_data: Список данных папок из API

        Returns:
            Количество синхронизированных папок
        """
        synced_count = 0

        # Сортируем папки по уровню вложенности (depth)
        folders_data_sorted = sorted(folders_data, key=lambda x: x.get('depth', 0))

        for folder_data in folders_data_sorted:
            try:
                self._sync_folder(folder_data)
                synced_count += 1

                if synced_count % 50 == 0:
                    logger.info(f"Synced {synced_count}/{len(folders_data)} folders")

            except Exception as e:
                logger.error(f"Failed to sync folder {folder_data.get('id')}: {e}")

        return synced_count

    def _sync_folder(self, folder_data: Dict) -> SimplePrintFolder:
        """
        Синхронизировать одну папку

        Args:
            folder_data: Данные папки из API

        Returns:
            Объект SimplePrintFolder
        """
        sp_id = folder_data['id']
        name = folder_data['name']
        depth = folder_data.get('depth', 0)
        parent_id = folder_data.get('parent_folder_id', 0)

        # Получаем родительскую папку
        parent = None
        if parent_id and parent_id != 0:
            try:
                parent = SimplePrintFolder.objects.get(simpleprint_id=parent_id)
            except SimplePrintFolder.DoesNotExist:
                logger.warning(f"Parent folder {parent_id} not found for folder {sp_id}")

        # Парсим дату создания
        created_at_sp = parse_datetime(folder_data['created'])
        if not created_at_sp:
            created_at_sp = timezone.now()

        # Права доступа из org
        org = folder_data.get('org', {})
        items = folder_data.get('items', {})

        # Создаем или обновляем папку
        folder, created = SimplePrintFolder.objects.update_or_create(
            simpleprint_id=sp_id,
            defaults={
                'name': name,
                'parent': parent,
                'depth': depth,
                'files_count': items.get('files', 0),
                'folders_count': items.get('folders', 0),
                'can_view': org.get('view', True),
                'can_upload': org.get('upload', True),
                'can_modify': org.get('modify', True),
                'can_download': org.get('download', True),
                'created_at_sp': created_at_sp,
                'last_synced_at': timezone.now(),
            }
        )

        action = "Created" if created else "Updated"
        logger.debug(f"{action} folder: {name} (ID: {sp_id})")

        return folder

    def _sync_files(self, files_data: List[Dict]) -> int:
        """
        Синхронизировать файлы

        Args:
            files_data: Список данных файлов из API

        Returns:
            Количество синхронизированных файлов
        """
        synced_count = 0

        for file_data in files_data:
            try:
                self._sync_file(file_data)
                synced_count += 1

                if synced_count % 50 == 0:
                    logger.info(f"Synced {synced_count}/{len(files_data)} files")

            except Exception as e:
                logger.error(f"Failed to sync file {file_data.get('id')}: {e}")

        return synced_count

    def _sync_file(self, file_data: Dict) -> SimplePrintFile:
        """
        Синхронизировать один файл

        Args:
            file_data: Данные файла из API

        Returns:
            Объект SimplePrintFile
        """
        sp_id = file_data['id']
        name = file_data['name']

        # Парсим дату создания
        created_at_sp = parse_datetime(file_data['created'])
        if not created_at_sp:
            created_at_sp = timezone.now()

        # Получаем папку (файл может быть в корне, без папки)
        folder = None
        # SimplePrint API не всегда возвращает parent_folder_id в данных файла
        # Это нужно будет уточнить при тестировании

        # Создаем или обновляем файл
        file_obj, created = SimplePrintFile.objects.update_or_create(
            simpleprint_id=sp_id,
            defaults={
                'name': name,
                'folder': folder,
                'ext': file_data.get('ext', ''),
                'file_type': file_data.get('type', ''),
                'size': file_data.get('size', 0),
                'zip_printable': file_data.get('zipPrintable', False),
                'zip_no_model': file_data.get('zipNoModel', False),
                'user_id': file_data.get('user_id'),
                'thumbnail': file_data.get('thumbnail', 0),
                'for_printer_models': file_data.get('forPrinterModels', []),
                'for_printers': file_data.get('forPrinters', []),
                'tags': file_data.get('tags', {}),
                'print_data': file_data.get('printData', {}),
                'cost_data': file_data.get('cost', {}),
                'gcode_analysis': file_data.get('gcodeAnalysis', {}),
                'custom_fields': file_data.get('customFields', []),
                'created_at_sp': created_at_sp,
                'last_synced_at': timezone.now(),
            }
        )

        action = "Created" if created else "Updated"
        logger.debug(f"{action} file: {name} (ID: {sp_id})")

        return file_obj

    def _cleanup_deleted_files(self, current_files: List[Dict]) -> int:
        """
        Удалить файлы которых нет в SimplePrint

        Args:
            current_files: Текущий список файлов из API

        Returns:
            Количество удаленных файлов
        """
        current_file_ids = {f['id'] for f in current_files}

        # Находим файлы в БД которых нет в SimplePrint
        deleted_files = SimplePrintFile.objects.exclude(simpleprint_id__in=current_file_ids)
        deleted_count = deleted_files.count()

        if deleted_count > 0:
            logger.info(f"Deleting {deleted_count} files that are no longer in SimplePrint")
            deleted_files.delete()

        return deleted_count

    def get_sync_stats(self) -> Dict:
        """
        Получить статистику синхронизации

        Returns:
            Словарь со статистикой
        """
        last_sync = SimplePrintSync.objects.filter(status='success').first()

        return {
            'total_folders': SimplePrintFolder.objects.count(),
            'total_files': SimplePrintFile.objects.count(),
            'last_sync': last_sync.started_at if last_sync else None,
            'last_sync_status': last_sync.status if last_sync else None,
            'last_sync_duration': last_sync.get_duration() if last_sync else None,
        }
