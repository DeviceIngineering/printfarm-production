#!/usr/bin/env python3
"""
Test settings API locally
"""
import requests
import json
import sys

API_BASE = 'http://localhost:8000/api/v1'

def test_endpoint(endpoint, method='GET', data=None):
    """Test an API endpoint"""
    url = f"{API_BASE}{endpoint}"
    
    try:
        if method == 'GET':
            response = requests.get(url, timeout=5)
        elif method == 'POST':
            response = requests.post(url, json=data or {}, timeout=5)
        elif method == 'PUT':
            response = requests.put(url, json=data or {}, timeout=5)
        
        print(f"\n{'='*60}")
        print(f"{method} {endpoint}")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print("✅ Success:")
                print(json.dumps(result, indent=2, ensure_ascii=False))
            except:
                print("✅ Success (non-JSON response)")
                print(response.text[:500])
        else:
            print("❌ Error:")
            print(response.text[:500])
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection failed to {url}")
        print("Is the Django server running? Try: python manage.py runserver")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    print("🔧 Testing PrintFarm Settings API")
    print("Make sure Django server is running: python manage.py runserver")
    
    # Test basic endpoints
    test_endpoint('/products/')  # Check if basic API works
    
    # Test settings endpoints
    test_endpoint('/settings/system-info/')
    test_endpoint('/settings/summary/')
    test_endpoint('/settings/sync/')
    test_endpoint('/settings/general/')
    
    # Test connection
    test_endpoint('/settings/sync/test-connection/', 'POST')
    
    print("\n" + "="*60)
    print("🌐 Open test_settings_frontend.html in browser for interactive testing")

if __name__ == '__main__':
    main()