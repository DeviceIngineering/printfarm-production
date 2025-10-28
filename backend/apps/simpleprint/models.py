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


class SimplePrintWebhookEvent(models.Model):
    """
    Модель для логирования webhook событий от SimplePrint
    """
    EVENT_TYPE_CHOICES = [
        ('file_created', 'Файл создан'),
        ('file_updated', 'Файл обновлен'),
        ('file_deleted', 'Файл удален'),
        ('folder_created', 'Папка создана'),
        ('folder_deleted', 'Папка удалена'),
        ('unknown', 'Неизвестное событие'),
    ]

    event_type = models.CharField(max_length=50, choices=EVENT_TYPE_CHOICES)
    payload = models.JSONField(help_text="Полные данные webhook")

    # Обработка события
    processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    processing_error = models.TextField(blank=True)

    # Метаданные
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-received_at']
        indexes = [
            models.Index(fields=['event_type', '-received_at']),
            models.Index(fields=['processed', '-received_at']),
        ]
        verbose_name = "SimplePrint Webhook Event"
        verbose_name_plural = "SimplePrint Webhook Events"

    def __str__(self):
        return f"{self.get_event_type_display()} - {self.received_at.strftime('%Y-%m-%d %H:%M')}"


class PrinterSnapshot(models.Model):
    """
    Снимок состояния принтера из SimplePrint API
    Сохраняется каждый раз при синхронизации для отслеживания изменений
    """
    # Идентификация принтера
    printer_id = models.CharField(max_length=50, db_index=True, help_text="SimplePrint ID принтера")
    printer_name = models.CharField(max_length=100, help_text="Имя принтера (P1S-2, P1S-3, etc.)")

    # Состояние принтера
    STATE_CHOICES = [
        ('printing', 'Печатает'),
        ('idle', 'Ожидание'),
        ('offline', 'Оффлайн'),
        ('paused', 'Пауза'),
        ('error', 'Ошибка'),
    ]
    state = models.CharField(max_length=20, choices=STATE_CHOICES, help_text="Состояние принтера")
    online = models.BooleanField(default=True, help_text="Принтер онлайн")

    # Текущее задание
    job_id = models.CharField(max_length=50, null=True, blank=True, help_text="ID задания")
    job_file = models.CharField(max_length=500, null=True, blank=True, help_text="Имя файла задания")

    # Прогресс задания
    percentage = models.IntegerField(default=0, help_text="Процент выполнения (0-100)")
    current_layer = models.IntegerField(null=True, blank=True, default=0, help_text="Текущий слой")
    max_layer = models.IntegerField(null=True, blank=True, default=0, help_text="Максимальный слой")
    elapsed_time = models.IntegerField(default=0, help_text="Прошло времени (секунды)")

    # Температура
    temperature_nozzle = models.IntegerField(null=True, blank=True, help_text="Температура сопла (°C)")
    temperature_bed = models.IntegerField(null=True, blank=True, help_text="Температура стола (°C)")
    temperature_ambient = models.IntegerField(null=True, blank=True, help_text="Температура окружающей среды (°C)")

    # Расчетные поля
    job_start_time = models.DateTimeField(null=True, blank=True, help_text="Расчетное время начала задания")
    job_end_time_estimate = models.DateTimeField(null=True, blank=True, help_text="Расчетное время окончания")
    idle_since = models.DateTimeField(null=True, blank=True, help_text="В состоянии ожидания с")

    # Метаданные
    created_at = models.DateTimeField(auto_now_add=True, help_text="Время создания снимка")
    updated_at = models.DateTimeField(auto_now=True, help_text="Время обновления снимка")

    # Дополнительные данные (для будущего использования)
    raw_data = models.JSONField(default=dict, blank=True, help_text="Полные данные от API")

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['printer_id', '-created_at']),
            models.Index(fields=['state', '-created_at']),
            models.Index(fields=['printer_name']),
        ]
        verbose_name = "SimplePrint Printer Snapshot"
        verbose_name_plural = "SimplePrint Printer Snapshots"

    def __str__(self):
        return f"{self.printer_name} - {self.get_state_display()} ({self.created_at.strftime('%H:%M:%S')})"

    def get_idle_duration_seconds(self):
        """Получить длительность простоя в секундах"""
        if self.idle_since:
            return int((timezone.now() - self.idle_since).total_seconds())
        return 0

    def get_time_remaining_seconds(self):
        """Получить оставшееся время до окончания задания в секундах"""
        if self.job_end_time_estimate and self.state == 'printing':
            remaining = (self.job_end_time_estimate - timezone.now()).total_seconds()
            return max(0, int(remaining))
        return 0


class PrintJob(models.Model):
    """
    История печатных заданий
    Сохраняет полную информацию о каждом задании для аналитики и отслеживания
    """
    # Идентификация
    job_id = models.CharField(max_length=50, unique=True, db_index=True, help_text="ID задания в SimplePrint")
    printer_id = models.CharField(max_length=50, db_index=True, help_text="ID принтера")
    printer_name = models.CharField(max_length=100, help_text="Имя принтера")

    # Файл задания
    file_id = models.CharField(max_length=255, null=True, blank=True, help_text="ID файла в SimplePrint")
    file_name = models.CharField(max_length=500, help_text="Имя файла")
    article = models.CharField(max_length=100, null=True, blank=True, db_index=True, help_text="Артикул (парсинг из имени)")

    # Состояние
    STATUS_CHOICES = [
        ('queued', 'В очереди'),
        ('printing', 'Печатается'),
        ('completed', 'Завершено'),
        ('cancelled', 'Отменено'),
        ('failed', 'Ошибка'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, db_index=True, help_text="Статус задания")

    # Прогресс
    percentage = models.IntegerField(default=0, help_text="Процент выполнения (0-100)")
    current_layer = models.IntegerField(default=0, help_text="Текущий слой")
    max_layer = models.IntegerField(default=0, help_text="Максимальный слой")

    # Время
    queued_at = models.DateTimeField(null=True, blank=True, help_text="Время добавления в очередь")
    started_at = models.DateTimeField(null=True, blank=True, db_index=True, help_text="Время начала печати")
    completed_at = models.DateTimeField(null=True, blank=True, help_text="Время завершения")
    estimated_time = models.IntegerField(default=0, help_text="Оценочное время (секунды)")
    elapsed_time = models.IntegerField(default=0, help_text="Затраченное время (секунды)")

    # Результат
    success = models.BooleanField(default=False, help_text="Задание успешно завершено")
    error_message = models.TextField(blank=True, help_text="Сообщение об ошибке")

    # Метаданные
    raw_data = models.JSONField(default=dict, blank=True, help_text="Полные данные от API")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Время создания записи")
    updated_at = models.DateTimeField(auto_now=True, help_text="Время обновления записи")

    class Meta:
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['printer_id', '-started_at']),
            models.Index(fields=['status', '-started_at']),
            models.Index(fields=['article', '-started_at']),
            models.Index(fields=['-completed_at']),
        ]
        verbose_name = "Print Job"
        verbose_name_plural = "Print Jobs"

    def __str__(self):
        return f"{self.job_id} - {self.printer_name} - {self.get_status_display()}"

    def get_duration_seconds(self):
        """Получить длительность выполнения задания в секундах"""
        if self.completed_at and self.started_at:
            return int((self.completed_at - self.started_at).total_seconds())
        return self.elapsed_time


class PrintQueue(models.Model):
    """
    Очередь заданий принтера
    Отслеживает задания, ожидающие печати
    """
    # Идентификация
    queue_id = models.CharField(max_length=50, unique=True, db_index=True, help_text="ID очереди в SimplePrint")
    printer_id = models.CharField(max_length=50, db_index=True, help_text="ID принтера")
    printer_name = models.CharField(max_length=100, help_text="Имя принтера")

    # Задание
    file_id = models.CharField(max_length=255, help_text="ID файла в SimplePrint")
    file_name = models.CharField(max_length=500, help_text="Имя файла")
    article = models.CharField(max_length=100, null=True, blank=True, db_index=True, help_text="Артикул")

    # Позиция в очереди
    position = models.IntegerField(default=0, db_index=True, help_text="Позиция в очереди (0 = первое)")

    # Оценки
    estimated_time = models.IntegerField(default=0, help_text="Оценочное время печати (секунды)")
    estimated_start = models.DateTimeField(null=True, blank=True, help_text="Расчетное время начала")

    # Метаданные
    added_at = models.DateTimeField(auto_now_add=True, help_text="Время добавления в очередь")
    updated_at = models.DateTimeField(auto_now=True, help_text="Время обновления")
    raw_data = models.JSONField(default=dict, blank=True, help_text="Полные данные от API")

    class Meta:
        ordering = ['printer_id', 'position']
        indexes = [
            models.Index(fields=['printer_id', 'position']),
            models.Index(fields=['article']),
        ]
        verbose_name = "Print Queue Item"
        verbose_name_plural = "Print Queue Items"

    def __str__(self):
        return f"{self.printer_name} - Позиция {self.position} - {self.file_name}"


class PrinterWebhookEvent(models.Model):
    """
    События webhook для принтеров (отдельно от файловых событий)
    Логирует все события от SimplePrint webhooks для отладки и мониторинга
    """
    EVENT_TYPE_CHOICES = [
        ('test', 'Тестовое событие'),
        ('printer_online', 'Принтер онлайн'),
        ('printer_offline', 'Принтер оффлайн'),
        ('printer_state_changed', 'Изменение состояния принтера'),
        ('job_started', 'Задание начато'),
        ('job_completed', 'Задание завершено'),
        ('job_cancelled', 'Задание отменено'),
        ('job_failed', 'Задание провалено'),
        ('job_paused', 'Задание приостановлено'),
        ('job_resumed', 'Задание возобновлено'),
        ('job_progress', 'Прогресс задания'),
        ('queue_changed', 'Очередь изменена'),
        ('file_created', 'Файл создан'),
        ('file_deleted', 'Файл удален'),
        ('error_occurred', 'Произошла ошибка'),
        ('unknown', 'Неизвестное событие'),
    ]

    event_type = models.CharField(max_length=50, choices=EVENT_TYPE_CHOICES, db_index=True, help_text="Тип события")
    printer_id = models.CharField(max_length=50, null=True, blank=True, db_index=True, help_text="ID принтера")
    job_id = models.CharField(max_length=50, null=True, blank=True, help_text="ID задания")
    payload = models.JSONField(help_text="Полные данные webhook payload")

    # Обработка
    processed = models.BooleanField(default=False, db_index=True, help_text="Событие обработано")
    processed_at = models.DateTimeField(null=True, blank=True, help_text="Время обработки")
    processing_error = models.TextField(blank=True, help_text="Ошибка при обработке")

    # Метаданные
    received_at = models.DateTimeField(auto_now_add=True, db_index=True, help_text="Время получения webhook")

    class Meta:
        ordering = ['-received_at']
        indexes = [
            models.Index(fields=['printer_id', '-received_at']),
            models.Index(fields=['event_type', '-received_at']),
            models.Index(fields=['processed', '-received_at']),
        ]
        verbose_name = "Printer Webhook Event"
        verbose_name_plural = "Printer Webhook Events"

    def __str__(self):
        return f"{self.get_event_type_display()} - {self.received_at.strftime('%Y-%m-%d %H:%M:%S')}"
