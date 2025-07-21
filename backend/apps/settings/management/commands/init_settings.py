from django.core.management.base import BaseCommand
from apps.settings.models import SystemInfo, SyncScheduleSettings, GeneralSettings
from django.conf import settings


class Command(BaseCommand):
    help = 'Initialize default settings for the PrintFarm system'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset all settings to defaults',
        )
        
        parser.add_argument(
            '--warehouse-id',
            type=str,
            help='Default warehouse ID for sync',
            default=None
        )
    
    def handle(self, *args, **options):
        reset = options['reset']
        warehouse_id = options['warehouse_id']
        
        # Initialize SystemInfo (singleton)
        try:
            if reset:
                SystemInfo.objects.all().delete()
            
            system_info = SystemInfo.get_instance()
            self.stdout.write(
                self.style.SUCCESS(f'✅ System info initialized (Version: {system_info.version})')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error initializing system info: {e}')
            )
        
        # Initialize SyncScheduleSettings
        try:
            if reset:
                SyncScheduleSettings.objects.all().delete()
            
            sync_settings = SyncScheduleSettings.get_instance()
            
            # Set warehouse ID if provided
            if warehouse_id:
                sync_settings.warehouse_id = warehouse_id
                sync_settings.save()
                self.stdout.write(f'📦 Warehouse ID set to: {warehouse_id}')
            elif not sync_settings.warehouse_id:
                # Try to use default from settings
                default_warehouse = getattr(settings, 'MOYSKLAD_CONFIG', {}).get('default_warehouse_id')
                if default_warehouse:
                    sync_settings.warehouse_id = default_warehouse
                    sync_settings.save()
                    self.stdout.write(f'📦 Warehouse ID set to default: {default_warehouse}')
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Sync settings initialized (Interval: {sync_settings.sync_interval_display})')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error initializing sync settings: {e}')
            )
        
        # Initialize GeneralSettings
        try:
            if reset:
                GeneralSettings.objects.all().delete()
            
            general_settings = GeneralSettings.get_instance()
            self.stdout.write(
                self.style.SUCCESS(f'✅ General settings initialized')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error initializing general settings: {e}')
            )
        
        # Show current settings summary
        self.stdout.write('\n' + self.style.HTTP_INFO('📊 Current Settings Summary:'))
        
        try:
            system_info = SystemInfo.get_instance()
            sync_settings = SyncScheduleSettings.get_instance()
            general_settings = GeneralSettings.get_instance()
            
            self.stdout.write(f'🔧 System Version: {system_info.version}')
            self.stdout.write(f'📅 Build Date: {system_info.build_date}')
            self.stdout.write(f'🔄 Sync Enabled: {"Yes" if sync_settings.sync_enabled else "No"}')
            self.stdout.write(f'⏱️  Sync Interval: {sync_settings.sync_interval_display}')
            self.stdout.write(f'📦 Warehouse ID: {sync_settings.warehouse_id or "Not set"}')
            self.stdout.write(f'🏭 Default Stock: {general_settings.default_new_product_stock}')
            self.stdout.write(f'📋 Products per page: {general_settings.products_per_page}')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error showing summary: {e}')
            )
        
        self.stdout.write('\n' + self.style.SUCCESS('🎉 Settings initialization completed!'))
        
        # Show next steps
        self.stdout.write('\n' + self.style.WARNING('📝 Next Steps:'))
        self.stdout.write('1. Set warehouse ID: python manage.py init_settings --warehouse-id YOUR_ID')
        self.stdout.write('2. Configure excluded groups via Admin or API')
        self.stdout.write('3. Test sync connection: curl -X POST http://localhost:8000/api/v1/settings/sync/test-connection/')
        self.stdout.write('4. Access settings API: http://localhost:8000/api/v1/settings/summary/')