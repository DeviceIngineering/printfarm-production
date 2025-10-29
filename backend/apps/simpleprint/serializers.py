"""
SimplePrint Serializers

DRF serializers для SimplePrint моделей.
"""

from rest_framework import serializers
from .models import (
    SimplePrintFolder, SimplePrintFile, SimplePrintSync, SimplePrintWebhookEvent,
    PrinterSnapshot, PrintJob, PrintQueue, PrinterWebhookEvent
)


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
    material_color = serializers.SerializerMethodField()
    print_time = serializers.SerializerMethodField()
    weight = serializers.SerializerMethodField()
    quantity = serializers.SerializerMethodField()
    article = serializers.SerializerMethodField()

    class Meta:
        model = SimplePrintFile
        fields = [
            'id', 'simpleprint_id', 'name', 'folder', 'folder_name',
            'ext', 'file_type', 'size', 'size_display',
            'tags', 'gcode_analysis', 'print_data',
            'material_color', 'print_time', 'weight', 'quantity', 'article',
            'created_at_sp', 'last_synced_at'
        ]

    def get_size_display(self, obj):
        """Размер в человекочитаемом формате"""
        return obj.get_size_display()

    def get_material_color(self, obj):
        """Получить цвет материала из тегов"""
        if 'material' in obj.tags and len(obj.tags['material']) > 0:
            return obj.tags['material'][0].get('color', None)
        return None

    def get_article(self, obj):
        """
        Извлечь артикул из имени файла

        Артикул находится в начале имени файла, перед указателями:
        - part1, part2... (части изделия)
        - 25pcs, 3k (количество)
        - временными метками (12h51m)

        Форматы артикулов:
        - 673-50930 (3 цифры - 5 цифр)
        - N406-05-54.7 (с буквами, точками, тире, подчеркиваниями)
        - 138_N406-12-138 (сложные комбинации)
        - 710 (простые числа)
        """
        import re
        filename = obj.name

        # Убираем расширение
        name_without_ext = filename.rsplit('.', 1)[0] if '.' in filename else filename

        # Паттерны для поиска границы артикула:
        # ПРИОРИТЕТ: pcs/psc имеет приоритет над k
        # - part\d (part1, part2)
        # - \d+pcs, \d+psc (явное указание количества)
        # - \d+k (количество ТОЛЬКО если идет отдельно после underscore)
        # - \d+h\d*m (временные метки типа 12h51m)

        # Находим первое вхождение этих паттернов
        patterns = [
            r'_part\d+',              # _part1, _part2
            r'_\d+[,.]?\d*(pcs|psc)', # _25pcs, _42psc (опечатка), _1.5pcs (ПРИОРИТЕТ)
            r'_\d+k(?=[_\s\d]|$)',   # _3k (количество, только если отдельно)
            r'_\d+h\d*m',             # _12h51m, _2h (время печати с часами и минутами)
            r'_\d+m_',                # _30m_ (только минуты, за которыми идет что-то еще)
            r'_\d+g_',                # _370g_ (вес, за которым идет что-то еще)
        ]

        earliest_pos = len(name_without_ext)
        for pattern in patterns:
            match = re.search(pattern, name_without_ext, re.IGNORECASE)
            if match:
                earliest_pos = min(earliest_pos, match.start())

        # Извлекаем артикул - все до первого найденного паттерна
        article_part = name_without_ext[:earliest_pos]

        # Очищаем артикул от trailing underscore
        article = article_part.rstrip('_')

        # Удаляем префикс с номером папки (например, "138_" в начале)
        # Паттерн: 1-3 цифры + подчеркивание в начале строки
        article = re.sub(r'^(\d{1,3})_', '', article)

        # Удаляем распространенные суффиксы (NEW, OLD, V1, V2, V3, UPDATED, FINAL и т.д.)
        # Паттерн: underscore + любые буквы/цифры в конце артикула
        article = re.sub(r'_(NEW|OLD|V\d+|UPDATED|FINAL|TEST|DRAFT)$', '', article, flags=re.IGNORECASE)

        # Если артикул не пустой и содержит хотя бы одну цифру или букву
        if article and re.search(r'[A-Za-z0-9]', article):
            return article

        return None

    def get_quantity(self, obj):
        """
        Извлечь количество деталей из имени файла

        ПРИОРИТЕТ (от высокого к низкому):
        1. pcs/psc (явное указание штук) - ВСЕГДА имеет приоритет
        2. part (части изделия) = 0.5
        3. k/K (только если идет ОТДЕЛЬНО после underscore, не в артикуле)

        Примеры:
        - 45_N421-11-45K_part2_10pcs_... → 10.0 (pcs приоритетнее, 45K - часть артикула)
        - 102-43032_42psc_... → 42.0 (psc)
        - N406-12-138_3K_... → 3.0 (отдельное k после underscore)
        - 673-50930_part1_... → 0.5 (part)
        """
        import re
        filename = obj.name.lower()

        # ПРИОРИТЕТ 1: Проверяем наличие pcs/psc (явное указание количества)

        # 1a. Дробные значения с pcs/psc: "1,5pcs" или "1.5pcs"
        match = re.search(r'(\d+)[,.](\d+)(pcs|psc)(?=[_\s\d]|$)', filename)
        if match:
            integer_part = int(match.group(1))
            decimal_part = int(match.group(2))
            return float(f"{integer_part}.{decimal_part}")

        # 1b. Целые значения с pcs/psc: "25pcs", "42psc"
        match = re.search(r'(\d+)(pcs|psc)(?=[_\s\d]|$)', filename)
        if match:
            return float(match.group(1))

        # ПРИОРИТЕТ 2: Проверяем паттерн "part" (part1, part2, part3 и т.д.)
        # Если изделие печатается по частям, каждая часть = 0.5
        match = re.search(r'part\d+', filename)
        if match:
            return 0.5

        # ПРИОРИТЕТ 3: Проверяем k ТОЛЬКО если нет pcs/psc
        # ВАЖНО: k должен идти ПОСЛЕ underscore (не в начале имени, не в артикуле)
        # Паттерн: _\d+k с lookahead для конца или разделителя
        match = re.search(r'_(\d+)k(?=[_\s\d]|$)', filename)
        if match:
            return float(match.group(1))

        # Дробные значения с k (только если после underscore)
        match = re.search(r'_(\d+)[,.](\d+)k(?=[_\s\d]|$)', filename)
        if match:
            integer_part = int(match.group(1))
            decimal_part = int(match.group(2))
            return float(f"{integer_part}.{decimal_part}")

        return None

    def get_print_time(self, obj):
        """Получить время печати в секундах из gcode_analysis"""
        if obj.gcode_analysis and 'estimate' in obj.gcode_analysis:
            return obj.gcode_analysis['estimate']
        return None

    def get_weight(self, obj):
        """
        Получить вес филамента в граммах из gcode_analysis
        Вычисляется как: (filament_length_mm * π * (diameter/2)^2 * density) / 1000
        """
        if not obj.gcode_analysis:
            return None

        # Получаем длину филамента в мм
        filament_length = None
        if 'filament' in obj.gcode_analysis:
            filament_data = obj.gcode_analysis['filament']
            if isinstance(filament_data, list) and len(filament_data) > 0:
                filament_length = filament_data[0]  # первый элемент - длина в мм
            elif isinstance(filament_data, (int, float)):
                filament_length = filament_data

        if not filament_length:
            return None

        # Получаем плотность и диаметр из materialData
        density = 1.24  # плотность по умолчанию для PLA
        diameter = 1.75  # диаметр по умолчанию

        if 'materialData' in obj.gcode_analysis:
            material_data = obj.gcode_analysis['materialData']
            if isinstance(material_data, list) and len(material_data) > 0:
                material = material_data[0]
                density = material.get('density', density)
                diameter = material.get('diameter', diameter)

        # Вычисляем вес: Volume = length * π * (radius)^2, Weight = Volume * density
        import math
        radius = diameter / 2
        volume_cm3 = (filament_length / 10) * math.pi * (radius / 10) ** 2  # переводим в см³
        weight_g = volume_cm3 * density

        return round(weight_g, 1)


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


class PrinterSnapshotSerializer(serializers.ModelSerializer):
    """
    Serializer для PrinterSnapshot
    """
    state_display = serializers.CharField(source='get_state_display', read_only=True)
    idle_duration_seconds = serializers.SerializerMethodField()
    time_remaining_seconds = serializers.SerializerMethodField()

    class Meta:
        model = PrinterSnapshot
        fields = [
            'id', 'printer_id', 'printer_name',
            'state', 'state_display', 'online',
            'job_id', 'job_file',
            'percentage', 'current_layer', 'max_layer', 'elapsed_time',
            'temperature_nozzle', 'temperature_bed', 'temperature_ambient',
            'job_start_time', 'job_end_time_estimate', 'idle_since',
            'idle_duration_seconds', 'time_remaining_seconds',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_idle_duration_seconds(self, obj):
        """Продолжительность простоя в секундах"""
        return obj.get_idle_duration_seconds()

    def get_time_remaining_seconds(self, obj):
        """Оставшееся время до окончания в секундах"""
        return obj.get_time_remaining_seconds()


class PrinterSyncResultSerializer(serializers.Serializer):
    """
    Serializer для результата синхронизации принтеров
    """
    synced = serializers.IntegerField()
    failed = serializers.IntegerField()
    printers = serializers.ListField(
        child=serializers.DictField()
    )


class PrinterStatsSerializer(serializers.Serializer):
    """
    Serializer для статистики принтеров
    """
    total = serializers.IntegerField()
    printing = serializers.IntegerField()
    idle = serializers.IntegerField()
    offline = serializers.IntegerField()
    error = serializers.IntegerField()
    online = serializers.IntegerField()


# ==================== Новые serializers для Webhook Testing ====================


class PrintJobSerializer(serializers.ModelSerializer):
    """Serializer для PrintJob"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    duration = serializers.SerializerMethodField()

    class Meta:
        model = PrintJob
        fields = [
            'id', 'job_id', 'printer_id', 'printer_name',
            'file_id', 'file_name', 'article',
            'status', 'status_display', 'percentage',
            'current_layer', 'max_layer',
            'queued_at', 'started_at', 'completed_at',
            'estimated_time', 'elapsed_time', 'duration',
            'success', 'error_message',
            'created_at', 'updated_at'
        ]

    def get_duration(self, obj):
        """Получить длительность в секундах"""
        return obj.get_duration_seconds()


class PrintQueueSerializer(serializers.ModelSerializer):
    """Serializer для PrintQueue"""
    estimated_time_display = serializers.SerializerMethodField()

    class Meta:
        model = PrintQueue
        fields = [
            'id', 'queue_id', 'printer_id', 'printer_name',
            'file_id', 'file_name', 'article',
            'position', 'estimated_time', 'estimated_time_display',
            'estimated_start', 'added_at', 'updated_at'
        ]

    def get_estimated_time_display(self, obj):
        """Форматированное время"""
        time = obj.estimated_time
        if time:
            hours = time // 3600
            minutes = (time % 3600) // 60
            if hours > 0:
                return f"{hours}ч {minutes}м"
            return f"{minutes}м"
        return None


class PrinterWebhookEventSerializer(serializers.ModelSerializer):
    """Serializer для PrinterWebhookEvent"""
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)

    class Meta:
        model = PrinterWebhookEvent
        fields = [
            'id', 'event_type', 'event_type_display',
            'printer_id', 'job_id', 'payload',
            'processed', 'processed_at', 'processing_error',
            'received_at'
        ]
        read_only_fields = ['received_at', 'processed_at']


class WebhookTestRequestSerializer(serializers.Serializer):
    """Serializer для тестового webhook запроса"""
    event_type = serializers.ChoiceField(choices=[
        ('printer_online', 'Принтер онлайн'),
        ('printer_offline', 'Принтер оффлайн'),
        ('job_started', 'Задание начато'),
        ('job_completed', 'Задание завершено'),
        ('job_cancelled', 'Задание отменено'),
        ('job_failed', 'Задание провалено'),
        ('job_progress', 'Прогресс задания'),
        ('queue_changed', 'Очередь изменена'),
    ])
    printer_id = serializers.CharField(required=False, allow_blank=True)
    job_id = serializers.CharField(required=False, allow_blank=True)
    test_data = serializers.JSONField(required=False)


class WebhookInfoSerializer(serializers.Serializer):
    """Serializer для информации о webhook"""
    id = serializers.CharField()
    url = serializers.CharField()
    enabled = serializers.BooleanField()
    events = serializers.ListField(child=serializers.CharField())
    description = serializers.CharField(required=False, allow_blank=True)


class WebhookTestingDataSerializer(serializers.Serializer):
    """Serializer для данных webhook testing"""
    webhooks = WebhookInfoSerializer(many=True)
    recent_events = PrinterWebhookEventSerializer(many=True)
    event_stats = serializers.DictField()
    websocket_available = serializers.BooleanField()


class TimelineJobSerializer(serializers.ModelSerializer):
    """
    Упрощенный serializer для заданий в timeline.
    Содержит только необходимую информацию для отображения на временной шкале.
    """
    duration_seconds = serializers.SerializerMethodField()
    material_color = serializers.SerializerMethodField()

    class Meta:
        model = PrintJob
        fields = [
            'job_id', 'article', 'file_name',
            'status', 'percentage',
            'started_at', 'completed_at',
            'duration_seconds', 'material_color'
        ]

    def get_duration_seconds(self, obj):
        """Получить длительность задания в секундах"""
        return obj.get_duration_seconds()

    def get_material_color(self, obj):
        """
        Получить цвет материала из raw_data задания.
        Возвращает: 'black', 'white', 'other'
        """
        # Пытаемся получить цвет из raw_data
        if obj.raw_data and isinstance(obj.raw_data, dict):
            # SimplePrint может отправлять цвет материала в разных местах
            material_data = obj.raw_data.get('material', {})
            if isinstance(material_data, dict):
                color = material_data.get('color', '').lower()
                if 'black' in color or 'черн' in color:
                    return 'black'
                elif 'white' in color or 'бел' in color:
                    return 'white'
                elif color:
                    return 'other'

        return 'other'


class TimelinePrinterSerializer(serializers.Serializer):
    """
    Serializer для принтера с заданиями в timeline.
    """
    id = serializers.CharField()
    name = serializers.CharField()
    jobs = TimelineJobSerializer(many=True)
