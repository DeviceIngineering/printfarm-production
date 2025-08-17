"""
МойСклад API client for PrintFarm production system.
"""
import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from urllib.parse import urljoin

import httpx
import requests
from django.conf import settings
from django.core.files.base import ContentFile

from apps.core.exceptions import MoySkladAPIException

logger = logging.getLogger(__name__)

class MoySkladClient:
    """
    Client for МойСклад API with rate limiting and error handling.
    """
    
    def __init__(self):
        self.config = settings.MOYSKLAD_CONFIG
        self.base_url = self.config['base_url']
        self.token = self.config['token']
        self.rate_limit = self.config['rate_limit']
        self.retry_attempts = self.config['retry_attempts']
        self.timeout = self.config['timeout']
        
        self.session = requests.Session()
        # МойСклад использует токен напрямую в заголовке Authorization
        self.session.headers.update({
            'Authorization': f'Bearer {self.token}',
            'Accept-Encoding': 'gzip',
            'Accept': 'application/json;charset=utf-8',  # МойСклад требует точно такой формат
            'Content-Type': 'application/json;charset=utf-8'
        })
        
        self._last_request_time = 0
    
    def _rate_limit_wait(self):
        """
        Ensure rate limiting compliance.
        """
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        min_interval = 1.0 / self.rate_limit
        
        if time_since_last < min_interval:
            time.sleep(min_interval - time_since_last)
        
        self._last_request_time = time.time()
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make a rate-limited request to МойСклад API.
        """
        self._rate_limit_wait()
        
        url = urljoin(self.base_url + '/', endpoint)
        
        # Отладочный вывод
        logger.info(f"Making request to: {url}")
        logger.info(f"Headers: {self.session.headers}")
        
        for attempt in range(self.retry_attempts):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    timeout=self.timeout,
                    **kwargs
                )
                
                if response.status_code == 429:  # Rate limit exceeded
                    retry_after = int(response.headers.get('Retry-After', 60))
                    logger.warning(f"Rate limit exceeded, waiting {retry_after} seconds")
                    time.sleep(retry_after)
                    continue
                
                logger.info(f"Response status: {response.status_code}")
                if response.status_code != 200:
                    logger.error(f"Response content: {response.text}")
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request attempt {attempt + 1} failed: {str(e)}")
                if attempt == self.retry_attempts - 1:
                    raise MoySkladAPIException(
                        f"Failed to make request after {self.retry_attempts} attempts: {str(e)}",
                        status_code=getattr(response, 'status_code', None) if 'response' in locals() else None
                    )
                time.sleep(2 ** attempt)  # Exponential backoff
    
    def get_warehouses(self) -> List[Dict]:
        """
        Get list of warehouses from МойСклад.
        """
        try:
            data = self._make_request('GET', 'entity/store')
            warehouses = data.get('rows', [])
            
            # Преобразуем в нужный формат для frontend
            result = []
            for warehouse in warehouses:
                result.append({
                    'id': warehouse.get('id'),
                    'name': warehouse.get('name'),
                    'code': warehouse.get('externalCode', ''),
                    'address': warehouse.get('address', ''),
                    'archived': warehouse.get('archived', False)
                })
            
            return result
        except Exception as e:
            logger.error(f"Failed to get warehouses: {str(e)}")
            raise e  # Пробросим ошибку дальше для отладки
    
    def get_product_groups(self) -> List[Dict]:
        """
        Get list of product groups from МойСклад.
        """
        try:
            data = self._make_request('GET', 'entity/productfolder')
            groups = data.get('rows', [])
            
            # Преобразуем в нужный формат для frontend
            result = []
            for group in groups:
                result.append({
                    'id': group.get('id'),
                    'name': group.get('name'),
                    'pathName': group.get('pathName', group.get('name', '')),
                    'code': group.get('externalCode', ''),
                    'archived': group.get('archived', False),
                    'parent': {
                        'id': group.get('productFolder', {}).get('id'),
                        'name': group.get('productFolder', {}).get('name')
                    } if group.get('productFolder') else None
                })
            
            return result
        except Exception as e:
            logger.error(f"Failed to get product groups: {str(e)}")
            raise e  # Пробросим ошибку дальше для отладки
    
    def get_stock_report(self, warehouse_id: str, product_group_ids: List[str] = None) -> List[Dict]:
        """
        Get stock report from МойСклад.
        """
        # МойСклад требует полный href для склада в фильтре
        store_href = f"{self.base_url}/entity/store/{warehouse_id}"
        params = {
            'filter': f'store={store_href}',
            'limit': 1000
        }
        
        try:
            data = self._make_request('GET', 'report/stock/all', params=params)
            rows = data.get('rows', [])
            
            # Фильтруем исключенные группы товаров на уровне приложения
            if product_group_ids:
                logger.info(f"Filtering out {len(product_group_ids)} excluded groups: {product_group_ids}")
                filtered_rows = []
                excluded_count = 0
                
                for row in rows:
                    # Проверяем, относится ли товар к исключенным группам
                    folder = row.get('folder')
                    if folder and folder.get('meta', {}).get('href'):
                        folder_id = folder['meta']['href'].split('/')[-1]
                        if folder_id in product_group_ids:
                            excluded_count += 1
                            continue  # Пропускаем товары из исключенных групп
                    
                    filtered_rows.append(row)
                
                logger.info(f"Excluded {excluded_count} products from {len(product_group_ids)} groups. Remaining: {len(filtered_rows)} products")
                return filtered_rows
            
            return rows
        except Exception as e:
            logger.error(f"Failed to get stock report: {str(e)}")
            return []
    
    def get_all_products_with_stock(self, warehouse_id: str, excluded_group_ids: List[str] = None) -> List[Dict]:
        """
        Get all products from МойСклад (including those with zero stock).
        Optimized version that combines product list with stock information.
        """
        try:
            # Получаем все товары
            params = {
                'limit': 1000,
                'archived': False  # Исключаем архивные товары
            }
            
            data = self._make_request('GET', 'entity/product', params=params)
            all_products = data.get('rows', [])
            
            logger.info(f"Fetched {len(all_products)} total products from МойСклад")
            
            # Фильтруем исключенные группы
            if excluded_group_ids:
                logger.info(f"Filtering out {len(excluded_group_ids)} excluded groups: {excluded_group_ids}")
                filtered_products = []
                excluded_count = 0
                
                for product in all_products:
                    # Проверяем, относится ли товар к исключенным группам
                    folder = product.get('productFolder')
                    if folder and folder.get('meta', {}).get('href'):
                        folder_id = folder['meta']['href'].split('/')[-1]
                        if folder_id in excluded_group_ids:
                            excluded_count += 1
                            continue  # Пропускаем товары из исключенных групп
                    
                    filtered_products.append(product)
                
                logger.info(f"Excluded {excluded_count} products from {len(excluded_group_ids)} groups. Remaining: {len(filtered_products)} products")
                all_products = filtered_products
            
            # Получаем ПОЛНЫЙ отчет по остаткам (включая нулевые)
            store_href = f"{self.base_url}/entity/store/{warehouse_id}"
            stock_params = {
                'filter': f'store={store_href}',
                'limit': 1000,
                'includeZeroStocks': True  # Включаем товары с нулевыми остатками
            }
            
            try:
                stock_data = self._make_request('GET', 'report/stock/all', params=stock_params)
                stock_rows = stock_data.get('rows', [])
                logger.info(f"Fetched {len(stock_rows)} stock records from МойСклад")
            except Exception as e:
                logger.warning(f"Failed to get stock report with zero stocks: {str(e)}")
                stock_rows = []
            
            # Создаем словарь остатков по ID товара
            stock_by_product_id = {}
            for stock_row in stock_rows:
                product_meta = stock_row.get('meta', {})
                if product_meta.get('href'):
                    # Убираем параметры запроса из href
                    href = product_meta['href']
                    product_id = href.split('/')[-1].split('?')[0]
                    stock_by_product_id[product_id] = stock_row
            
            # Комбинируем товары с информацией об остатках
            result_products = []
            for product in all_products:
                product_id = product.get('id')
                if not product_id:
                    continue
                
                # Ищем информацию об остатках для этого товара
                stock_info = stock_by_product_id.get(product_id)
                
                if stock_info:
                    # Используем информацию из отчета по остаткам
                    result_products.append(stock_info)
                else:
                    # Создаем запись с нулевым остатком
                    stock_info = {
                        'meta': product.get('meta'),
                        'name': product.get('name'),
                        'code': product.get('code'),
                        'article': product.get('article'),
                        'folder': product.get('productFolder'),
                        'stock': 0,  # Нулевой остаток
                        'quantity': 0,
                        'price': 0
                    }
                    result_products.append(stock_info)
            
            logger.info(f"Successfully processed {len(result_products)} products with stock information")
            return result_products
            
        except Exception as e:
            logger.error(f"Failed to get all products with stock: {str(e)}")
            return []
    
    def get_turnover_report(self, warehouse_id: str, date_from: datetime, date_to: datetime) -> List[Dict]:
        """
        Get turnover report from МойСклад.
        """
        # МойСклад требует полный href для склада в фильтре
        store_href = f"{self.base_url}/entity/store/{warehouse_id}"
        params = {
            'filter': f'store={store_href}',
            'momentFrom': date_from.strftime('%Y-%m-%d %H:%M:%S'),
            'momentTo': date_to.strftime('%Y-%m-%d %H:%M:%S'),
            'limit': 1000
        }
        
        try:
            data = self._make_request('GET', 'report/turnover/all', params=params)
            return data.get('rows', [])
        except Exception as e:
            logger.error(f"Failed to get turnover report: {str(e)}")
            return []
    
    def get_product_images(self, product_id: str) -> List[Dict]:
        """
        Get product images from МойСклад.
        """
        try:
            data = self._make_request('GET', f'entity/product/{product_id}/images')
            return data.get('rows', [])
        except Exception as e:
            logger.error(f"Failed to get product images for {product_id}: {str(e)}")
            return []
    
    def download_image(self, image_url: str) -> Optional[bytes]:
        """
        Download image from МойСклад.
        """
        try:
            self._rate_limit_wait()
            
            response = self.session.get(
                image_url,
                timeout=self.timeout,
                headers={'Authorization': f'Bearer {self.token}'}
            )
            response.raise_for_status()
            return response.content
        except Exception as e:
            logger.error(f"Failed to download image {image_url}: {str(e)}")
            return None
    
    def get_products_batch(self, offset: int = 0, limit: int = 1000) -> Dict[str, Any]:
        """
        Get products in batches from МойСклад.
        """
        params = {
            'offset': offset,
            'limit': limit,
            'expand': 'productFolder'
        }
        
        try:
            return self._make_request('GET', 'entity/product', params=params)
        except Exception as e:
            logger.error(f"Failed to get products batch: {str(e)}")
            return {'rows': [], 'meta': {'size': 0}}
    
    def test_connection(self) -> bool:
        """
        Test connection to МойСклад API.
        """
        try:
            self._make_request('GET', 'context/employee')
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False
    
    def extract_color_from_attributes(self, attributes: List[Dict]) -> str:
        """
        Извлекает значение цвета из атрибутов товара МойСклад.
        
        Args:
            attributes: Список атрибутов товара из МойСклад API
            
        Returns:
            Значение цвета или пустая строка, если цвет не найден
        """
        if not attributes:
            return ''
        
        # Ищем атрибут с названием "Цвет" (нечувствительно к регистру)
        for attr in attributes:
            attr_name = attr.get('name', '').lower().strip()
            if attr_name == 'цвет':
                color_value = attr.get('value', '')
                if color_value:
                    # ИСПРАВЛЕНИЕ: Обрабатываем случай, когда value - это объект (customentity)
                    if isinstance(color_value, dict):
                        # Для custom entity извлекаем поле 'name'
                        color_name = color_value.get('name', '')
                        if color_name:
                            logger.debug(f"Найден цвет товара (из customentity): {color_name}")
                            return str(color_name).strip()
                    else:
                        # Для простых строковых значений
                        logger.debug(f"Найден цвет товара (строка): {color_value}")
                        return str(color_value).strip()
        
        return ''
    
    def get_product_details(self, product_id: str) -> Dict[str, Any]:
        """
        Получает детальную информацию о товаре, включая атрибуты.
        
        Args:
            product_id: ID товара в МойСклад
            
        Returns:
            Детальная информация о товаре с атрибутами
        """
        try:
            # Запрашиваем товар с атрибутами
            params = {
                'expand': 'attributes'
            }
            
            product_data = self._make_request('GET', f'entity/product/{product_id}', params=params)
            
            # Извлекаем цвет из атрибутов
            attributes = product_data.get('attributes', [])
            color = self.extract_color_from_attributes(attributes)
            
            # Добавляем цвет в данные товара
            product_data['color'] = color
            
            logger.debug(f"Получена детальная информация о товаре {product_id}, цвет: {color}")
            
            return product_data
            
        except Exception as e:
            logger.error(f"Ошибка при получении деталей товара {product_id}: {str(e)}")
            return {}