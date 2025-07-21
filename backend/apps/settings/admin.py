from django.contrib import admin
from .models import SystemInfo, SyncScheduleSettings, GeneralSettings


@admin.register(SystemInfo)
class SystemInfoAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'version', 'build_date']
    readonly_fields = ['version', 'build_date']
    
    def has_add_permission(self, request):
        # Запрещаем создание новых экземпляров (синглтон)
        return not SystemInfo.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Запрещаем удаление
        return False


@admin.register(SyncScheduleSettings)
class SyncScheduleSettingsAdmin(admin.ModelAdmin):
    list_display = [
        '__str__', 
        'sync_enabled', 
        'sync_interval_display', 
        'last_sync_at', 
        'last_sync_status',
        'sync_success_rate'
    ]
    
    list_filter = ['sync_enabled', 'last_sync_status', 'created_at']
    
    readonly_fields = [
        'last_sync_at', 
        'last_sync_status', 
        'last_sync_message',
        'total_syncs',
        'successful_syncs',
        'sync_success_rate',
        'next_sync_time',
        'created_at',
        'updated_at'
    ]
    
    fieldsets = (
        ('Основные настройки', {
            'fields': ('sync_enabled', 'sync_interval_minutes')
        }),
        ('Настройки склада', {
            'fields': ('warehouse_id', 'warehouse_name'),
            'classes': ('collapse',)
        }),
        ('Исключения', {
            'fields': ('excluded_group_ids', 'excluded_group_names'),
            'classes': ('collapse',)
        }),
        ('Статистика', {
            'fields': (
                'last_sync_at', 
                'last_sync_status', 
                'last_sync_message',
                'next_sync_time',
                'total_syncs',
                'successful_syncs',
                'sync_success_rate'
            ),
            'classes': ('collapse',)
        }),
        ('Система', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def has_add_permission(self, request):
        # Запрещаем создание новых экземпляров (синглтон)
        return not SyncScheduleSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Запрещаем удаление
        return False


@admin.register(GeneralSettings)
class GeneralSettingsAdmin(admin.ModelAdmin):
    list_display = [
        '__str__',
        'default_new_product_stock',
        'default_target_days',
        'low_stock_threshold',
        'products_per_page'
    ]
    
    fieldsets = (
        ('Настройки производства', {
            'fields': (
                'default_new_product_stock',
                'default_target_days', 
                'low_stock_threshold'
            )
        }),
        ('Настройки интерфейса', {
            'fields': (
                'products_per_page',
                'show_images',
                'auto_refresh_interval'
            )
        }),
        ('Система', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def has_add_permission(self, request):
        # Запрещаем создание новых экземпляров (синглтон)
        return not GeneralSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Запрещаем удаление
        return False