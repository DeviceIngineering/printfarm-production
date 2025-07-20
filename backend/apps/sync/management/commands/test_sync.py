"""
Django management command to test МойСклад synchronization.
"""
from django.core.management.base import BaseCommand
from apps.sync.services import SyncService
from apps.sync.moysklad_client import MoySkladClient


class Command(BaseCommand):
    help = 'Test synchronization with МойСклад'

    def add_arguments(self, parser):
        parser.add_argument(
            '--warehouse-id',
            type=str,
            help='Warehouse ID for sync',
            default='241ed919-a631-11ee-0a80-07a9000bb947'
        )
        parser.add_argument(
            '--test-connection',
            action='store_true',
            help='Only test connection'
        )
        parser.add_argument(
            '--test-stock',
            action='store_true',
            help='Test stock report API'
        )

    def handle(self, *args, **options):
        client = MoySkladClient()
        
        if options['test_connection']:
            self.stdout.write('Testing connection to МойСклад...')
            try:
                if client.test_connection():
                    self.stdout.write(self.style.SUCCESS('Connection successful!'))
                else:
                    self.stdout.write(self.style.ERROR('Connection failed!'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Connection error: {str(e)}'))
            return
        
        if options['test_stock']:
            warehouse_id = options['warehouse_id']
            self.stdout.write(f'Testing stock report for warehouse {warehouse_id}...')
            try:
                stock_data = client.get_stock_report(warehouse_id)
                self.stdout.write(self.style.SUCCESS(f'Stock report retrieved: {len(stock_data)} items'))
                
                # Show first item with full structure
                if stock_data:
                    import json
                    self.stdout.write("Full structure of first item:")
                    self.stdout.write(json.dumps(stock_data[0], indent=2, ensure_ascii=False))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Stock report error: {str(e)}'))
            return
        
        # Full sync test
        warehouse_id = options['warehouse_id']
        self.stdout.write(f'Starting sync test for warehouse {warehouse_id}...')
        
        try:
            service = SyncService()
            sync_log = service.sync_products(warehouse_id, sync_type='manual')
            
            self.stdout.write(self.style.SUCCESS(
                f'Sync completed!\n'
                f'  Status: {sync_log.status}\n'
                f'  Total products: {sync_log.total_products}\n'
                f'  Synced: {sync_log.synced_products}\n'
                f'  Failed: {sync_log.failed_products}\n'
                f'  Duration: {sync_log.duration}'
            ))
            
            if sync_log.error_details:
                self.stdout.write(self.style.WARNING(f'Error details: {sync_log.error_details}'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Sync failed: {str(e)}'))