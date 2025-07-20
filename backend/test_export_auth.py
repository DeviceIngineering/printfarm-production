#!/usr/bin/env python3
"""
Test Excel export with authentication.
"""
import os
import sys
import django
import requests

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User

# Get or create a test user and token
user, created = User.objects.get_or_create(username='testuser')
if created:
    user.set_password('testpass123')
    user.save()

token, created = Token.objects.get_or_create(user=user)
print(f"Test token: {token.key}")

# Test the new export endpoint with query parameter authentication
base_url = 'http://localhost:8000'

# Test 1: Products export with query parameter auth
print("\n🧪 Testing products export with query parameter auth...")
try:
    response = requests.get(
        f'{base_url}/api/v1/reports/export/products/',
        params={'auth_token': token.key},
        timeout=30
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"✅ Export successful! Content-Type: {response.headers.get('Content-Type')}")
        print(f"Content-Disposition: {response.headers.get('Content-Disposition')}")
        print(f"Content length: {len(response.content)} bytes")
    else:
        print(f"❌ Export failed: {response.text}")
except Exception as e:
    print(f"❌ Request failed: {e}")

# Test 2: Production list export
print("\n🧪 Testing production list export...")
try:
    response = requests.get(
        f'{base_url}/api/v1/reports/export/production-list/',
        params={'auth_token': token.key},
        timeout=30
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"✅ Export successful! Content-Type: {response.headers.get('Content-Type')}")
        print(f"Content-Disposition: {response.headers.get('Content-Disposition')}")
        print(f"Content length: {len(response.content)} bytes")
    else:
        print(f"❌ Export failed: {response.text}")
except Exception as e:
    print(f"❌ Request failed: {e}")

# Test 3: Without authentication (should fail)
print("\n🧪 Testing without authentication (should fail)...")
try:
    response = requests.get(
        f'{base_url}/api/v1/reports/export/products/',
        timeout=30
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 401:
        print("✅ Correctly rejected unauthenticated request")
    else:
        print(f"❌ Unexpected response: {response.text}")
except Exception as e:
    print(f"❌ Request failed: {e}")

print("\n✨ Test completed!")