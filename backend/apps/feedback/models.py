"""
Модели для системы обратной связи фокус-группы
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
import json


class FeedbackCategory(models.TextChoices):
    """Категории обратной связи"""
    BUG = 'bug', 'Баг/Ошибка'
    PERFORMANCE = 'performance', 'Производительность'
    UI_UX = 'ui_ux', 'Интерфейс/UX'
    FEATURE_REQUEST = 'feature_request', 'Предложение функции'
    WORKFLOW = 'workflow', 'Рабочий процесс'
    DATA_ACCURACY = 'data_accuracy', 'Точность данных'
    INTEGRATION = 'integration', 'Интеграция МойСклад'
    EXPORT = 'export', 'Экспорт данных'
    OTHER = 'other', 'Другое'


class BugSeverity(models.TextChoices):
    """Уровни критичности багов"""
    CRITICAL = 'critical', 'Критический (система не работает)'
    HIGH = 'high', 'Высокий (важная функция не работает)'
    MEDIUM = 'medium', 'Средний (неудобство в работе)'
    LOW = 'low', 'Низкий (косметическая проблема)'


class FeedbackStatus(models.TextChoices):
    """Статусы обработки feedback"""
    NEW = 'new', 'Новый'
    IN_REVIEW = 'in_review', 'На рассмотрении'
    IN_PROGRESS = 'in_progress', 'В работе'
    RESOLVED = 'resolved', 'Решен'
    CLOSED = 'closed', 'Закрыт'
    DUPLICATE = 'duplicate', 'Дубликат'
    WONT_FIX = 'wont_fix', 'Не будет исправлен'


class FeedbackSubmission(models.Model):
    """Основная модель для отчетов обратной связи"""
    
    # Базовая информация
    title = models.CharField(max_length=200, verbose_name="Заголовок")
    description = models.TextField(verbose_name="Описание")
    category = models.CharField(
        max_length=20,
        choices=FeedbackCategory.choices,
        default=FeedbackCategory.OTHER,
        verbose_name="Категория"
    )
    
    # Информация о пользователе
    user_id = models.CharField(max_length=100, verbose_name="ID пользователя")
    user_email = models.EmailField(blank=True, verbose_name="Email пользователя")
    user_name = models.CharField(max_length=100, blank=True, verbose_name="Имя пользователя")
    
    # Техническая информация
    browser = models.CharField(max_length=100, blank=True, verbose_name="Браузер")
    os = models.CharField(max_length=100, blank=True, verbose_name="Операционная система")
    screen_resolution = models.CharField(max_length=20, blank=True, verbose_name="Разрешение экрана")
    user_agent = models.TextField(blank=True, verbose_name="User Agent")
    
    # Контекст ошибки
    page_url = models.URLField(blank=True, verbose_name="URL страницы")
    steps_to_reproduce = models.TextField(blank=True, verbose_name="Шаги для воспроизведения")
    expected_behavior = models.TextField(blank=True, verbose_name="Ожидаемое поведение")
    actual_behavior = models.TextField(blank=True, verbose_name="Фактическое поведение")
    
    # Приоритизация
    severity = models.CharField(
        max_length=10,
        choices=BugSeverity.choices,
        blank=True,
        verbose_name="Критичность"
    )
    frequency = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Частота возникновения"
    )
    
    # Файлы и скриншоты
    screenshot = models.ImageField(
        upload_to='feedback/screenshots/',
        blank=True,
        null=True,
        verbose_name="Скриншот"
    )
    attachment = models.FileField(
        upload_to='feedback/attachments/',
        blank=True,
        null=True,
        verbose_name="Прикрепленный файл"
    )
    
    # Статус и обработка
    status = models.CharField(
        max_length=15,
        choices=FeedbackStatus.choices,
        default=FeedbackStatus.NEW,
        verbose_name="Статус"
    )
    assigned_to = models.CharField(max_length=100, blank=True, verbose_name="Назначен")
    priority = models.IntegerField(
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Приоритет (1-высший, 5-низший)"
    )
    
    # Временные метки
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    resolved_at = models.DateTimeField(blank=True, null=True, verbose_name="Дата решения")
    
    # Дополнительные данные
    metadata = models.JSONField(default=dict, blank=True, verbose_name="Метаданные")
    
    class Meta:
        db_table = 'feedback_submission'
        verbose_name = 'Отчет обратной связи'
        verbose_name_plural = 'Отчеты обратной связи'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'category']),
            models.Index(fields=['created_at']),
            models.Index(fields=['priority', 'severity']),
        ]
    
    def __str__(self):
        return f"[{self.category}] {self.title}"
    
    @property
    def is_critical(self):
        """Проверяет, является ли feedback критическим"""
        return self.severity == BugSeverity.CRITICAL or self.priority == 1
    
    @property
    def response_time_hours(self):
        """Возвращает время ответа в часах"""
        if self.resolved_at:
            delta = self.resolved_at - self.created_at
            return delta.total_seconds() / 3600
        return None


class FeedbackComment(models.Model):
    """Комментарии к отчетам обратной связи"""
    
    feedback = models.ForeignKey(
        FeedbackSubmission,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name="Отчет"
    )
    author = models.CharField(max_length=100, verbose_name="Автор")
    comment = models.TextField(verbose_name="Комментарий")
    is_internal = models.BooleanField(default=False, verbose_name="Внутренний комментарий")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    
    class Meta:
        db_table = 'feedback_comment'
        verbose_name = 'Комментарий к отчету'
        verbose_name_plural = 'Комментарии к отчетам'
        ordering = ['created_at']
    
    def __str__(self):
        return f"Комментарий от {self.author}"


class UserSatisfactionSurvey(models.Model):
    """Опросы удовлетворенности пользователей"""
    
    user_id = models.CharField(max_length=100, verbose_name="ID пользователя")
    
    # Оценки различных аспектов (1-5)
    overall_satisfaction = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Общая удовлетворенность"
    )
    ease_of_use = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Простота использования"
    )
    performance_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Оценка производительности"
    )
    feature_completeness = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Полнота функций"
    )
    design_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Оценка дизайна"
    )
    
    # Текстовые ответы
    most_liked_feature = models.TextField(blank=True, verbose_name="Больше всего понравилось")
    most_disliked_feature = models.TextField(blank=True, verbose_name="Больше всего не понравилось")
    improvement_suggestions = models.TextField(blank=True, verbose_name="Предложения по улучшению")
    missing_features = models.TextField(blank=True, verbose_name="Недостающие функции")
    
    # Рекомендации
    would_recommend = models.BooleanField(verbose_name="Порекомендовали бы коллегам")
    recommendation_score = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        verbose_name="NPS оценка (0-10)"
    )
    
    # Контекст использования
    usage_frequency = models.CharField(
        max_length=20,
        choices=[
            ('daily', 'Ежедневно'),
            ('weekly', 'Еженедельно'),
            ('monthly', 'Ежемесячно'),
            ('rarely', 'Редко'),
        ],
        verbose_name="Частота использования"
    )
    primary_use_case = models.TextField(blank=True, verbose_name="Основной сценарий использования")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    
    class Meta:
        db_table = 'user_satisfaction_survey'
        verbose_name = 'Опрос удовлетворенности'
        verbose_name_plural = 'Опросы удовлетворенности'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Опрос {self.user_id} - {self.overall_satisfaction}/5"
    
    @property
    def nps_category(self):
        """Возвращает категорию NPS"""
        if self.recommendation_score >= 9:
            return 'Промоутер'
        elif self.recommendation_score >= 7:
            return 'Нейтральный'
        else:
            return 'Критик'


class FeatureUsageTracking(models.Model):
    """Отслеживание использования функций"""
    
    user_id = models.CharField(max_length=100, verbose_name="ID пользователя")
    feature_name = models.CharField(max_length=100, verbose_name="Название функции")
    action = models.CharField(max_length=50, verbose_name="Действие")
    
    # Временные метрики
    session_id = models.CharField(max_length=100, verbose_name="ID сессии")
    duration_ms = models.IntegerField(blank=True, null=True, verbose_name="Длительность (мс)")
    
    # Результат действия
    success = models.BooleanField(default=True, verbose_name="Успешно")
    error_message = models.TextField(blank=True, verbose_name="Сообщение об ошибке")
    
    # Контекст
    page_url = models.URLField(blank=True, verbose_name="URL страницы")
    browser = models.CharField(max_length=100, blank=True, verbose_name="Браузер")
    
    # A/B тест информация
    ab_test_variant = models.CharField(max_length=20, blank=True, verbose_name="Вариант A/B теста")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Время события")
    
    class Meta:
        db_table = 'feature_usage_tracking'
        verbose_name = 'Отслеживание использования функций'
        verbose_name_plural = 'Отслеживание использования функций'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user_id', 'feature_name']),
            models.Index(fields=['created_at']),
            models.Index(fields=['ab_test_variant']),
        ]
    
    def __str__(self):
        return f"{self.user_id} - {self.feature_name} - {self.action}"


class FeedbackTemplate(models.Model):
    """Шаблоны для быстрого создания отчетов"""
    
    name = models.CharField(max_length=100, verbose_name="Название шаблона")
    category = models.CharField(
        max_length=20,
        choices=FeedbackCategory.choices,
        verbose_name="Категория"
    )
    title_template = models.CharField(max_length=200, verbose_name="Шаблон заголовка")
    description_template = models.TextField(verbose_name="Шаблон описания")
    
    # Поля которые нужно заполнить
    required_fields = models.JSONField(default=list, verbose_name="Обязательные поля")
    optional_fields = models.JSONField(default=list, verbose_name="Опциональные поля")
    
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    
    class Meta:
        db_table = 'feedback_template'
        verbose_name = 'Шаблон отчета'
        verbose_name_plural = 'Шаблоны отчетов'
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.category} - {self.name}"