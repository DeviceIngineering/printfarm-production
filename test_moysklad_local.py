#!/usr/bin/env python3

"""
Test script to debug MoySklad API connectivity in local environment.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
sys.path.insert(0, '/Users/dim11/Documents/myProjects/Factory_v2/backend')

django.setup()

from django.conf import settings

def test_moysklad_config():
    """Test MoySklad configuration."""
    print("=== MoySklad Configuration Test ===")
    
    try:
        config = settings.MOYSKLAD_CONFIG
        print(f"✅ Base URL: {config['base_url']}")
        print(f"✅ Token: {config['token'][:20]}...")  # Show only first 20 chars
        print(f"✅ Default Warehouse: {config['default_warehouse_id']}")
        print(f"✅ Rate Limit: {config['rate_limit']} req/sec")
        return True
    except Exception as e:
        print(f"❌ Configuration Error: {e}")
        return False

def test_moysklad_client():
    """Test MoySklad client initialization."""
    print("\n=== MoySklad Client Test ===")
    
    try:
        from apps.sync.moysklad_client import MoySkladClient
        client = MoySkladClient()
        print("✅ Client initialized successfully")
        return client
    except Exception as e:
        print(f"❌ Client Initialization Error: {e}")
        return None

def test_warehouses_api(client):
    """Test warehouses API."""
    print("\n=== Warehouses API Test ===")
    
    if not client:
        print("❌ No client available")
        return False
    
    try:
        warehouses = client.get_warehouses()
        print(f"✅ Warehouses retrieved: {len(warehouses)} found")
        
        for i, warehouse in enumerate(warehouses[:3]):  # Show first 3
            print(f"  {i+1}. {warehouse.get('name', 'N/A')} (ID: {warehouse.get('id', 'N/A')})")
        
        return True
    except Exception as e:
        print(f"❌ Warehouses API Error: {e}")
        return False

def test_product_groups_api(client):
    """Test product groups API."""
    print("\n=== Product Groups API Test ===")
    
    if not client:
        print("❌ No client available")
        return False
    
    try:
        groups = client.get_product_groups()
        print(f"✅ Product groups retrieved: {len(groups)} found")
        
        for i, group in enumerate(groups[:3]):  # Show first 3
            print(f"  {i+1}. {group.get('name', 'N/A')} (ID: {group.get('id', 'N/A')})")
        
        return True
    except Exception as e:
        print(f"❌ Product Groups API Error: {e}")
        return False

def test_api_endpoints():
    """Test API endpoints directly."""
    print("\n=== API Endpoints Test ===")
    
    try:
        import requests
        
        # Test warehouses endpoint
        url = "http://localhost:8000/api/v1/sync/warehouses/"
        print(f"Testing: {url}")
        
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Warehouses endpoint works: {len(data)} warehouses")
        else:
            print(f"❌ Warehouses endpoint error: {response.text}")
        
        # Test product groups endpoint
        url = "http://localhost:8000/api/v1/sync/product-groups/"
        print(f"\nTesting: {url}")
        
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Product groups endpoint works: {len(data)} groups")
        else:
            print(f"❌ Product groups endpoint error: {response.text}")
            
    except Exception as e:
        print(f"❌ API Endpoints Error: {e}")

def main():
    """Main test function."""
    print("🧪 MoySklad Local Environment Debug Tool")
    print("=" * 50)
    
    # Test configuration
    config_ok = test_moysklad_config()
    if not config_ok:
        print("\n❌ Configuration failed. Check your .env file.")
        return
    
    # Test client
    client = test_moysklad_client()
    
    # Test APIs
    test_warehouses_api(client)
    test_product_groups_api(client)
    
    # Test endpoints (requires server to be running)
    print("\n" + "=" * 50)
    print("🌐 Testing API endpoints (make sure server is running):")
    test_api_endpoints()
    
    print("\n" + "=" * 50)
    print("🏁 Debug complete!")
    print("\nIf you see errors:")
    print("1. Check that your .env file has correct MOYSKLAD_TOKEN")
    print("2. Make sure Django server is running: python3 manage.py runserver")
    print("3. Check your internet connection")
    print("4. Verify MoySklad API token permissions")

if __name__ == "__main__":
    main()