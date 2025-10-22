"""
SimplePrint Integration Models

Модели для хранения информации о файлах и папках из SimplePrint API.
"""

from django.db import models
from django.utils import timezone


class SimplePrintFolder(models.Model):
    """
    Модель для хранения информации о папках из SimplePrint
    """
    # Основные поля
    simpleprint_id = models.IntegerField(unique=True, db_index=True, help_text="ID папки в SimplePrint")
    name = models.CharField(max_length=500, help_text="Название папки")

    # Иерархия
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subfolders',
        help_text="Родительская папка"
    )
    depth = models.IntegerField(default=0, help_text="Уровень вложенности")

    # Статистика
    files_count = models.IntegerField(default=0, help_text="Количество файлов в папке")
    folders_count = models.IntegerField(default=0, help_text="Количество подпапок")

    # Права доступа (из org)
    can_view = models.BooleanField(default=True)
    can_upload = models.BooleanField(default=True)
    can_modify = models.BooleanField(default=True)
    can_download = models.BooleanField(default=True)

    # Метаданные
    created_at_sp = models.DateTimeField(help_text="Дата создания в SimplePrint")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Дата создания в локальной БД")
    updated_at = models.DateTimeField(auto_now=True, help_text="Дата обновления в локальной БД")
    last_synced_at = models.DateTimeField(default=timezone.now, help_text="Дата последней синхронизации")

    class Meta:
        ordering = ['depth', 'name']
        indexes = [
            models.Index(fields=['parent', 'name']),
            models.Index(fields=['simpleprint_id']),
            models.Index(fields=['last_synced_at']),
        ]
        verbose_name = "SimplePrint Папка"
        verbose_name_plural = "SimplePrint Папки"

    def __str__(self):
        return f"{self.name} (ID: {self.simpleprint_id})"

    def get_full_path(self):
        """Получить полный путь к папке"""
        if self.parent:
            return f"{self.parent.get_full_path()}/{self.name}"
        return self.name


class SimplePrintFile(models.Model):
    """
    Модель для хранения информации о G-code файлах из SimplePrint
    """
    # Основные поля
    simpleprint_id = models.CharField(max_length=255, unique=True, db_index=True, help_text="ID/хэш файла в SimplePrint")
    name = models.CharField(max_length=500, help_text="Имя файла")

    # Связь с папкой
    folder = models.ForeignKey(
        SimplePrintFolder,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='files',
        help_text="Папка в которой находится файл"
    )

    # Информация о файле
    ext = models.CharField(max_length=20, blank=True, help_text="Расширение файла")
    file_type = models.CharField(max_length=50, blank=True, help_text="Тип файла (printable, etc)")
    size = models.BigIntegerField(default=0, help_text="Размер файла в байтах")

    # Флаги
    zip_printable = models.BooleanField(default=False)
    zip_no_model = models.BooleanField(default=False)

    # Пользователь и принтер
    user_id = models.IntegerField(null=True, blank=True, help_text="ID пользователя в SimplePrint")
    thumbnail = models.IntegerField(default=0, help_text="Наличие миниатюры")
    for_printer_models = models.JSONField(default=list, blank=True, help_text="Модели принтеров")
    for_printers = models.JSONField(default=list, blank=True, help_text="Конкретные принтеры")

    # Теги и материалы (JSON)
    tags = models.JSONField(default=dict, blank=True, help_text="Теги файла (nozzleData, material)")

    # Статистика печати (JSON)
    print_data = models.JSONField(default=dict, blank=True, help_text="Статистика печати (printsDone, printsCancelled, etc)")

    # Стоимость (JSON)
    cost_data = models.JSONField(default=dict, blank=True, help_text="Информация о стоимости")

    # Анализ G-code (JSON)
    gcode_analysis = models.JSONField(default=dict, blank=True, help_text="Детальный анализ G-code")

    # Пользовательские поля
    custom_fields = models.JSONField(default=list, blank=True, help_text="Пользовательские поля")

    # Метаданные
    created_at_sp = models.DateTimeField(help_text="Дата создания в SimplePrint")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Дата создания в локальной БД")
    updated_at = models.DateTimeField(auto_now=True, help_text="Дата обновления в локальной БД")
    last_synced_at = models.DateTimeField(default=timezone.now, help_text="Дата последней синхронизации")

    class Meta:
        ordering = ['-created_at_sp']
        indexes = [
            models.Index(fields=['folder', 'name']),
            models.Index(fields=['simpleprint_id']),
            models.Index(fields=['file_type']),
            models.Index(fields=['last_synced_at']),
            models.Index(fields=['-created_at_sp']),
        ]
        verbose_name = "SimplePrint Файл"
        verbose_name_plural = "SimplePrint Файлы"

    def __str__(self):
        return f"{self.name} ({self.get_size_display()})"

    def get_size_display(self):
        """Получить размер файла в человекочитаемом формате"""
        size = self.size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def get_material_info(self):
        """Получить информацию о материале из тегов"""
        if 'material' in self.tags and len(self.tags['material']) > 0:
            material = self.tags['material'][0]
            return f"{material.get('type', 'Unknown')} - {material.get('color', 'Unknown')}"
        return "Unknown"

    def get_print_time_estimate(self):
        """Получить оценку времени печати в секундах"""
        if 'gcodeAnalysis' in self.__dict__ and 'estimate' in self.gcode_analysis:
            return self.gcode_analysis['estimate']
        return None

    def get_filament_usage(self):
        """Получить использование филамента в мм"""
        if 'gcodeAnalysis' in self.__dict__ and 'filament' in self.gcode_analysis:
            filament = self.gcode_analysis.get('filament', [])
            if filament and len(filament) > 0:
                return filament[0]
        return None


class SimplePrintSync(models.Model):
    """
    Модель для отслеживания истории синхронизации с SimplePrint
    """
    STATUS_CHOICES = [
        ('pending', 'В процессе'),
        ('success', 'Успешно'),
        ('failed', 'Ошибка'),
        ('partial', 'Частично выполнено'),
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Время выполнения
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    # Статистика папок
    total_folders = models.IntegerField(default=0)
    synced_folders = models.IntegerField(default=0)

    # Статистика файлов
    total_files = models.IntegerField(default=0)
    synced_files = models.IntegerField(default=0)
    deleted_files = models.IntegerField(default=0)

    # Детали ошибок
    error_details = models.TextField(blank=True)

    class Meta:
        ordering = ['-started_at']
        verbose_name = "SimplePrint Синхронизация"
        verbose_name_plural = "SimplePrint Синхронизации"

    def __str__(self):
        return f"Sync {self.started_at.strftime('%Y-%m-%d %H:%M')} - {self.get_status_display()}"

    def get_duration(self):
        """Получить продолжительность синхронизации"""
        if self.finished_at:
            delta = self.finished_at - self.started_at
            return delta.total_seconds()
        return None
