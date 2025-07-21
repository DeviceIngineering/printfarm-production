from rest_framework import serializers
from .models import SystemInfo, SyncScheduleSettings, GeneralSettings


class SystemInfoSerializer(serializers.ModelSerializer):
    version = serializers.ReadOnlyField()
    build_date = serializers.ReadOnlyField()
    
    class Meta:
        model = SystemInfo
        fields = ['version', 'build_date']


class SyncScheduleSettingsSerializer(serializers.ModelSerializer):
    sync_interval_display = serializers.ReadOnlyField()
    next_sync_time = serializers.ReadOnlyField()
    sync_success_rate = serializers.ReadOnlyField()
    
    class Meta:
        model = SyncScheduleSettings
        fields = [
            'sync_enabled',
            'sync_interval_minutes',
            'sync_interval_display',
            'warehouse_id',
            'warehouse_name',
            'excluded_group_ids',
            'excluded_group_names',
            'last_sync_at',
            'last_sync_status',
            'last_sync_message',
            'next_sync_time',
            'total_syncs',
            'successful_syncs',
            'sync_success_rate',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'last_sync_at',
            'last_sync_status', 
            'last_sync_message',
            'total_syncs',
            'successful_syncs',
            'created_at',
            'updated_at',
        ]
    
    def validate_sync_interval_minutes(self, value):
        """Проверить что интервал кратен 30 минутам"""
        if value % 30 != 0:
            raise serializers.ValidationError(
                "Интервал синхронизации должен быть кратен 30 минутам"
            )
        if value < 30:
            raise serializers.ValidationError(
                "Минимальный интервал синхронизации - 30 минут"
            )
        if value > 1440:
            raise serializers.ValidationError(
                "Максимальный интервал синхронизации - 24 часа (1440 минут)"
            )
        return value


class GeneralSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneralSettings
        fields = [
            'default_new_product_stock',
            'default_target_days',
            'low_stock_threshold',
            'products_per_page',
            'show_images',
            'auto_refresh_interval',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def validate_default_new_product_stock(self, value):
        if value < 1:
            raise serializers.ValidationError("Значение должно быть больше 0")
        if value > 100:
            raise serializers.ValidationError("Значение не должно превышать 100")
        return value
    
    def validate_default_target_days(self, value):
        if value < 1:
            raise serializers.ValidationError("Значение должно быть больше 0")
        if value > 90:
            raise serializers.ValidationError("Значение не должно превышать 90 дней")
        return value


class SettingsSummarySerializer(serializers.Serializer):
    """Сводная информация о всех настройках"""
    system_info = SystemInfoSerializer()
    sync_settings = SyncScheduleSettingsSerializer()
    general_settings = GeneralSettingsSerializer()
    
    # Дополнительная информация
    total_products = serializers.IntegerField()
    last_sync_info = serializers.DictField()
    system_status = serializers.DictField()