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
        # - part\d (part1, part2)
        # - \d+[,.]?\d*(pcs|k) (25pcs, 3k, 1.5k, 1,5k)
        # - \d+h (временные метки типа 12h)

        # Находим первое вхождение этих паттернов
        patterns = [
            r'_part\d+',              # _part1, _part2
            r'_\d+[,.]?\d*(pcs|psc|k)', # _25pcs, _42psc (опечатка), _3k, _1.5k
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

        Поддерживаемые паттерны:
        - 25pcs, 42psc (опечатка) = 25 единиц
        - 3k, 3K = 3 единицы
        - 1,5k, 1.5k = 1.5 единицы (дробное значение)
        - part1, part2, part3... = 0.5 (половина изделия, когда печатается по частям)
        """
        import re
        filename = obj.name.lower()

        # 1. Проверяем дробные значения типа "1,5k" или "1.5k" или "1.5pcs"
        match = re.search(r'(\d+)[,.](\d+)(pcs|psc|k)(?=[_\s\d]|$)', filename)
        if match:
            integer_part = int(match.group(1))
            decimal_part = int(match.group(2))
            # Создаем дробное число: 1,5 -> 1.5
            return float(f"{integer_part}.{decimal_part}")

        # 2. Проверяем целые значения типа "25pcs", "42psc" или "3k"
        match = re.search(r'(\d+)(pcs|psc|k)(?=[_\s\d]|$)', filename)
        if match:
            return float(match.group(1))

        # 3. Проверяем паттерн "part" (part1, part2, part3 и т.д.)
        # Если изделие печатается по частям, каждая часть = 0.5
        match = re.search(r'part\d+', filename)
        if match:
            return 0.5

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
