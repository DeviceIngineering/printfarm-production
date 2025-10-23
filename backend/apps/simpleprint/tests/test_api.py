"""
Тесты SimplePrint API Endpoints
Цель: Проверить REST API endpoints с детальной диагностикой
"""

import pytest
import logging
from unittest.mock import patch, MagicMock
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from apps.simpleprint.models import SimplePrintSync, SimplePrintFile, SimplePrintFolder

logger = logging.getLogger(__name__)


@pytest.mark.django_db
class TestSimplePrintAPI:
    """Тестирование SimplePrint REST API"""

    @pytest.fixture
    def api_client(self):
        """Создать API клиент с аутентификацией"""
        client = APIClient()

        # Создаем пользователя и токен
        user = User.objects.create_user(username='testuser', password='testpass')
        token = Token.objects.create(user=user)

        # Устанавливаем токен в заголовки
        client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        return client

    def test_01_trigger_sync_endpoint(self, api_client):
        """
        ✅/❌ Тест 1: POST /api/v1/simpleprint/sync/trigger/
        Проверяет: запуск синхронизации через API
        """
        print("\n" + "="*80)
        print("🌐 ТЕСТ 1: POST /api/v1/simpleprint/sync/trigger/")
        print("="*80)

        try:
            url = '/api/v1/simpleprint/sync/trigger/'
            data = {
                'full_sync': False,
                'force': False
            }

            print(f"📡 Запрос:")
            print(f"   - URL: {url}")
            print(f"   - Method: POST")
            print(f"   - Data: {data}")
            print(f"   - Headers: Authorization: Token ***")

            with patch('apps.simpleprint.tasks.sync_simpleprint_task') as mock_task:
                # Мокаем Celery task
                mock_async_result = MagicMock()
                mock_async_result.id = 'test-task-id-123'
                mock_task.delay.return_value = mock_async_result

                print(f"\n🧪 Мок: Celery task вернет task_id='test-task-id-123'")

                response = api_client.post(url, data, format='json')

                print(f"\n📥 Ответ API:")
                print(f"   - Status Code: {response.status_code}")
                print(f"   - Data: {response.json()}")

                # Проверки
                assert response.status_code == status.HTTP_202_ACCEPTED, \
                    f"❌ FAIL: Ожидался статус 202, получен {response.status_code}"

                response_data = response.json()
                assert 'task_id' in response_data, "❌ FAIL: В ответе нет 'task_id'"
                assert response_data['status'] == 'started', \
                    f"❌ FAIL: status={response_data.get('status')}, ожидался 'started'"

                # Проверяем что Celery task был вызван
                assert mock_task.delay.called, "❌ FAIL: Celery task не был вызван"
                call_kwargs = mock_task.delay.call_args[1]
                assert call_kwargs['full_sync'] == False, "❌ FAIL: Неверный параметр full_sync"

                print(f"\n✅ PASS: Endpoint работает корректно")
                print(f"   ✓ Статус 202 ACCEPTED")
                print(f"   ✓ task_id возвращен: {response_data['task_id']}")
                print(f"   ✓ Celery task вызван с правильными параметрами")

        except AssertionError as e:
            print(f"\n❌ FAIL: {str(e)}")
            print(f"📍 Файл: backend/apps/simpleprint/views.py")
            print(f"📍 Метод: SimplePrintSyncViewSet.trigger()")
            raise
        except Exception as e:
            print(f"\n❌ FAIL: Ошибка запроса к API")
            print(f"📍 Тип ошибки: {type(e).__name__}")
            print(f"📍 Сообщение: {str(e)}")
            print(f"📍 Файл: backend/apps/simpleprint/views.py")

            import traceback
            print(f"\n🔍 Полный traceback:")
            print(traceback.format_exc())
            raise

    def test_02_sync_status_endpoint(self, api_client):
        """
        ✅/❌ Тест 2: GET /api/v1/simpleprint/sync/status/{task_id}/
        Проверяет: получение статуса задачи
        """
        print("\n" + "="*80)
        print("🌐 ТЕСТ 2: GET /api/v1/simpleprint/sync/status/{task_id}/")
        print("="*80)

        try:
            task_id = 'test-task-id-456'
            url = f'/api/v1/simpleprint/sync/status/{task_id}/'

            print(f"📡 Запрос:")
            print(f"   - URL: {url}")
            print(f"   - Method: GET")
            print(f"   - Task ID: {task_id}")

            with patch('apps.simpleprint.views.AsyncResult') as mock_async_result:
                # Мокаем результат задачи
                mock_result = MagicMock()
                mock_result.state = 'SUCCESS'
                mock_result.ready.return_value = True
                mock_result.successful.return_value = True
                mock_result.result = {
                    'sync_id': 1,
                    'status': 'success',
                    'total_files': 100,
                    'synced_files': 100,
                }
                mock_async_result.return_value = mock_result

                print(f"\n🧪 Мок: Задача в состоянии SUCCESS")

                response = api_client.get(url)

                print(f"\n📥 Ответ API:")
                print(f"   - Status Code: {response.status_code}")
                print(f"   - Data: {response.json()}")

                # Проверки
                assert response.status_code == status.HTTP_200_OK, \
                    f"❌ FAIL: Ожидался статус 200, получен {response.status_code}"

                response_data = response.json()
                assert 'state' in response_data, "❌ FAIL: В ответе нет 'state'"
                assert response_data['state'] == 'SUCCESS', \
                    f"❌ FAIL: state={response_data.get('state')}, ожидался 'SUCCESS'"
                assert response_data['ready'] is True, "❌ FAIL: ready != True"

                print(f"\n✅ PASS: Endpoint работает корректно")
                print(f"   ✓ Статус 200 OK")
                print(f"   ✓ State: {response_data['state']}")
                print(f"   ✓ Ready: {response_data['ready']}")
                print(f"   ✓ Result данные получены")

        except AssertionError as e:
            print(f"\n❌ FAIL: {str(e)}")
            print(f"📍 Файл: backend/apps/simpleprint/views.py")
            print(f"📍 Метод: SimplePrintSyncViewSet.task_status()")
            raise
        except Exception as e:
            print(f"\n❌ FAIL: Ошибка запроса к API")
            print(f"📍 Тип ошибки: {type(e).__name__}")
            print(f"📍 Сообщение: {str(e)}")

            import traceback
            print(f"\n🔍 Полный traceback:")
            print(traceback.format_exc())
            raise

    def test_03_sync_stats_endpoint(self, api_client):
        """
        ✅/❌ Тест 3: GET /api/v1/simpleprint/sync/stats/
        Проверяет: получение статистики синхронизации
        """
        print("\n" + "="*80)
        print("🌐 ТЕСТ 3: GET /api/v1/simpleprint/sync/stats/")
        print("="*80)

        try:
            url = '/api/v1/simpleprint/sync/stats/'

            # Создаем тестовые данные
            folder = SimplePrintFolder.objects.create(
                simpleprint_id=12345,
                name='Test Folder',
                depth=0,
                files_count=5,
                folders_count=0
            )

            for i in range(5):
                SimplePrintFile.objects.create(
                    simpleprint_id=f'file_{i}',
                    name=f'test_file_{i}.gcode',
                    folder=folder,
                    ext='gcode',
                    file_type='gcode',
                    size=1000000 * (i + 1)
                )

            print(f"📊 Тестовые данные созданы:")
            print(f"   - Папок: 1")
            print(f"   - Файлов: 5")

            print(f"\n📡 Запрос:")
            print(f"   - URL: {url}")
            print(f"   - Method: GET")

            response = api_client.get(url)

            print(f"\n📥 Ответ API:")
            print(f"   - Status Code: {response.status_code}")
            print(f"   - Data: {response.json()}")

            # Проверки
            assert response.status_code == status.HTTP_200_OK, \
                f"❌ FAIL: Ожидался статус 200, получен {response.status_code}"

            response_data = response.json()
            assert 'total_folders' in response_data, "❌ FAIL: В ответе нет 'total_folders'"
            assert 'total_files' in response_data, "❌ FAIL: В ответе нет 'total_files'"

            assert response_data['total_folders'] == 1, \
                f"❌ FAIL: total_folders={response_data.get('total_folders')}, ожидалось 1"
            assert response_data['total_files'] == 5, \
                f"❌ FAIL: total_files={response_data.get('total_files')}, ожидалось 5"

            print(f"\n✅ PASS: Endpoint работает корректно")
            print(f"   ✓ Статус 200 OK")
            print(f"   ✓ Папок: {response_data['total_folders']}")
            print(f"   ✓ Файлов: {response_data['total_files']}")

        except AssertionError as e:
            print(f"\n❌ FAIL: {str(e)}")
            print(f"📍 Файл: backend/apps/simpleprint/views.py")
            print(f"📍 Метод: SimplePrintSyncViewSet.stats()")
            raise
        except Exception as e:
            print(f"\n❌ FAIL: Ошибка запроса к API")
            print(f"📍 Тип ошибки: {type(e).__name__}")
            print(f"📍 Сообщение: {str(e)}")

            import traceback
            print(f"\n🔍 Полный traceback:")
            print(traceback.format_exc())
            raise

    def test_04_files_list_endpoint(self, api_client):
        """
        ✅/❌ Тест 4: GET /api/v1/simpleprint/files/
        Проверяет: получение списка файлов
        """
        print("\n" + "="*80)
        print("🌐 ТЕСТ 4: GET /api/v1/simpleprint/files/")
        print("="*80)

        try:
            url = '/api/v1/simpleprint/files/'

            # Используем данные из предыдущего теста
            files_count = SimplePrintFile.objects.count()

            print(f"📊 Файлов в БД: {files_count}")

            print(f"\n📡 Запрос:")
            print(f"   - URL: {url}")
            print(f"   - Method: GET")

            response = api_client.get(url)

            print(f"\n📥 Ответ API:")
            print(f"   - Status Code: {response.status_code}")
            response_data = response.json()
            print(f"   - Results: {len(response_data.get('results', []))} items")

            # Проверки
            assert response.status_code == status.HTTP_200_OK, \
                f"❌ FAIL: Ожидался статус 200, получен {response.status_code}"

            assert 'results' in response_data, "❌ FAIL: В ответе нет 'results'"

            results = response_data['results']
            if len(results) > 0:
                first_file = results[0]
                print(f"\n📄 Первый файл:")
                print(f"   - ID: {first_file.get('id')}")
                print(f"   - Name: {first_file.get('name')}")
                print(f"   - Size: {first_file.get('size_display')}")

                # Проверяем структуру
                assert 'id' in first_file, "❌ FAIL: В файле нет 'id'"
                assert 'name' in first_file, "❌ FAIL: В файле нет 'name'"
                assert 'size' in first_file, "❌ FAIL: В файле нет 'size'"

            print(f"\n✅ PASS: Endpoint работает корректно")
            print(f"   ✓ Статус 200 OK")
            print(f"   ✓ Получено {len(results)} файлов")

        except AssertionError as e:
            print(f"\n❌ FAIL: {str(e)}")
            print(f"📍 Файл: backend/apps/simpleprint/views.py")
            print(f"📍 ViewSet: SimplePrintFileViewSet")
            raise
        except Exception as e:
            print(f"\n❌ FAIL: Ошибка запроса к API")
            print(f"📍 Тип ошибки: {type(e).__name__}")
            print(f"📍 Сообщение: {str(e)}")

            import traceback
            print(f"\n🔍 Полный traceback:")
            print(traceback.format_exc())
            raise


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
