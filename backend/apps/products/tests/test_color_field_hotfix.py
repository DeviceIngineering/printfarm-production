"""
Регрессионные тесты для hotfix color field JSON parsing
"""
import json
from django.test import TestCase
from apps.sync.moysklad_client import MoySkladClient


class ColorFieldHotfixRegressionTests(TestCase):
    """
    Регрессионные тесты для исправления проблемы с JSON парсингом цвета
    """
    
    def setUp(self):
        self.client = MoySkladClient()
    
    def test_extract_color_from_customentity_object(self):
        """
        Тест: Извлечение цвета из customentity объекта (основная проблема)
        """
        # Реальный пример данных из МойСклад API
        attributes = [
            {
                'id': 'color-attr-id',
                'name': 'Цвет',
                'value': {
                    'meta': {
                        'href': 'https://api.moysklad.ru/api/remap/1.2/entity/customentity/a727977a-a753-11ef-0a80-182c00160918/f5d6d1fd-a754-11ef-0a80-0d8500168db3',
                        'metadataHref': 'https://api.moysklad.ru/api/remap/1.2/context/companysettings/metadata/customEntities/a727977a-a753-11ef-0a80-182c00160918',
                        'type': 'customentity',
                        'mediaType': 'application/json',
                        'uuidHref': 'https://online.moysklad.ru/app/#custom_a727977a-a753-11ef-0a80-182c00160918/edit?id=f5d6d1fd-a754-11ef-0a80-0d8500168db3'
                    },
                    'name': 'Черный'
                }
            }
        ]
        
        # Извлекаем цвет
        color = self.client.extract_color_from_attributes(attributes)
        
        # Проверяем, что извлекается именно название цвета, а не JSON
        self.assertEqual(color, 'Черный')
        self.assertNotIn('{', color)  # Не должно содержать JSON структуру
        self.assertNotIn('meta', color)  # Не должно содержать meta данные
    
    def test_extract_color_from_simple_string_value(self):
        """
        Тест: Обратная совместимость - извлечение цвета из простой строки
        """
        attributes = [
            {
                'id': 'color-attr-id',
                'name': 'Цвет',
                'value': 'Красный'  # Простая строка
            }
        ]
        
        color = self.client.extract_color_from_attributes(attributes)
        self.assertEqual(color, 'Красный')
    
    def test_extract_color_handles_empty_customentity(self):
        """
        Тест: Обработка пустого customentity объекта
        """
        attributes = [
            {
                'id': 'color-attr-id',
                'name': 'Цвет',
                'value': {
                    'meta': {'type': 'customentity'},
                    'name': ''  # Пустое название
                }
            }
        ]
        
        color = self.client.extract_color_from_attributes(attributes)
        self.assertEqual(color, '')
    
    def test_extract_color_handles_malformed_customentity(self):
        """
        Тест: Обработка некорректного customentity объекта
        """
        attributes = [
            {
                'id': 'color-attr-id',
                'name': 'Цвет',
                'value': {
                    'meta': {'type': 'customentity'}
                    # Отсутствует поле 'name'
                }
            }
        ]
        
        color = self.client.extract_color_from_attributes(attributes)
        self.assertEqual(color, '')
    
    def test_extract_color_with_whitespace_in_customentity(self):
        """
        Тест: Обработка пробелов в названии цвета из customentity
        """
        attributes = [
            {
                'id': 'color-attr-id',
                'name': 'Цвет',
                'value': {
                    'meta': {'type': 'customentity'},
                    'name': '  Синий  '  # С пробелами
                }
            }
        ]
        
        color = self.client.extract_color_from_attributes(attributes)
        self.assertEqual(color, 'Синий')  # Пробелы должны быть удалены
    
    def test_extract_color_with_special_characters_in_customentity(self):
        """
        Тест: Обработка специальных символов в названии цвета
        """
        attributes = [
            {
                'id': 'color-attr-id',
                'name': 'Цвет',
                'value': {
                    'meta': {'type': 'customentity'},
                    'name': 'Красно-синий #FF5733'
                }
            }
        ]
        
        color = self.client.extract_color_from_attributes(attributes)
        self.assertEqual(color, 'Красно-синий #FF5733')
    
    def test_extract_color_case_insensitive_with_customentity(self):
        """
        Тест: Поиск атрибута "Цвет" нечувствителен к регистру (с customentity)
        """
        test_cases = [
            {'name': 'цвет', 'value': {'name': 'Зелёный'}},
            {'name': 'ЦВЕТ', 'value': {'name': 'Жёлтый'}},
            {'name': 'Цвет', 'value': {'name': 'Синий'}},
            {'name': 'ЦвЕт', 'value': {'name': 'Фиолетовый'}}
        ]
        
        for case in test_cases:
            attributes = [case]
            color = self.client.extract_color_from_attributes(attributes)
            expected_color = case['value']['name']
            self.assertEqual(color, expected_color, 
                           f"Не удалось извлечь цвет для атрибута '{case['name']}'")
    
    def test_extract_color_no_json_serialization_in_result(self):
        """
        Тест: Результат не содержит JSON сериализации (основная проблема)
        """
        # Сложный customentity объект
        complex_value = {
            'meta': {
                'href': 'https://api.moysklad.ru/api/remap/1.2/entity/customentity/test',
                'type': 'customentity',
                'mediaType': 'application/json'
            },
            'id': 'test-color-id',
            'name': 'Белый',
            'description': 'Описание цвета',
            'externalCode': 'WHITE_001'
        }
        
        attributes = [
            {
                'id': 'color-attr-id',
                'name': 'Цвет',
                'value': complex_value
            }
        ]
        
        color = self.client.extract_color_from_attributes(attributes)
        
        # Основные проверки
        self.assertEqual(color, 'Белый')
        self.assertIsInstance(color, str)
        self.assertNotIn('{', color)  # Не JSON
        self.assertNotIn('"', color)  # Не сериализованная строка
        self.assertNotIn('meta', color)  # Не содержит метаданные
        self.assertNotIn('href', color)  # Не содержит ссылки
        
        # Проверка, что это именно строка, а не JSON string
        try:
            json.loads(color)
            self.fail("Цвет не должен быть валидным JSON!")
        except (json.JSONDecodeError, TypeError):
            pass  # Это хорошо - цвет не является JSON
    
    def test_no_regression_in_production_scenario(self):
        """
        Тест: Проверка отсутствия регрессии в реальном сценарии
        """
        # Имитируем реальные данные, которые приходят из МойСклад
        production_scenario_attributes = [
            {
                'id': 'weight-attr',
                'name': 'Вес',
                'value': '1.5'
            },
            {
                'id': 'color-attr',
                'name': 'Цвет',
                'value': {
                    'meta': {
                        'href': 'https://api.moysklad.ru/api/remap/1.2/entity/customentity/a727977a-a753-11ef-0a80-182c00160918/f5d6d1fd-a754-11ef-0a80-0d8500168db3',
                        'metadataHref': 'https://api.moysklad.ru/api/remap/1.2/context/companysettings/metadata/customEntities/a727977a-a753-11ef-0a80-182c00160918',
                        'type': 'customentity',
                        'mediaType': 'application/json'
                    },
                    'name': 'Черный'
                }
            },
            {
                'id': 'size-attr',
                'name': 'Размер',
                'value': 'XL'
            }
        ]
        
        # Извлекаем цвет
        color = self.client.extract_color_from_attributes(production_scenario_attributes)
        
        # Проверяем корректность
        self.assertEqual(color, 'Черный')
        self.assertEqual(len(color), 6)  # Длина строки "Черный"
        self.assertTrue(color.isalpha() or ' ' in color)  # Только буквы или пробелы