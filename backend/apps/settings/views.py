from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import SystemInfo, SyncScheduleSettings, GeneralSettings
from .serializers import (
    SystemInfoSerializer, 
    SyncScheduleSettingsSerializer, 
    GeneralSettingsSerializer,
    SettingsSummarySerializer
)
from .services import SettingsService, ScheduleManager
from apps.sync.moysklad_client import MoySkladClient


@api_view(['GET'])
@permission_classes([AllowAny])
def system_info(request):
    """Получить информацию о системе"""
    try:
        info = SystemInfo.get_instance()
        serializer = SystemInfoSerializer(info)
        return Response(serializer.data)
    except Exception as e:
        return Response(
            {'error': f'Ошибка получения системной информации: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET', 'PUT'])
@permission_classes([AllowAny])
def sync_settings(request):
    """Управление настройками синхронизации"""
    
    if request.method == 'GET':
        try:
            settings = SyncScheduleSettings.get_instance()
            serializer = SyncScheduleSettingsSerializer(settings)
            
            # Добавляем информацию о статусе расписания
            data = serializer.data
            schedule_status = SettingsService.get_sync_schedule_status()
            data['schedule_status'] = schedule_status
            
            return Response(data)
        except Exception as e:
            return Response(
                {'error': f'Ошибка получения настроек: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    elif request.method == 'PUT':
        try:
            settings = SyncScheduleSettings.get_instance()
            serializer = SyncScheduleSettingsSerializer(settings, data=request.data, partial=True)
            
            if serializer.is_valid():
                settings = serializer.save()
                
                # Обновляем расписание в Celery Beat
                result = SettingsService.update_sync_schedule(settings)
                
                response_data = serializer.data
                response_data['schedule_update'] = result
                
                return Response(response_data)
            else:
                return Response(
                    {'error': 'Некорректные данные', 'details': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            return Response(
                {'error': f'Ошибка обновления настроек: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['GET', 'PUT'])
@permission_classes([AllowAny])
def general_settings(request):
    """Управление общими настройками"""
    
    if request.method == 'GET':
        try:
            settings = GeneralSettings.get_instance()
            serializer = GeneralSettingsSerializer(settings)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': f'Ошибка получения настроек: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    elif request.method == 'PUT':
        try:
            settings = GeneralSettings.get_instance()
            serializer = GeneralSettingsSerializer(settings, data=request.data, partial=True)
            
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            else:
                return Response(
                    {'error': 'Некорректные данные', 'details': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            return Response(
                {'error': f'Ошибка обновления настроек: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['GET'])
@permission_classes([AllowAny])
def settings_summary(request):
    """Получить сводную информацию о всех настройках"""
    try:
        summary = SettingsService.get_system_summary()
        serializer = SettingsSummarySerializer(summary)
        return Response(serializer.data)
    except Exception as e:
        return Response(
            {'error': f'Ошибка получения сводной информации: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def test_sync_connection(request):
    """Тестировать подключение к МойСклад"""
    try:
        result = SettingsService.test_sync_connection()
        return Response(result)
    except Exception as e:
        return Response(
            {'success': False, 'message': f'Ошибка тестирования: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def trigger_manual_sync(request):
    """Запустить ручную синхронизацию"""
    try:
        warehouse_id = request.data.get('warehouse_id')
        excluded_groups = request.data.get('excluded_groups', [])
        
        result = SettingsService.trigger_manual_sync(warehouse_id, excluded_groups)
        
        if result['success']:
            return Response(result)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        return Response(
            {'success': False, 'message': f'Ошибка запуска синхронизации: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def schedule_status(request):
    """Получить статус расписания задач"""
    try:
        status_data = SettingsService.get_sync_schedule_status()
        return Response(status_data)
    except Exception as e:
        return Response(
            {'error': f'Ошибка получения статуса расписания: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def update_schedule(request):
    """Обновить расписание синхронизации"""
    try:
        interval_minutes = request.data.get('interval_minutes', 60)
        enabled = request.data.get('enabled', True)
        
        # Валидация интервала
        if interval_minutes % 30 != 0:
            return Response(
                {'error': 'Интервал должен быть кратен 30 минутам'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if interval_minutes < 30 or interval_minutes > 1440:
            return Response(
                {'error': 'Интервал должен быть от 30 минут до 24 часов'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Обновляем расписание
        if enabled:
            task = ScheduleManager.create_or_update_sync_schedule(interval_minutes, enabled)
            message = f'Расписание обновлено: каждые {interval_minutes} минут'
        else:
            ScheduleManager.disable_sync_schedule()
            message = 'Расписание отключено'
        
        # Обновляем настройки
        settings = SyncScheduleSettings.get_instance()
        settings.sync_enabled = enabled
        settings.sync_interval_minutes = interval_minutes
        settings.save()
        
        return Response({
            'success': True,
            'message': message,
            'interval_minutes': interval_minutes,
            'enabled': enabled
        })
        
    except Exception as e:
        return Response(
            {'success': False, 'message': f'Ошибка обновления расписания: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def get_warehouses(request):
    """Получить список складов из МойСклад"""
    try:
        client = MoySkladClient()
        warehouses = client.get_warehouses()
        
        # Преобразуем в удобный формат для фронтенда
        formatted_warehouses = []
        for warehouse in warehouses:
            formatted_warehouses.append({
                'id': warehouse.get('id'),
                'name': warehouse.get('name', 'Без названия'),
                'description': warehouse.get('description', ''),
                'archived': warehouse.get('archived', False)
            })
        
        # Фильтруем архивированные склады
        active_warehouses = [w for w in formatted_warehouses if not w['archived']]
        
        return Response({
            'warehouses': active_warehouses,
            'total': len(active_warehouses)
        })
        
    except Exception as e:
        return Response(
            {'error': f'Ошибка получения списка складов: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def get_product_groups(request):
    """Получить список групп товаров из МойСклад"""
    try:
        client = MoySkladClient()
        product_groups = client.get_product_groups()
        
        # Преобразуем в удобный формат для фронтенда
        formatted_groups = []
        for group in product_groups:
            formatted_groups.append({
                'id': group.get('id'),
                'name': group.get('name', 'Без названия'),
                'pathName': group.get('pathName', ''),
                'archived': group.get('archived', False),
                'parent': group.get('parent')
            })
        
        # Фильтруем архивированные группы
        active_groups = [g for g in formatted_groups if not g['archived']]
        
        return Response({
            'product_groups': active_groups,
            'total': len(active_groups)
        })
        
    except Exception as e:
        return Response(
            {'error': f'Ошибка получения списка групп товаров: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )