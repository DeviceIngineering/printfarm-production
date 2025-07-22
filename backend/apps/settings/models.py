from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.core.models import TimestampedModel
import subprocess
import os


class SystemInfo(models.Model):
    """Информация о системе - синглтон модель"""
    
    class Meta:
        verbose_name = 'Информация о системе'
        verbose_name_plural = 'Информация о системе'
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if not self.pk and SystemInfo.objects.exists():
            raise ValueError('Может существовать только один экземпляр SystemInfo')
        return super().save(*args, **kwargs)
    
    @classmethod
    def get_instance(cls):
        """Получить единственный экземпляр"""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj
    
    @property
    def version(self):
        """Получить текущую версию из VERSION файла или git"""
        try:
            # Сначала пытаемся прочитать из файла VERSION
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            version_file = os.path.join(project_root, 'VERSION')
            
            if os.path.exists(version_file):
                with open(version_file, 'r', encoding='utf-8') as f:
                    version = f.read().strip()
                    if version:
                        return f"v{version}"
            
            # Если нет файла VERSION, пытаемся получить из git tag
            result = subprocess.run(
                ['git', 'describe', '--tags', '--exact-match', 'HEAD'],
                capture_output=True,
                text=True,
                cwd=project_root
            )
            if result.returncode == 0:
                return result.stdout.strip()
            
            # Если нет тега, получаем короткий хеш коммита
            result = subprocess.run(
                ['git', 'rev-parse', '--short', 'HEAD'],
                capture_output=True,
                text=True,
                cwd=project_root
            )
            if result.returncode == 0:
                return f"commit-{result.stdout.strip()}"
                
        except Exception:
            pass
        
        return "unknown"
    
    @property
    def build_date(self):
        """Получить дату последнего коммита"""
        try:
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            result = subprocess.run(
                ['git', 'log', '-1', '--format=%cd', '--date=iso'],
                capture_output=True,
                text=True,
                cwd=project_root
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        
        return "unknown"
    
    def __str__(self):
        return f"System Info (v{self.version})"


class SyncScheduleSettings(TimestampedModel):
    """Настройки расписания синхронизации"""
    
    INTERVAL_CHOICES = [
        (30, '30 минут'),
        (60, '1 час'),
        (90, '1,5 часа'),
        (120, '2 часа'),
        (150, '2,5 часа'),
        (180, '3 часа'),
        (210, '3,5 часа'),
        (240, '4 часа'),
        (270, '4,5 часа'),
        (300, '5 часов'),
        (360, '6 часов'),
        (420, '7 часов'),
        (480, '8 часов'),
        (540, '9 часов'),
        (600, '10 часов'),
        (660, '11 часов'),
        (720, '12 часов'),
        (1440, '24 часа'),
    ]
    
    # Основные настройки
    sync_enabled = models.BooleanField(
        default=True,
        verbose_name='Включить автоматическую синхронизацию'
    )
    
    sync_interval_minutes = models.IntegerField(
        choices=INTERVAL_CHOICES,
        default=60,
        validators=[MinValueValidator(30), MaxValueValidator(1440)],
        verbose_name='Интервал синхронизации (минуты)'
    )
    
    # Настройки склада
    warehouse_id = models.CharField(
        max_length=36,
        blank=True,
        verbose_name='ID склада для синхронизации'
    )
    
    warehouse_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Название склада'
    )
    
    # Исключаемые группы товаров
    excluded_group_ids = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Исключаемые группы товаров (ID)'
    )
    
    excluded_group_names = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Исключаемые группы товаров (названия)'
    )
    
    # Время последней синхронизации
    last_sync_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Время последней синхронизации'
    )
    
    last_sync_status = models.CharField(
        max_length=20,
        choices=[
            ('success', 'Успешно'),
            ('failed', 'Ошибка'),
            ('partial', 'Частично'),
            ('in_progress', 'В процессе'),
        ],
        blank=True,
        verbose_name='Статус последней синхронизации'
    )
    
    last_sync_message = models.TextField(
        blank=True,
        verbose_name='Сообщение о последней синхронизации'
    )
    
    # Время создания расписания
    schedule_created_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Время создания/обновления расписания'
    )
    
    # Статистика
    total_syncs = models.IntegerField(
        default=0,
        verbose_name='Всего синхронизаций'
    )
    
    successful_syncs = models.IntegerField(
        default=0,
        verbose_name='Успешных синхронизаций'
    )
    
    class Meta:
        verbose_name = 'Настройки синхронизации'
        verbose_name_plural = 'Настройки синхронизации'
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if not self.pk and SyncScheduleSettings.objects.exists():
            raise ValueError('Может существовать только один экземпляр SyncScheduleSettings')
        return super().save(*args, **kwargs)
    
    @classmethod
    def get_instance(cls):
        """Получить единственный экземпляр"""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj
    
    @property
    def sync_interval_display(self):
        """Получить отображение интервала"""
        return dict(self.INTERVAL_CHOICES).get(self.sync_interval_minutes, f"{self.sync_interval_minutes} мин")
    
    @property
    def next_sync_time(self):
        """Рассчитать время следующей синхронизации"""
        if not self.sync_enabled or not self.schedule_created_at:
            return None
        
        from django.utils import timezone
        from datetime import timedelta
        from django_celery_beat.models import PeriodicTask
        
        # Пытаемся получить реальное время последнего запуска из Celery Beat
        try:
            task = PeriodicTask.objects.get(name='sync-moysklad-scheduled')
            if task.enabled and task.last_run_at:
                # Если есть запуск Celery Beat, рассчитываем от него
                return task.last_run_at + timedelta(minutes=self.sync_interval_minutes)
        except PeriodicTask.DoesNotExist:
            pass
        
        # Если есть последняя синхронизация после создания расписания, рассчитываем от неё
        if self.last_sync_at and self.last_sync_at >= self.schedule_created_at:
            return self.last_sync_at + timedelta(minutes=self.sync_interval_minutes)
        
        # Иначе рассчитываем от времени создания расписания
        return self.schedule_created_at + timedelta(minutes=self.sync_interval_minutes)
    
    @property
    def sync_success_rate(self):
        """Процент успешных синхронизаций"""
        if self.total_syncs == 0:
            return 0
        return round((self.successful_syncs / self.total_syncs) * 100, 1)
    
    def update_sync_stats(self, success: bool, message: str = ''):
        """Обновить статистику синхронизации"""
        from django.utils import timezone
        
        self.total_syncs += 1
        if success:
            self.successful_syncs += 1
            self.last_sync_status = 'success'
        else:
            self.last_sync_status = 'failed'
        
        self.last_sync_at = timezone.now()
        self.last_sync_message = message
        self.save()
    
    def __str__(self):
        status = "включена" if self.sync_enabled else "отключена"
        return f"Синхронизация ({status}, каждые {self.sync_interval_display})"


class GeneralSettings(TimestampedModel):
    """Общие настройки системы"""
    
    # Настройки производства
    default_new_product_stock = models.IntegerField(
        default=10,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        verbose_name='Целевой остаток для новых товаров'
    )
    
    default_target_days = models.IntegerField(
        default=15,
        validators=[MinValueValidator(1), MaxValueValidator(90)],
        verbose_name='Целевой запас в днях для старых товаров'
    )
    
    low_stock_threshold = models.IntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(50)],
        verbose_name='Порог низкого остатка'
    )
    
    # Настройки интерфейса
    products_per_page = models.IntegerField(
        default=100,
        choices=[(25, '25'), (50, '50'), (100, '100'), (200, '200')],
        verbose_name='Товаров на странице'
    )
    
    show_images = models.BooleanField(
        default=True,
        verbose_name='Показывать изображения товаров'
    )
    
    auto_refresh_interval = models.IntegerField(
        default=0,
        choices=[
            (0, 'Отключено'),
            (30, '30 секунд'),
            (60, '1 минута'),
            (300, '5 минут'),
            (600, '10 минут'),
        ],
        verbose_name='Автообновление страницы (секунды)'
    )
    
    class Meta:
        verbose_name = 'Общие настройки'
        verbose_name_plural = 'Общие настройки'
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if not self.pk and GeneralSettings.objects.exists():
            raise ValueError('Может существовать только один экземпляр GeneralSettings')
        return super().save(*args, **kwargs)
    
    @classmethod
    def get_instance(cls):
        """Получить единственный экземпляр"""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj
    
    def __str__(self):
        return f"Общие настройки (обновлено: {self.updated_at.strftime('%d.%m.%Y %H:%M')})"