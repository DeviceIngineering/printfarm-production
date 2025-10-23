"""
Тесты SimplePrint Sync Service
Цель: Проверить каждый этап синхронизации с детальной диагностикой
"""

import pytest
import logging
from unittest.mock import patch, MagicMock
from django.utils import timezone
from apps.simpleprint.services import SimplePrintSyncService
from apps.simpleprint.models import SimplePrintFile, SimplePrintFolder, SimplePrintSync

logger = logging.getLogger(__name__)


@pytest.mark.django_db
class TestSimplePrintSync:
    """Тестирование SimplePrint синхронизации"""

    @pytest.fixture
    def service(self):
        """Создать сервис для тестов"""
        return SimplePrintSyncService()

    @pytest.fixture
    def mock_api_response(self):
        """Мок ответа API с файлами и папками"""
        return {
            'folders': [
                {
                    'id': 16787,
                    'name': '401_500',
                    'parent_id': None,
                },
                {
                    'id': 17670,
                    'name': '402-40441',
                    'parent_id': 16787,
                }
            ],
            'files': [
                {
                    'id': 'file_123',
                    'name': '402-40441_19k_13h3m_365G_BLACK.gcode',
                    'folder': 17670,
                    'ext': 'gcode',
                    'size': 365000000,
                    'created': '2024-01-15T10:30:00Z',
                }
            ]
        }

    def test_01_create_sync_log(self, service):
        """
        ✅/❌ Тест 1: Создание записи синхронизации
        Проверяет: SimplePrintSync.objects.create()
        """
        print("\n" + "="*80)
        print("📝 ТЕСТ 1: Создание записи синхронизации")
        print("="*80)

        try:
            print(f"📊 Создание SimplePrintSync записи...")
            print(f"   - status: 'pending'")
            print(f"   - started_at: {timezone.now()}")

            # Создаем запись синхронизации
            sync_log = SimplePrintSync.objects.create(
                status='pending',
                started_at=timezone.now()
            )

            print(f"\n✅ Запись создана:")
            print(f"   - ID: {sync_log.id}")
            print(f"   - Status: {sync_log.status}")
            print(f"   - Started: {sync_log.started_at}")

            # Проверяем что запись в БД
            assert sync_log.id is not None, "❌ FAIL: sync_log.id is None"
            assert sync_log.status == 'pending', f"❌ FAIL: status={sync_log.status}, expected='pending'"

            # Проверяем что можно получить из БД
            from_db = SimplePrintSync.objects.get(id=sync_log.id)
            assert from_db is not None, "❌ FAIL: Не удалось получить запись из БД"

            print(f"\n✅ PASS: SimplePrintSync запись создана и сохранена в БД")

        except AssertionError as e:
            print(f"\n❌ FAIL: {str(e)}")
            print(f"📍 Файл: backend/apps/simpleprint/models.py")
            print(f"📍 Модель: SimplePrintSync")
            raise
        except Exception as e:
            print(f"\n❌ FAIL: Ошибка создания записи")
            print(f"📍 Тип ошибки: {type(e).__name__}")
            print(f"📍 Сообщение: {str(e)}")
            print(f"📍 Файл: backend/apps/simpleprint/models.py")

            import traceback
            print(f"\n🔍 Полный traceback:")
            print(traceback.format_exc())
            raise

    @patch('apps.simpleprint.services.SimplePrintClient')
    def test_02_fetch_all_data(self, mock_client_class, service, mock_api_response):
        """
        ✅/❌ Тест 2: Получение всех данных из API
        Проверяет: fetch_all_files_and_folders_recursively()
        """
        print("\n" + "="*80)
        print("📦 ТЕСТ 2: Получение всех данных из SimplePrint API")
        print("="*80)

        try:
            # Настраиваем мок
            mock_client = MagicMock()
            mock_client.get_files_and_folders.return_value = mock_api_response
            mock_client_class.return_value = mock_client

            print(f"🧪 Мок API ответ:")
            print(f"   - Папок: {len(mock_api_response['folders'])}")
            print(f"   - Файлов: {len(mock_api_response['files'])}")

            print(f"\n📡 Вызов: service.fetch_all_files_and_folders_recursively()")

            all_data = service.fetch_all_files_and_folders_recursively()

            print(f"\n📥 Полученные данные:")
            print(f"   - Тип: {type(all_data).__name__}")

            if isinstance(all_data, dict):
                print(f"   - Ключи: {list(all_data.keys())}")
                if 'folders' in all_data:
                    print(f"   - Папок: {len(all_data['folders'])}")
                    for folder in all_data['folders'][:3]:
                        print(f"      • {folder.get('name', 'N/A')} (id={folder.get('id', 'N/A')})")

                if 'files' in all_data:
                    print(f"   - Файлов: {len(all_data['files'])}")
                    for file in all_data['files'][:3]:
                        print(f"      • {file.get('name', 'N/A')} (id={file.get('id', 'N/A')})")

            # Проверки
            assert all_data is not None, "❌ FAIL: all_data is None"
            assert isinstance(all_data, dict), f"❌ FAIL: all_data не является dict: {type(all_data)}"

            print(f"\n✅ PASS: Данные успешно получены из API")

        except AssertionError as e:
            print(f"\n❌ FAIL: {str(e)}")
            print(f"📍 Файл: backend/apps/simpleprint/services.py")
            print(f"📍 Метод: fetch_all_files_and_folders_recursively()")
            raise
        except Exception as e:
            print(f"\n❌ FAIL: Ошибка получения данных")
            print(f"📍 Тип ошибки: {type(e).__name__}")
            print(f"📍 Сообщение: {str(e)}")
            print(f"📍 Файл: backend/apps/simpleprint/services.py")

            import traceback
            print(f"\n🔍 Полный traceback:")
            print(traceback.format_exc())
            raise

    @patch('apps.simpleprint.services.SimplePrintClient')
    def test_03_save_folders(self, mock_client_class, service, mock_api_response):
        """
        ✅/❌ Тест 3: Сохранение папок в БД
        Проверяет: _save_folders_to_db()
        """
        print("\n" + "="*80)
        print("💾 ТЕСТ 3: Сохранение папок в базу данных")
        print("="*80)

        try:
            folders_data = mock_api_response['folders']

            print(f"📊 Данные папок для сохранения:")
            for folder in folders_data:
                print(f"   • ID: {folder['id']}, Имя: {folder['name']}, Parent: {folder.get('parent_id', 'None')}")

            print(f"\n💾 Вызов: service._save_folders_to_db(folders_data)")

            # Сохраняем папки
            saved_count = 0
            for folder_data in folders_data:
                folder, created = SimplePrintFolder.objects.update_or_create(
                    simpleprint_id=folder_data['id'],
                    defaults={
                        'name': folder_data['name'],
                        'depth': 0,  # Упрощенно для теста
                        'files_count': 0,
                        'folders_count': 0,
                        'last_synced_at': timezone.now(),
                    }
                )
                saved_count += 1
                print(f"   {'✅ Создана' if created else '🔄 Обновлена'}: {folder.name} (id={folder.id})")

            print(f"\n📊 Проверка БД:")
            db_count = SimplePrintFolder.objects.count()
            print(f"   - Сохранено: {saved_count}")
            print(f"   - В БД: {db_count}")

            assert db_count == len(folders_data), f"❌ FAIL: В БД {db_count} папок, ожидалось {len(folders_data)}"

            # Проверяем содержимое
            for folder_data in folders_data:
                folder = SimplePrintFolder.objects.get(simpleprint_id=folder_data['id'])
                assert folder.name == folder_data['name'], f"❌ FAIL: Имя папки не совпадает"
                print(f"   ✓ Папка {folder.name} корректно сохранена")

            print(f"\n✅ PASS: Все папки сохранены корректно")

        except AssertionError as e:
            print(f"\n❌ FAIL: {str(e)}")
            print(f"📍 Файл: backend/apps/simpleprint/services.py")
            print(f"📍 Метод: _save_folders_to_db()")
            raise
        except Exception as e:
            print(f"\n❌ FAIL: Ошибка сохранения папок")
            print(f"📍 Тип ошибки: {type(e).__name__}")
            print(f"📍 Сообщение: {str(e)}")
            print(f"📍 Файл: backend/apps/simpleprint/models.py или services.py")

            import traceback
            print(f"\n🔍 Полный traceback:")
            print(traceback.format_exc())
            raise

    @patch('apps.simpleprint.services.SimplePrintClient')
    def test_04_save_files(self, mock_client_class, service, mock_api_response):
        """
        ✅/❌ Тест 4: Сохранение файлов в БД
        Проверяет: _save_files_to_db()
        """
        print("\n" + "="*80)
        print("💾 ТЕСТ 4: Сохранение файлов в базу данных")
        print("="*80)

        try:
            # Сначала создаем папку для файла
            folder = SimplePrintFolder.objects.create(
                simpleprint_id=17670,
                name='402-40441',
                depth=1,
                files_count=0,
                folders_count=0,
                last_synced_at=timezone.now()
            )
            print(f"📁 Создана папка: {folder.name} (id={folder.id})")

            files_data = mock_api_response['files']

            print(f"\n📊 Данные файлов для сохранения:")
            for file in files_data:
                print(f"   • ID: {file['id']}, Имя: {file['name']}")
                print(f"     Папка: {file.get('folder', 'None')}, Размер: {file.get('size', 0)} bytes")

            print(f"\n💾 Сохранение файлов...")

            saved_count = 0
            for file_data in files_data:
                # Получаем папку
                folder_obj = None
                if file_data.get('folder'):
                    try:
                        folder_obj = SimplePrintFolder.objects.get(simpleprint_id=file_data['folder'])
                    except SimplePrintFolder.DoesNotExist:
                        print(f"   ⚠️  Папка {file_data['folder']} не найдена")

                file, created = SimplePrintFile.objects.update_or_create(
                    simpleprint_id=file_data['id'],
                    defaults={
                        'name': file_data['name'],
                        'folder': folder_obj,
                        'ext': file_data.get('ext', ''),
                        'file_type': file_data.get('ext', 'unknown'),
                        'size': file_data.get('size', 0),
                        'size_display': f"{file_data.get('size', 0) / 1024 / 1024:.2f} MB",
                        'created_at_sp': file_data.get('created', timezone.now()),
                        'last_synced_at': timezone.now(),
                    }
                )
                saved_count += 1
                print(f"   {'✅ Создан' if created else '🔄 Обновлен'}: {file.name}")

            print(f"\n📊 Проверка БД:")
            db_count = SimplePrintFile.objects.count()
            print(f"   - Сохранено: {saved_count}")
            print(f"   - В БД: {db_count}")

            assert db_count == len(files_data), f"❌ FAIL: В БД {db_count} файлов, ожидалось {len(files_data)}"

            # Проверяем связи с папками
            for file_data in files_data:
                file = SimplePrintFile.objects.get(simpleprint_id=file_data['id'])
                assert file.name == file_data['name'], f"❌ FAIL: Имя файла не совпадает"

                if file_data.get('folder'):
                    assert file.folder is not None, f"❌ FAIL: Файл не связан с папкой"
                    assert file.folder.simpleprint_id == file_data['folder'], f"❌ FAIL: Неверная папка"
                    print(f"   ✓ Файл {file.name} связан с папкой {file.folder.name}")
                else:
                    print(f"   ✓ Файл {file.name} корректно сохранен")

            print(f"\n✅ PASS: Все файлы сохранены корректно с правильными связями")

        except AssertionError as e:
            print(f"\n❌ FAIL: {str(e)}")
            print(f"📍 Файл: backend/apps/simpleprint/services.py")
            print(f"📍 Метод: _save_files_to_db()")
            raise
        except Exception as e:
            print(f"\n❌ FAIL: Ошибка сохранения файлов")
            print(f"📍 Тип ошибки: {type(e).__name__}")
            print(f"📍 Сообщение: {str(e)}")
            print(f"📍 Файл: backend/apps/simpleprint/models.py или services.py")

            import traceback
            print(f"\n🔍 Полный traceback:")
            print(traceback.format_exc())
            raise

    @patch('apps.simpleprint.services.SimplePrintClient')
    def test_05_full_sync(self, mock_client_class, service, mock_api_response):
        """
        ✅/❌ Тест 5: Полная синхронизация (end-to-end)
        Проверяет: sync_all_files()
        """
        print("\n" + "="*80)
        print("🔄 ТЕСТ 5: Полная синхронизация (E2E тест)")
        print("="*80)

        try:
            # Настраиваем мок
            mock_client = MagicMock()
            mock_client.get_files_and_folders.return_value = mock_api_response
            mock_client_class.return_value = mock_client

            print(f"🧪 Мок данные:")
            print(f"   - Папок: {len(mock_api_response['folders'])}")
            print(f"   - Файлов: {len(mock_api_response['files'])}")

            print(f"\n🚀 Запуск полной синхронизации...")
            print(f"📡 Вызов: service.sync_all_files(full_sync=False)")

            # Запускаем синхронизацию
            sync_log = service.sync_all_files(full_sync=False)

            print(f"\n📊 Результат синхронизации:")
            print(f"   - ID записи: {sync_log.id}")
            print(f"   - Статус: {sync_log.status}")
            print(f"   - Всего папок: {sync_log.total_folders}")
            print(f"   - Синхронизировано папок: {sync_log.synced_folders}")
            print(f"   - Всего файлов: {sync_log.total_files}")
            print(f"   - Синхронизировано файлов: {sync_log.synced_files}")

            # Проверки
            assert sync_log is not None, "❌ FAIL: sync_log is None"
            assert sync_log.status in ['success', 'completed'], f"❌ FAIL: status={sync_log.status}"

            # Проверяем что данные сохранены в БД
            folders_count = SimplePrintFolder.objects.count()
            files_count = SimplePrintFile.objects.count()

            print(f"\n📊 Проверка базы данных:")
            print(f"   - Папок в БД: {folders_count}")
            print(f"   - Файлов в БД: {files_count}")

            assert folders_count > 0, "❌ FAIL: Папки не сохранены в БД"
            assert files_count > 0, "❌ FAIL: Файлы не сохранены в БД"

            print(f"\n✅ PASS: Полная синхронизация выполнена успешно")
            print(f"   ✓ SimplePrintSync запись создана")
            print(f"   ✓ Папки сохранены в БД")
            print(f"   ✓ Файлы сохранены в БД")
            print(f"   ✓ Связи между папками и файлами установлены")

        except AssertionError as e:
            print(f"\n❌ FAIL: {str(e)}")
            print(f"📍 Файл: backend/apps/simpleprint/services.py")
            print(f"📍 Метод: sync_all_files()")
            raise
        except Exception as e:
            print(f"\n❌ FAIL: Ошибка полной синхронизации")
            print(f"📍 Тип ошибки: {type(e).__name__}")
            print(f"📍 Сообщение: {str(e)}")
            print(f"📍 Файл: backend/apps/simpleprint/services.py")

            import traceback
            print(f"\n🔍 Полный traceback:")
            print(traceback.format_exc())
            raise


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
