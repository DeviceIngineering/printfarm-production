"""
Django Admin для SimplePrint моделей
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import (
    SimplePrintFolder, SimplePrintFile, SimplePrintSync, SimplePrintWebhookEvent,
    PrinterSnapshot, PrintJob, PrintQueue, PrinterWebhookEvent
)


@admin.register(SimplePrintFolder)
class SimplePrintFolderAdmin(admin.ModelAdmin):
    """
    Админка для папок SimplePrint
    """
    list_display = ['simpleprint_id', 'name', 'parent', 'depth', 'files_count', 'folders_count', 'last_synced_at']
    list_filter = ['depth', 'last_synced_at', 'can_view', 'can_modify']
    search_fields = ['name', 'simpleprint_id']
    readonly_fields = ['created_at', 'updated_at', 'last_synced_at']
    raw_id_fields = ['parent']

    fieldsets = (
        ('Основная информация', {
            'fields': ('simpleprint_id', 'name', 'parent', 'depth')
        }),
        ('Статистика', {
            'fields': ('files_count', 'folders_count')
        }),
        ('Права доступа', {
            'fields': ('can_view', 'can_upload', 'can_modify', 'can_download'),
            'classes': ('collapse',)
        }),
        ('Метаданные', {
            'fields': ('created_at_sp', 'created_at', 'updated_at', 'last_synced_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SimplePrintFile)
class SimplePrintFileAdmin(admin.ModelAdmin):
    """
    Админка для файлов SimplePrint
    """
    list_display = [
        'name', 'simpleprint_id', 'folder', 'get_size', 'file_type',
        'get_material', 'last_synced_at'
    ]
    list_filter = ['file_type', 'last_synced_at', 'ext']
    search_fields = ['name', 'simpleprint_id']
    readonly_fields = ['created_at', 'updated_at', 'last_synced_at', 'get_size']
    raw_id_fields = ['folder']

    fieldsets = (
        ('Основная информация', {
            'fields': ('simpleprint_id', 'name', 'folder', 'ext', 'file_type', 'size', 'get_size')
        }),
        ('Флаги', {
            'fields': ('zip_printable', 'zip_no_model', 'thumbnail'),
            'classes': ('collapse',)
        }),
        ('Принтер и пользователь', {
            'fields': ('user_id', 'for_printer_models', 'for_printers'),
            'classes': ('collapse',)
        }),
        ('JSON данные', {
            'fields': ('tags', 'print_data', 'cost_data', 'gcode_analysis', 'custom_fields'),
            'classes': ('collapse',)
        }),
        ('Метаданные', {
            'fields': ('created_at_sp', 'created_at', 'updated_at', 'last_synced_at'),
            'classes': ('collapse',)
        }),
    )

    def get_size(self, obj):
        """Отображение размера файла"""
        return obj.get_size_display()
    get_size.short_description = 'Размер'

    def get_material(self, obj):
        """Отображение материала"""
        return obj.get_material_info()
    get_material.short_description = 'Материал'


@admin.register(SimplePrintSync)
class SimplePrintSyncAdmin(admin.ModelAdmin):
    """
    Админка для истории синхронизации
    """
    list_display = [
        'started_at', 'get_status_badge', 'get_duration_display',
        'total_folders', 'synced_folders',
        'total_files', 'synced_files', 'deleted_files'
    ]
    list_filter = ['status', 'started_at']
    readonly_fields = ['started_at', 'get_duration_display']

    fieldsets = (
        ('Статус', {
            'fields': ('status', 'started_at', 'finished_at', 'get_duration_display')
        }),
        ('Статистика папок', {
            'fields': ('total_folders', 'synced_folders')
        }),
        ('Статистика файлов', {
            'fields': ('total_files', 'synced_files', 'deleted_files')
        }),
        ('Ошибки', {
            'fields': ('error_details',),
            'classes': ('collapse',)
        }),
    )

    def get_status_badge(self, obj):
        """Отображение статуса с цветовым индикатором"""
        colors = {
            'pending': '#ffc107',
            'success': '#28a745',
            'failed': '#dc3545',
            'partial': '#17a2b8',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    get_status_badge.short_description = 'Статус'

    def get_duration_display(self, obj):
        """Отображение продолжительности"""
        duration = obj.get_duration()
        if duration:
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            return f"{minutes}м {seconds}с"
        return "В процессе..."
    get_duration_display.short_description = 'Длительность'


@admin.register(SimplePrintWebhookEvent)
class SimplePrintWebhookEventAdmin(admin.ModelAdmin):
    """
    Админка для webhook событий
    """
    list_display = [
        'received_at', 'event_type', 'get_processed_badge',
        'processed_at', 'has_error'
    ]
    list_filter = ['event_type', 'processed', 'received_at']
    readonly_fields = ['received_at', 'processed_at']
    search_fields = ['payload']

    fieldsets = (
        ('Информация о событии', {
            'fields': ('event_type', 'received_at', 'payload')
        }),
        ('Обработка', {
            'fields': ('processed', 'processed_at', 'processing_error')
        }),
    )

    def get_processed_badge(self, obj):
        """Отображение статуса обработки"""
        if obj.processed:
            color = '#28a745'
            text = 'Обработано'
        else:
            color = '#ffc107'
            text = 'Ожидает'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            text
        )
    get_processed_badge.short_description = 'Статус'

    def has_error(self, obj):
        """Наличие ошибки"""
        return bool(obj.processing_error)
    has_error.boolean = True
    has_error.short_description = 'Ошибка'


@admin.register(PrinterSnapshot)
class PrinterSnapshotAdmin(admin.ModelAdmin):
    """Админка для снимков принтеров"""
    list_display = [
        'printer_name', 'get_state_badge', 'get_online_badge',
        'job_file', 'percentage', 'created_at'
    ]
    list_filter = ['state', 'online', 'printer_name', 'created_at']
    search_fields = ['printer_id', 'printer_name', 'job_file']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Принтер', {
            'fields': ('printer_id', 'printer_name', 'state', 'online')
        }),
        ('Задание', {
            'fields': ('job_id', 'job_file', 'percentage', 'current_layer', 'max_layer', 'elapsed_time')
        }),
        ('Температура', {
            'fields': ('temperature_nozzle', 'temperature_bed', 'temperature_ambient'),
            'classes': ('collapse',)
        }),
        ('Временные метки', {
            'fields': ('job_start_time', 'job_end_time_estimate', 'idle_since', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_state_badge(self, obj):
        """Отображение статуса с цветом"""
        colors = {
            'printing': '#007bff',
            'idle': '#28a745',
            'offline': '#6c757d',
            'paused': '#ffc107',
            'error': '#dc3545',
        }
        color = colors.get(obj.state, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_state_display()
        )
    get_state_badge.short_description = 'Статус'

    def get_online_badge(self, obj):
        """Отображение online статуса"""
        if obj.online:
            return format_html('<span style="color: #28a745;">● Online</span>')
        return format_html('<span style="color: #dc3545;">● Offline</span>')
    get_online_badge.short_description = 'Подключение'


@admin.register(PrintJob)
class PrintJobAdmin(admin.ModelAdmin):
    """Админка для истории заданий"""
    list_display = [
        'job_id', 'printer_name', 'article', 'get_status_badge',
        'percentage', 'started_at', 'get_duration', 'success'
    ]
    list_filter = ['status', 'success', 'printer_name', 'started_at']
    search_fields = ['job_id', 'printer_name', 'file_name', 'article']
    readonly_fields = ['created_at', 'updated_at', 'get_duration']

    fieldsets = (
        ('Идентификация', {
            'fields': ('job_id', 'printer_id', 'printer_name')
        }),
        ('Файл', {
            'fields': ('file_id', 'file_name', 'article')
        }),
        ('Статус и прогресс', {
            'fields': ('status', 'percentage', 'current_layer', 'max_layer', 'success')
        }),
        ('Временные метки', {
            'fields': ('queued_at', 'started_at', 'completed_at', 'estimated_time', 'elapsed_time', 'get_duration')
        }),
        ('Ошибки', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
        ('Метаданные', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_status_badge(self, obj):
        """Отображение статуса"""
        colors = {
            'queued': '#6c757d',
            'printing': '#007bff',
            'completed': '#28a745',
            'cancelled': '#ffc107',
            'failed': '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    get_status_badge.short_description = 'Статус'

    def get_duration(self, obj):
        """Отображение длительности"""
        duration = obj.get_duration_seconds()
        if duration:
            hours = duration // 3600
            minutes = (duration % 3600) // 60
            seconds = duration % 60
            if hours > 0:
                return f"{hours}ч {minutes}м {seconds}с"
            return f"{minutes}м {seconds}с"
        return "—"
    get_duration.short_description = 'Длительность'


@admin.register(PrintQueue)
class PrintQueueAdmin(admin.ModelAdmin):
    """Админка для очереди заданий"""
    list_display = [
        'printer_name', 'position', 'article', 'file_name',
        'get_estimated_time', 'added_at'
    ]
    list_filter = ['printer_name', 'added_at']
    search_fields = ['queue_id', 'printer_name', 'file_name', 'article']
    readonly_fields = ['added_at', 'updated_at']

    fieldsets = (
        ('Идентификация', {
            'fields': ('queue_id', 'printer_id', 'printer_name', 'position')
        }),
        ('Файл', {
            'fields': ('file_id', 'file_name', 'article')
        }),
        ('Оценки', {
            'fields': ('estimated_time', 'estimated_start', 'get_estimated_time')
        }),
        ('Метаданные', {
            'fields': ('added_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_estimated_time(self, obj):
        """Отображение оценочного времени"""
        time = obj.estimated_time
        if time:
            hours = time // 3600
            minutes = (time % 3600) // 60
            if hours > 0:
                return f"{hours}ч {minutes}м"
            return f"{minutes}м"
        return "—"
    get_estimated_time.short_description = 'Время печати'


@admin.register(PrinterWebhookEvent)
class PrinterWebhookEventAdmin(admin.ModelAdmin):
    """Админка для webhook событий принтеров"""
    list_display = [
        'received_at', 'get_event_badge', 'printer_id', 'job_id',
        'get_processed_badge', 'has_error'
    ]
    list_filter = ['event_type', 'processed', 'printer_id', 'received_at']
    search_fields = ['printer_id', 'job_id']
    readonly_fields = ['received_at', 'processed_at']

    fieldsets = (
        ('Событие', {
            'fields': ('event_type', 'printer_id', 'job_id', 'received_at')
        }),
        ('Обработка', {
            'fields': ('processed', 'processed_at', 'processing_error')
        }),
        ('Payload', {
            'fields': ('payload',),
            'classes': ('collapse',)
        }),
    )

    def get_event_badge(self, obj):
        """Отображение типа события"""
        colors = {
            'printer_online': '#28a745',
            'printer_offline': '#6c757d',
            'job_started': '#007bff',
            'job_completed': '#28a745',
            'job_cancelled': '#ffc107',
            'job_failed': '#dc3545',
            'job_progress': '#17a2b8',
            'queue_changed': '#6f42c1',
        }
        color = colors.get(obj.event_type, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_event_type_display()
        )
    get_event_badge.short_description = 'Тип события'

    def get_processed_badge(self, obj):
        """Отображение статуса обработки"""
        if obj.processed:
            color = '#28a745'
            text = '✓'
        else:
            color = '#ffc107'
            text = '⏳'
        return format_html(
            '<span style="font-size: 16px;">{}</span>',
            text
        )
    get_processed_badge.short_description = 'Обработано'

    def has_error(self, obj):
        """Наличие ошибки"""
        return bool(obj.processing_error)
    has_error.boolean = True
    has_error.short_description = 'Ошибка'
