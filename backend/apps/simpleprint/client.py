"""
SimplePrint API Client

Клиент для работы с SimplePrint API.
Поддерживает rate limiting и retry логику.
"""

import time
import logging
import requests
from typing import Dict, List, Optional
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class SimplePrintAPIError(Exception):
    """Исключение для ошибок SimplePrint API"""
    pass


class SimplePrintFilesClient:
    """
    Клиент для работы с файлами и папками в SimplePrint API
    """

    def __init__(self):
        """Инициализация клиента"""
        config = settings.SIMPLEPRINT_CONFIG

        self.base_url = config['base_url'].rstrip('/')
        self.api_token = config['api_token']
        self.rate_limit = config['rate_limit']  # requests per minute

        # Вычисляем задержку между запросами
        self.request_delay = 60.0 / self.rate_limit  # секунды между запросами

        self.retry_attempts = 2  # Уменьшили количество попыток
        self.timeout = 10  # Уменьшили timeout до 10 секунд (было 30)

        # Последнее время запроса для rate limiting
        self._last_request_time = 0

    def _get_headers(self) -> Dict[str, str]:
        """Получить заголовки для запроса"""
        return {
            'X-API-KEY': self.api_token,
            'Accept': 'application/json',
        }

    def _rate_limit(self):
        """Применить rate limiting"""
        current_time = time.time()
        time_since_last_request = current_time - self._last_request_time

        if time_since_last_request < self.request_delay:
            sleep_time = self.request_delay - time_since_last_request
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)

        self._last_request_time = time.time()

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        retry_count: int = 0
    ) -> Dict:
        """
        Выполнить HTTP запрос с retry логикой

        Args:
            method: HTTP метод (GET, POST)
            endpoint: API endpoint
            params: Query параметры
            data: Данные для POST запроса
            retry_count: Текущая попытка (для рекурсии)

        Returns:
            Ответ от API в виде словаря

        Raises:
            SimplePrintAPIError: При ошибке API
        """
        # Применяем rate limiting
        self._rate_limit()

        url = f"{self.base_url}/{endpoint}"
        headers = self._get_headers()

        try:
            logger.debug(f"{method} {url} (попытка {retry_count + 1}/{self.retry_attempts})")

            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=self.timeout)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data, timeout=self.timeout)
            else:
                raise SimplePrintAPIError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()

            data = response.json()

            # Проверяем статус ответа SimplePrint
            if not data.get('status', False):
                error_message = data.get('message', 'Unknown error')
                logger.error(f"SimplePrint API error: {error_message}")
                raise SimplePrintAPIError(f"API returned error: {error_message}")

            return data

        except requests.exceptions.Timeout:
            logger.warning(f"Request timeout for {url}")
            if retry_count < self.retry_attempts - 1:
                return self._make_request(method, endpoint, params, data, retry_count + 1)
            raise SimplePrintAPIError(f"Request timeout after {self.retry_attempts} attempts")

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
            if retry_count < self.retry_attempts - 1 and e.response.status_code >= 500:
                # Retry только для серверных ошибок
                time.sleep(2 ** retry_count)  # Exponential backoff
                return self._make_request(method, endpoint, params, data, retry_count + 1)
            raise SimplePrintAPIError(f"HTTP error {e.response.status_code}: {e.response.text}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            if retry_count < self.retry_attempts - 1:
                time.sleep(2 ** retry_count)  # Exponential backoff
                return self._make_request(method, endpoint, params, data, retry_count + 1)
            raise SimplePrintAPIError(f"Request failed: {e}")

    def test_connection(self) -> bool:
        """
        Проверить подключение к API

        Returns:
            True если подключение успешно
        """
        try:
            response = self._make_request('GET', 'account/Test')
            return response.get('status', False)
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    def get_files_and_folders(self, parent_folder_id: Optional[int] = None) -> Dict:
        """
        Получить список файлов и папок

        Args:
            parent_folder_id: ID родительской папки (None = корень)

        Returns:
            Словарь с ключами 'files' и 'folders'
        """
        params = {}
        if parent_folder_id is not None:
            params['f'] = parent_folder_id  # SimplePrint API использует параметр 'f'

        # Кэшируем на 5 минут (если Redis доступен)
        cache_key = f'simpleprint_files_folders_{parent_folder_id}'
        try:
            cached_data = cache.get(cache_key)
            if cached_data:
                logger.debug(f"Using cached data for folder {parent_folder_id}")
                return cached_data
        except Exception as e:
            logger.debug(f"Cache unavailable: {e}")

        logger.info(f"Fetching files and folders for parent_id={parent_folder_id}")
        data = self._make_request('GET', 'files/GetFiles', params=params)

        result = {
            'files': data.get('files', []),
            'folders': data.get('folders', []),
            'folder': data.get('folder'),
            'path': data.get('path', []),
            'space': data.get('space', 0),
            'space_used': data.get('space_used', 0),
        }

        try:
            cache.set(cache_key, result, 300)  # 5 минут
        except Exception as e:
            logger.debug(f"Could not cache result: {e}")

        return result

    def get_folder_details(self, folder_id: int) -> Dict:
        """
        Получить детальную информацию о папке

        Args:
            folder_id: ID папки

        Returns:
            Информация о папке
        """
        logger.info(f"Fetching folder details for folder_id={folder_id}")

        params = {'id': folder_id}
        data = self._make_request('GET', 'files/GetFolder', params=params)

        return data.get('folder', {})

    def get_all_files_recursive(
        self,
        parent_folder_id: Optional[int] = None,
        max_depth: int = 50
    ) -> Dict[str, List]:
        """
        Рекурсивно получить все файлы и папки

        Args:
            parent_folder_id: ID родительской папки (None = корень)
            max_depth: Максимальная глубина рекурсии (защита от бесконечных циклов)

        Returns:
            Словарь с ключами 'all_files', 'all_folders', 'folder_count', 'file_count'
        """
        all_files = []
        all_folders = []
        visited_folders = set()  # Защита от циклических ссылок
        folder_count = 0
        file_count = 0

        def fetch_recursive(folder_id: Optional[int], current_path: str = "", depth: int = 0):
            """Рекурсивная функция для получения всех файлов"""
            nonlocal folder_count, file_count

            # Защита от слишком глубокой рекурсии
            if depth > max_depth:
                logger.warning(f"⚠️ Максимальная глубина рекурсии достигнута ({max_depth}) для пути: {current_path}")
                return

            # Проверяем на циклические ссылки
            folder_key = folder_id if folder_id is not None else 'root'
            if folder_key in visited_folders:
                logger.warning(f"⚠️ Пропуск уже посещенной папки ID={folder_id} (путь: {current_path})")
                return

            visited_folders.add(folder_key)
            logger.debug(f"📂 Добавляем в visited: {folder_key} (глубина: {depth})")

            data = self.get_files_and_folders(folder_id)

            # Добавляем файлы текущей папки
            files = data['files']
            for file in files:
                file['path'] = current_path  # Добавляем путь к файлу
                file['parent_folder_id'] = folder_id  # Добавляем ID родительской папки
                all_files.append(file)
                file_count += 1
                logger.debug(f"📄 Файл: {file.get('name')} в {current_path}")

            # Добавляем папки и рекурсивно обрабатываем подпапки
            folders = data['folders']
            for folder in folders:
                folder_count += 1
                folder_name = folder.get('name', 'Без названия')
                full_path = f"{current_path}/{folder_name}".strip("/")
                folder['path'] = full_path  # Добавляем путь к папке
                all_folders.append(folder)

                logger.info(f"📁 Папка: {full_path} (ID: {folder.get('id')}, глубина: {depth + 1})")

            logger.debug(f"Папка {folder_id}: {len(folders)} подпапок, {len(files)} файлов")

            # Рекурсивно обрабатываем подпапки
            for folder in folders:
                folder_name = folder.get('name', 'Без названия')
                full_path = f"{current_path}/{folder_name}".strip("/")
                fetch_recursive(folder['id'], full_path, depth + 1)

        logger.info(f"📂 Загружаем структуру SimplePrint (начало рекурсивного обхода)...")
        fetch_recursive(parent_folder_id)

        logger.info(f"✅ Готово! Папок: {folder_count}, файлов: {file_count} из {len(visited_folders)} уникальных локаций")

        return {
            'all_files': all_files,
            'all_folders': all_folders,
            'folder_count': folder_count,
            'file_count': file_count,
        }


class SimplePrintPrintersClient:
    """
    Клиент для работы с принтерами в SimplePrint API
    """

    def __init__(self):
        """Инициализация клиента"""
        config = settings.SIMPLEPRINT_CONFIG

        self.base_url = config['base_url'].rstrip('/')
        self.api_token = config['api_token']
        self.rate_limit = config['rate_limit']  # requests per minute

        # Вычисляем задержку между запросами
        self.request_delay = 60.0 / self.rate_limit  # секунды между запросами

        self.retry_attempts = 2  # Уменьшили количество попыток
        self.timeout = 10  # Уменьшили timeout до 10 секунд (было 30)

        # Последнее время запроса для rate limiting
        self._last_request_time = 0

    def _get_headers(self) -> Dict[str, str]:
        """Получить заголовки для запроса"""
        return {
            'X-API-KEY': self.api_token,
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }

    def _rate_limit(self):
        """Применить rate limiting"""
        current_time = time.time()
        time_since_last_request = current_time - self._last_request_time

        if time_since_last_request < self.request_delay:
            sleep_time = self.request_delay - time_since_last_request
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)

        self._last_request_time = time.time()

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        retry_count: int = 0
    ) -> Dict:
        """
        Выполнить HTTP запрос с retry логикой

        Args:
            method: HTTP метод (GET, POST)
            endpoint: API endpoint
            params: Query параметры
            data: Данные для POST запроса
            retry_count: Текущая попытка (для рекурсии)

        Returns:
            Ответ от API в виде словаря

        Raises:
            SimplePrintAPIError: При ошибке API
        """
        # Применяем rate limiting
        self._rate_limit()

        url = f"{self.base_url}/{endpoint}"
        headers = self._get_headers()

        try:
            logger.debug(f"{method} {url} (попытка {retry_count + 1}/{self.retry_attempts})")

            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=self.timeout)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data, timeout=self.timeout)
            else:
                raise SimplePrintAPIError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()

            data = response.json()

            # Проверяем статус ответа SimplePrint
            if not data.get('status', False):
                error_message = data.get('message', 'Unknown error')
                logger.error(f"SimplePrint API error: {error_message}")
                raise SimplePrintAPIError(f"API returned error: {error_message}")

            return data

        except requests.exceptions.Timeout:
            logger.warning(f"Request timeout for {url}")
            if retry_count < self.retry_attempts - 1:
                return self._make_request(method, endpoint, params, data, retry_count + 1)
            raise SimplePrintAPIError(f"Request timeout after {self.retry_attempts} attempts")

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
            if retry_count < self.retry_attempts - 1 and e.response.status_code >= 500:
                # Retry только для серверных ошибок
                time.sleep(2 ** retry_count)  # Exponential backoff
                return self._make_request(method, endpoint, params, data, retry_count + 1)
            raise SimplePrintAPIError(f"HTTP error {e.response.status_code}: {e.response.text}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            if retry_count < self.retry_attempts - 1:
                time.sleep(2 ** retry_count)  # Exponential backoff
                return self._make_request(method, endpoint, params, data, retry_count + 1)
            raise SimplePrintAPIError(f"Request failed: {e}")

    def get_printers(self) -> List[Dict]:
        """
        Получить список всех принтеров с их состоянием

        Returns:
            Список принтеров с подробной информацией
        """
        logger.info("Fetching all printers from SimplePrint API")

        try:
            response = self._make_request('POST', 'printers/Get')
            printers_data = response.get('data', [])

            logger.info(f"Successfully fetched {len(printers_data)} printers")
            return printers_data

        except Exception as e:
            logger.error(f"Failed to fetch printers: {e}")
            raise SimplePrintAPIError(f"Failed to fetch printers: {e}")

    def get_jobs_history(self, limit: int = 200) -> List[Dict]:
        """
        Получить историю печатных заданий

        Args:
            limit: Максимальное количество заданий для получения (по умолчанию 200)

        Returns:
            Список заданий с подробной информацией
        """
        logger.info(f"Fetching jobs history from SimplePrint API (limit={limit})")

        try:
            # SimplePrint API endpoint для получения истории заданий
            response = self._make_request('POST', 'jobs/GetHistory', data={'limit': limit})
            jobs_data = response.get('data', [])

            logger.info(f"Successfully fetched {len(jobs_data)} jobs")
            return jobs_data

        except Exception as e:
            logger.error(f"Failed to fetch jobs history: {e}")
            raise SimplePrintAPIError(f"Failed to fetch jobs history: {e}")

    def get_printer_jobs(self, printer_id: str) -> Dict:
        """
        Получить текущее задание и очередь для конкретного принтера

        Args:
            printer_id: ID принтера в SimplePrint

        Returns:
            Словарь с current_job и queue
        """
        logger.info(f"Fetching jobs for printer {printer_id}")

        try:
            response = self._make_request('POST', 'printers/Get', data={'id': printer_id})
            printer_data = response.get('data', {})

            return {
                'current_job': printer_data.get('current_job'),
                'queue': printer_data.get('queue', [])
            }

        except Exception as e:
            logger.error(f"Failed to fetch jobs for printer {printer_id}: {e}")
            raise SimplePrintAPIError(f"Failed to fetch jobs for printer {printer_id}: {e}")
