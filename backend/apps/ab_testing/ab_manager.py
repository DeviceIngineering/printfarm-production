"""
A/B Testing Manager для PrintFarm
Позволяет переключаться между различными алгоритмами производства и UI вариантами
"""

import hashlib
import json
import random
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from enum import Enum

from django.conf import settings
from django.core.cache import cache
from django.db import models
from django.contrib.auth.models import User


class TestVariant(Enum):
    """Варианты тестирования"""
    CONTROL = "control"  # Текущий алгоритм (v7.0)
    VARIANT_A = "variant_a"  # Новый алгоритм производства
    VARIANT_B = "variant_b"  # Экспериментальный алгоритм
    

class FeatureFlag(Enum):
    """Флаги функций для A/B тестирования"""
    PRODUCTION_ALGORITHM = "production_algorithm"
    UI_LAYOUT = "ui_layout"
    EXPORT_FORMAT = "export_format"
    SYNC_STRATEGY = "sync_strategy"
    CACHING_STRATEGY = "caching_strategy"


class ABTestManager:
    """Менеджер для управления A/B тестами"""
    
    def __init__(self):
        self.enabled = getattr(settings, 'AB_TESTING_ENABLED', False)
        self.cache_timeout = 3600  # 1 час
        
    def get_user_variant(self, user_id: str, feature: FeatureFlag) -> TestVariant:
        """
        Определяет вариант теста для пользователя
        Использует детерминированный подход на основе user_id
        """
        if not self.enabled:
            return TestVariant.CONTROL
            
        # Проверяем кэш
        cache_key = f"ab_test:{feature.value}:{user_id}"
        cached_variant = cache.get(cache_key)
        if cached_variant:
            return TestVariant(cached_variant)
            
        # Детерминированное распределение на основе хэша
        hash_input = f"{user_id}:{feature.value}:{settings.SECRET_KEY}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        
        # Распределение по вариантам
        distribution = self.get_distribution(feature)
        random_value = (hash_value % 100) / 100.0
        
        variant = self._select_variant(random_value, distribution)
        
        # Сохраняем в кэш
        cache.set(cache_key, variant.value, self.cache_timeout)
        
        # Логируем выбор
        self.log_variant_assignment(user_id, feature, variant)
        
        return variant
    
    def get_distribution(self, feature: FeatureFlag) -> Dict[TestVariant, float]:
        """
        Возвращает распределение вариантов для функции
        """
        distributions = {
            FeatureFlag.PRODUCTION_ALGORITHM: {
                TestVariant.CONTROL: 0.34,     # 34% - текущий алгоритм
                TestVariant.VARIANT_A: 0.33,   # 33% - новый алгоритм
                TestVariant.VARIANT_B: 0.33,   # 33% - экспериментальный
            },
            FeatureFlag.UI_LAYOUT: {
                TestVariant.CONTROL: 0.5,      # 50% - текущий UI
                TestVariant.VARIANT_A: 0.5,     # 50% - новый UI
                TestVariant.VARIANT_B: 0.0,
            },
            FeatureFlag.EXPORT_FORMAT: {
                TestVariant.CONTROL: 0.7,      # 70% - текущий формат
                TestVariant.VARIANT_A: 0.3,     # 30% - новый формат
                TestVariant.VARIANT_B: 0.0,
            },
            FeatureFlag.SYNC_STRATEGY: {
                TestVariant.CONTROL: 0.8,      # 80% - текущая стратегия
                TestVariant.VARIANT_A: 0.2,     # 20% - оптимизированная
                TestVariant.VARIANT_B: 0.0,
            },
            FeatureFlag.CACHING_STRATEGY: {
                TestVariant.CONTROL: 0.6,      # 60% - текущее кэширование
                TestVariant.VARIANT_A: 0.4,     # 40% - агрессивное кэширование
                TestVariant.VARIANT_B: 0.0,
            }
        }
        
        return distributions.get(feature, {
            TestVariant.CONTROL: 1.0,
            TestVariant.VARIANT_A: 0.0,
            TestVariant.VARIANT_B: 0.0,
        })
    
    def _select_variant(self, random_value: float, distribution: Dict[TestVariant, float]) -> TestVariant:
        """
        Выбирает вариант на основе случайного значения и распределения
        """
        cumulative = 0.0
        for variant, probability in distribution.items():
            cumulative += probability
            if random_value <= cumulative:
                return variant
        return TestVariant.CONTROL
    
    def log_variant_assignment(self, user_id: str, feature: FeatureFlag, variant: TestVariant):
        """
        Логирует назначение варианта пользователю
        """
        from apps.ab_testing.models import ABTestAssignment
        
        ABTestAssignment.objects.update_or_create(
            user_id=user_id,
            feature=feature.value,
            defaults={
                'variant': variant.value,
                'assigned_at': datetime.now()
            }
        )
    
    def track_event(self, user_id: str, feature: FeatureFlag, event_type: str, 
                    event_data: Optional[Dict[str, Any]] = None):
        """
        Отслеживает события для анализа эффективности вариантов
        """
        from apps.ab_testing.models import ABTestEvent
        
        variant = self.get_user_variant(user_id, feature)
        
        ABTestEvent.objects.create(
            user_id=user_id,
            feature=feature.value,
            variant=variant.value,
            event_type=event_type,
            event_data=event_data or {},
            created_at=datetime.now()
        )
    
    def get_metrics(self, feature: FeatureFlag, 
                   start_date: Optional[datetime] = None,
                   end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Возвращает метрики для A/B теста
        """
        from apps.ab_testing.models import ABTestEvent
        
        if not start_date:
            start_date = datetime.now() - timedelta(days=7)
        if not end_date:
            end_date = datetime.now()
            
        events = ABTestEvent.objects.filter(
            feature=feature.value,
            created_at__range=(start_date, end_date)
        )
        
        metrics = {}
        for variant in TestVariant:
            variant_events = events.filter(variant=variant.value)
            
            metrics[variant.value] = {
                'total_users': variant_events.values('user_id').distinct().count(),
                'total_events': variant_events.count(),
                'conversion_rate': self._calculate_conversion_rate(variant_events),
                'avg_time_to_action': self._calculate_avg_time_to_action(variant_events),
                'performance_metrics': self._calculate_performance_metrics(variant_events),
            }
        
        # Статистическая значимость
        metrics['statistical_significance'] = self._calculate_significance(metrics)
        
        return metrics
    
    def _calculate_conversion_rate(self, events) -> float:
        """Рассчитывает конверсию для варианта"""
        total_users = events.values('user_id').distinct().count()
        converted_users = events.filter(
            event_type='conversion'
        ).values('user_id').distinct().count()
        
        if total_users == 0:
            return 0.0
        
        return (converted_users / total_users) * 100
    
    def _calculate_avg_time_to_action(self, events) -> float:
        """Рассчитывает среднее время до целевого действия"""
        # Упрощенная реализация
        action_events = events.filter(event_type='action_completed')
        if not action_events.exists():
            return 0.0
            
        total_time = 0
        count = 0
        
        for event in action_events:
            if 'duration_ms' in event.event_data:
                total_time += event.event_data['duration_ms']
                count += 1
        
        if count == 0:
            return 0.0
            
        return total_time / count
    
    def _calculate_performance_metrics(self, events) -> Dict[str, float]:
        """Рассчитывает метрики производительности"""
        perf_events = events.filter(event_type='performance')
        
        metrics = {
            'avg_load_time': 0.0,
            'avg_api_response': 0.0,
            'error_rate': 0.0,
        }
        
        if not perf_events.exists():
            return metrics
            
        load_times = []
        api_times = []
        error_count = 0
        
        for event in perf_events:
            data = event.event_data
            if 'load_time' in data:
                load_times.append(data['load_time'])
            if 'api_response_time' in data:
                api_times.append(data['api_response_time'])
            if 'error' in data and data['error']:
                error_count += 1
        
        if load_times:
            metrics['avg_load_time'] = sum(load_times) / len(load_times)
        if api_times:
            metrics['avg_api_response'] = sum(api_times) / len(api_times)
        if perf_events.count() > 0:
            metrics['error_rate'] = (error_count / perf_events.count()) * 100
            
        return metrics
    
    def _calculate_significance(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Рассчитывает статистическую значимость результатов
        Упрощенная реализация z-теста для пропорций
        """
        import math
        
        control_data = metrics.get(TestVariant.CONTROL.value, {})
        variant_a_data = metrics.get(TestVariant.VARIANT_A.value, {})
        
        n1 = control_data.get('total_users', 0)
        n2 = variant_a_data.get('total_users', 0)
        
        if n1 < 30 or n2 < 30:
            return {
                'is_significant': False,
                'confidence_level': 0,
                'message': 'Недостаточно данных для статистической значимости'
            }
        
        p1 = control_data.get('conversion_rate', 0) / 100
        p2 = variant_a_data.get('conversion_rate', 0) / 100
        
        # Объединенная пропорция
        p = ((p1 * n1) + (p2 * n2)) / (n1 + n2)
        
        # Стандартная ошибка
        se = math.sqrt(p * (1 - p) * ((1/n1) + (1/n2)))
        
        if se == 0:
            return {
                'is_significant': False,
                'confidence_level': 0,
                'message': 'Невозможно рассчитать значимость'
            }
        
        # Z-статистика
        z = (p2 - p1) / se
        
        # Определяем уровень значимости
        confidence_level = 0
        is_significant = False
        
        if abs(z) > 2.58:
            confidence_level = 99
            is_significant = True
        elif abs(z) > 1.96:
            confidence_level = 95
            is_significant = True
        elif abs(z) > 1.645:
            confidence_level = 90
            is_significant = True
        
        winner = None
        if is_significant:
            if p2 > p1:
                winner = TestVariant.VARIANT_A.value
            else:
                winner = TestVariant.CONTROL.value
        
        return {
            'is_significant': is_significant,
            'confidence_level': confidence_level,
            'z_score': round(z, 3),
            'winner': winner,
            'message': f"Результаты {'статистически значимы' if is_significant else 'не значимы'} с уверенностью {confidence_level}%"
        }
    
    def override_variant(self, user_id: str, feature: FeatureFlag, variant: TestVariant):
        """
        Принудительно устанавливает вариант для пользователя (для тестирования)
        """
        cache_key = f"ab_test:{feature.value}:{user_id}"
        cache.set(cache_key, variant.value, self.cache_timeout * 24)  # 24 часа
        
        # Логируем переопределение
        self.log_variant_assignment(user_id, feature, variant)
    
    def clear_user_variants(self, user_id: str):
        """
        Очищает все варианты для пользователя
        """
        for feature in FeatureFlag:
            cache_key = f"ab_test:{feature.value}:{user_id}"
            cache.delete(cache_key)


# Глобальный экземпляр менеджера
ab_manager = ABTestManager()