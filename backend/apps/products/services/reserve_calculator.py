"""
Сервис для расчета значений в колонке "Резерв" на вкладке Точка
в таблице "Список к производству"

Алгоритм:
- Если Резерв > 0: отображать (Резерв - Остаток)
- Цветовая индикация:
  - Синий: если Резерв > Остаток (положительный результат)
  - Красный: если Резерв <= Остаток (отрицательный/нулевой результат)

Бизнес-цель: Сделать значения в колонке Резерв более значимыми 
и удобными для чтения пользователем
"""

import logging
from decimal import Decimal
from typing import Dict, Any, Optional
from django.utils import timezone

logger = logging.getLogger(__name__)


class ReserveCalculatorService:
    """
    Сервис для расчета и форматирования значений резерва
    с цветовой индикацией для пользовательского интерфейса
    """
    
    def __init__(self):
        """Инициализация сервиса расчета резерва"""
        logger.info("Инициализация ReserveCalculatorService")
        
    def calculate_reserve_display(
        self, 
        reserved_stock: Decimal, 
        current_stock: Decimal
    ) -> Dict[str, Any]:
        """
        Расчет отображаемого значения резерва и цветовой индикации
        
        Args:
            reserved_stock (Decimal): Количество товара в резерве
            current_stock (Decimal): Текущий остаток товара
            
        Returns:
            Dict[str, Any]: Словарь с результатами расчета:
                - calculated_reserve: Рассчитанное значение (Резерв - Остаток)
                - color_indicator: Цвет для отображения ('blue', 'red', 'gray')
                - is_positive: True если результат положительный
                - should_show_calculation: True если нужно показывать расчет
                - original_reserve: Исходное значение резерва
                - current_stock: Исходный остаток
        """
        start_time = timezone.now()
        
        logger.debug(
            f"Расчет резерва: резерв={reserved_stock}, остаток={current_stock}"
        )
        
        try:
            # Конвертируем в Decimal для точных вычислений
            reserve = Decimal(str(reserved_stock)) if reserved_stock else Decimal('0')
            stock = Decimal(str(current_stock)) if current_stock else Decimal('0')
            
            # Основной алгоритм: Резерв - Остаток
            calculated_reserve = reserve - stock
            
            # Определение цветовой индикации
            if reserve == Decimal('0'):
                # Если резерва нет - серый цвет, не показываем расчет
                color_indicator = 'gray'
                should_show_calculation = False
                is_positive = False
            elif reserve > stock:
                # Резерв больше остатка - синий цвет (хорошо)
                color_indicator = 'blue' 
                should_show_calculation = True
                is_positive = True
            else:
                # Резерв меньше или равен остатку - красный цвет (внимание)
                color_indicator = 'red'
                should_show_calculation = True  
                is_positive = False
                
            result = {
                'calculated_reserve': calculated_reserve,
                'color_indicator': color_indicator,
                'is_positive': is_positive,
                'should_show_calculation': should_show_calculation,
                'original_reserve': reserve,
                'current_stock': stock,
                'calculation_timestamp': start_time
            }
            
            # Логирование результата
            logger.debug(
                f"Результат расчета резерва: {calculated_reserve}, "
                f"цвет: {color_indicator}, положительный: {is_positive}"
            )
            
            return result
            
        except Exception as e:
            logger.error(
                f"Ошибка при расчете резерва: {e}, "
                f"резерв={reserved_stock}, остаток={current_stock}"
            )
            
            # Возвращаем безопасные значения по умолчанию
            return {
                'calculated_reserve': Decimal('0'),
                'color_indicator': 'gray',
                'is_positive': False,
                'should_show_calculation': False,
                'original_reserve': Decimal('0'),
                'current_stock': Decimal('0'),
                'calculation_timestamp': start_time,
                'error': str(e)
            }
    
    def format_reserve_for_display(
        self, 
        calculation_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Форматирование результата расчета для отображения в UI
        
        Args:
            calculation_result: Результат расчета от calculate_reserve_display()
            
        Returns:
            Dict[str, Any]: Форматированные данные для UI:
                - display_text: Текст для отображения
                - css_color: CSS цвет для стилизации
                - tooltip_text: Текст для всплывающей подсказки
        """
        try:
            calculated_reserve = calculation_result['calculated_reserve']
            color_indicator = calculation_result['color_indicator']
            original_reserve = calculation_result['original_reserve']
            current_stock = calculation_result['current_stock']
            
            # Определение CSS цветов
            css_colors = {
                'blue': '#1890ff',    # Синий - хорошо
                'red': '#ff4d4f',     # Красный - внимание
                'gray': '#8c8c8c'     # Серый - нет данных
            }
            
            # Форматирование текста для отображения
            if not calculation_result['should_show_calculation']:
                display_text = f"{original_reserve} шт"
                tooltip_text = "Резерв отсутствует"
            else:
                # Показываем расчет: "Резерв: 15 → 5 шт"
                sign = "+" if calculated_reserve >= 0 else ""
                display_text = f"{original_reserve} → {sign}{calculated_reserve} шт"
                
                if calculated_reserve > 0:
                    tooltip_text = f"Резерв превышает остаток на {calculated_reserve} шт"
                elif calculated_reserve == 0:
                    tooltip_text = "Резерв равен остатку"
                else:
                    tooltip_text = f"Резерв меньше остатка на {abs(calculated_reserve)} шт"
            
            return {
                'display_text': display_text,
                'css_color': css_colors.get(color_indicator, css_colors['gray']),
                'tooltip_text': tooltip_text,
                'color_indicator': color_indicator,
                'calculated_value': calculated_reserve,
                'needs_attention': color_indicator == 'red'
            }
            
        except Exception as e:
            logger.error(f"Ошибка форматирования резерва для UI: {e}")
            
            return {
                'display_text': "0 шт",
                'css_color': css_colors['gray'],
                'tooltip_text': "Ошибка расчета",
                'color_indicator': 'gray',
                'calculated_value': Decimal('0'),
                'needs_attention': False,
                'error': str(e)
            }
    
    def bulk_calculate_reserves(
        self, 
        products_data: list
    ) -> list:
        """
        Массовый расчет резервов для списка товаров
        
        Args:
            products_data: Список словарей с данными товаров
                [{'reserved_stock': Decimal, 'current_stock': Decimal, ...}, ...]
                
        Returns:
            list: Список товаров с добавленными полями расчета резерва
        """
        logger.info(f"Начало массового расчета резервов для {len(products_data)} товаров")
        
        start_time = timezone.now()
        results = []
        
        for i, product_data in enumerate(products_data):
            try:
                # Расчет резерва
                reserve_calc = self.calculate_reserve_display(
                    reserved_stock=product_data.get('reserved_stock', Decimal('0')),
                    current_stock=product_data.get('current_stock', Decimal('0'))
                )
                
                # Форматирование для UI
                ui_format = self.format_reserve_for_display(reserve_calc)
                
                # Добавляем расчетные поля к исходным данным товара
                enhanced_product = {
                    **product_data,
                    'reserve_calculation': reserve_calc,
                    'reserve_ui_format': ui_format,
                    'calculated_reserve': reserve_calc['calculated_reserve'],
                    'reserve_color': reserve_calc['color_indicator']
                }
                
                results.append(enhanced_product)
                
            except Exception as e:
                logger.error(f"Ошибка расчета резерва для товара {i}: {e}")
                
                # Добавляем товар с безопасными значениями
                enhanced_product = {
                    **product_data,
                    'reserve_calculation': None,
                    'reserve_ui_format': None,
                    'calculated_reserve': Decimal('0'),
                    'reserve_color': 'gray',
                    'calculation_error': str(e)
                }
                
                results.append(enhanced_product)
        
        end_time = timezone.now()
        execution_time = (end_time - start_time).total_seconds()
        
        logger.info(
            f"Завершен массовый расчет резервов: {len(results)} товаров, "
            f"время выполнения: {execution_time:.3f} сек"
        )
        
        # Проверка требования производительности (< 5 сек)
        if execution_time > 5.0:
            logger.warning(
                f"Время расчета резервов ({execution_time:.2f} сек) "
                f"превышает требование 5 сек для {len(products_data)} товаров"
            )
        
        return results


# Функция-утилита для быстрого доступа
def calculate_product_reserve(reserved_stock: Decimal, current_stock: Decimal) -> Dict[str, Any]:
    """
    Утилита для быстрого расчета резерва товара
    
    Args:
        reserved_stock: Резерв товара
        current_stock: Текущий остаток
        
    Returns:
        Dict с результатами расчета
    """
    calculator = ReserveCalculatorService()
    return calculator.calculate_reserve_display(reserved_stock, current_stock)