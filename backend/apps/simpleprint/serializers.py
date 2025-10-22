"""
SimplePrint Serializers

DRF serializers для SimplePrint моделей.
"""

from rest_framework import serializers
from .models import SimplePrintFolder, SimplePrintFile, SimplePrintSync, SimplePrintWebhookEvent


class SimplePrintFolderSerializer(serializers.ModelSerializer):
    """
    Serializer для SimplePrintFolder
    """
    full_path = serializers.SerializerMethodField()
    subfolders_count = serializers.SerializerMethodField()

    class Meta:
        model = SimplePrintFolder
        fields = [
            'id', 'simpleprint_id', 'name', 'parent', 'depth',
            'files_count', 'folders_count', 'full_path', 'subfolders_count',
            'can_view', 'can_upload', 'can_modify', 'can_download',
            'created_at_sp', 'created_at', 'updated_at', 'last_synced_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'last_synced_at']

    def get_full_path(self, obj):
        """Получить полный путь к папке"""
        return obj.get_full_path()

    def get_subfolders_count(self, obj):
        """Количество подпапок"""
        return obj.subfolders.count()


class SimplePrintFolderListSerializer(serializers.ModelSerializer):
    """
    Упрощенный serializer для списка папок
    """
    class Meta:
        model = SimplePrintFolder
        fields = [
            'id', 'simpleprint_id', 'name', 'depth',
            'files_count', 'folders_count', 'last_synced_at'
        ]


class SimplePrintFileSerializer(serializers.ModelSerializer):
    """
    Serializer для SimplePrintFile
    """
    folder_name = serializers.CharField(source='folder.name', read_only=True)
    size_display = serializers.SerializerMethodField()
    material_info = serializers.SerializerMethodField()
    print_time = serializers.SerializerMethodField()
    filament_usage = serializers.SerializerMethodField()

    class Meta:
        model = SimplePrintFile
        fields = [
            'id', 'simpleprint_id', 'name', 'folder', 'folder_name',
            'ext', 'file_type', 'size', 'size_display',
            'zip_printable', 'zip_no_model',
            'user_id', 'thumbnail',
            'for_printer_models', 'for_printers',
            'tags', 'print_data', 'cost_data', 'gcode_analysis',
            'material_info', 'print_time', 'filament_usage',
            'custom_fields',
            'created_at_sp', 'created_at', 'updated_at', 'last_synced_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'last_synced_at']

    def get_size_display(self, obj):
        """Размер в человекочитаемом формате"""
        return obj.get_size_display()

    def get_material_info(self, obj):
        """Информация о материале"""
        return obj.get_material_info()

    def get_print_time(self, obj):
        """Время печати в секундах"""
        return obj.get_print_time_estimate()

    def get_filament_usage(self, obj):
        """Использование филамента в мм"""
        return obj.get_filament_usage()


class SimplePrintFileListSerializer(serializers.ModelSerializer):
    """
    Упрощенный serializer для списка файлов
    """
    folder_name = serializers.CharField(source='folder.name', read_only=True)
    size_display = serializers.SerializerMethodField()

    class Meta:
        model = SimplePrintFile
        fields = [
            'id', 'simpleprint_id', 'name', 'folder', 'folder_name',
            'ext', 'file_type', 'size', 'size_display',
            'created_at_sp', 'last_synced_at'
        ]

    def get_size_display(self, obj):
        """Размер в человекочитаемом формате"""
        return obj.get_size_display()


class SimplePrintSyncSerializer(serializers.ModelSerializer):
    """
    Serializer для SimplePrintSync
    """
    duration = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = SimplePrintSync
        fields = [
            'id', 'status', 'status_display',
            'started_at', 'finished_at', 'duration',
            'total_folders', 'synced_folders',
            'total_files', 'synced_files', 'deleted_files',
            'error_details'
        ]
        read_only_fields = ['started_at', 'finished_at']

    def get_duration(self, obj):
        """Продолжительность в секундах"""
        return obj.get_duration()


class SimplePrintWebhookEventSerializer(serializers.ModelSerializer):
    """
    Serializer для SimplePrintWebhookEvent
    """
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)

    class Meta:
        model = SimplePrintWebhookEvent
        fields = [
            'id', 'event_type', 'event_type_display',
            'payload', 'processed', 'processed_at',
            'processing_error', 'received_at'
        ]
        read_only_fields = ['received_at', 'processed_at']


class SyncStatsSerializer(serializers.Serializer):
    """
    Serializer для статистики синхронизации
    """
    total_folders = serializers.IntegerField()
    total_files = serializers.IntegerField()
    last_sync = serializers.DateTimeField(allow_null=True)
    last_sync_status = serializers.CharField(allow_null=True)
    last_sync_duration = serializers.FloatField(allow_null=True)


class TriggerSyncSerializer(serializers.Serializer):
    """
    Serializer для запроса синхронизации
    """
    full_sync = serializers.BooleanField(default=False, help_text="Полная синхронизация с удалением отсутствующих файлов")
    force = serializers.BooleanField(default=False, help_text="Принудительная синхронизация")
