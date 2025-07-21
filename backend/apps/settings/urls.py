from django.urls import path
from . import views

urlpatterns = [
    # Системная информация
    path('system-info/', views.system_info, name='system-info'),
    
    # Настройки синхронизации
    path('sync/', views.sync_settings, name='sync-settings'),
    path('sync/test-connection/', views.test_sync_connection, name='test-sync-connection'),
    path('sync/trigger-manual/', views.trigger_manual_sync, name='trigger-manual-sync'),
    
    # Общие настройки
    path('general/', views.general_settings, name='general-settings'),
    
    # Сводная информация
    path('summary/', views.settings_summary, name='settings-summary'),
    
    # Управление расписанием
    path('schedule/status/', views.schedule_status, name='schedule-status'),
    path('schedule/update/', views.update_schedule, name='update-schedule'),
]