"""
Django Admin для SimplePrint моделей
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import SimplePrintFolder, SimplePrintFile, SimplePrintSync, SimplePrintWebhookEvent


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
