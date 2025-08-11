from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

def warehouses(request):
    return JsonResponse([
        {"id": "241ed919-a631-11ee-0a80-07a9000bb947", "name": "Основной склад"},
        {"id": "test-warehouse", "name": "Тестовый склад"}
    ], safe=False)

def groups(request):
    return JsonResponse([
        {"id": "group-1", "name": "Группа 1"},
        {"id": "group-2", "name": "Группа 2"}
    ], safe=False)

def status(request):
    return JsonResponse({"status": "ready", "is_running": False})

def products(request):
    return JsonResponse({"results": [], "count": 0})

def stats(request):
    return JsonResponse({"total": 0, "new": 0, "old": 0})

@csrf_exempt
def sync_start(request):
    return JsonResponse({
        "status": "started",
        "sync_id": "test-sync-123",
        "message": "Синхронизация запущена"
    })

@csrf_exempt
def settings_endpoint(request):
    if request.method == "GET":
        return JsonResponse({
            "moysklad_token": "f9be4985f5e3488716c040ca52b8e04c7c0f9e0b",
            "default_warehouse": "241ed919-a631-11ee-0a80-07a9000bb947",
            "sync_interval": 24,
            "auto_sync_enabled": False,
            "notification_enabled": True,
            "email_notifications": False,
            "backup_enabled": True,
            "debug_mode": False
        })
    elif request.method == "POST":
        return JsonResponse({
            "status": "success",
            "message": "Настройки сохранены успешно"
        })

@csrf_exempt
def settings_summary(request):
    return JsonResponse({
        "total_products": 0,
        "last_sync": None,
        "sync_status": "ready",
        "warehouse_count": 2,
        "groups_count": 2,
        "last_sync_duration": None,
        "sync_errors": 0,
        "system_status": "online"
    })