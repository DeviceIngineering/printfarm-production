#!/usr/bin/env python3
import os
import django
import sys
import json

# Setup Django
sys.path.append('/Users/dim11/Documents/myProjects/Factory_v2/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.test import Client
from rest_framework.authtoken.models import Token

# Create client
client = Client()

# Get token
token_key = '549ebaf641ffa608a26b79a21d72a296c99a02b7'
token = Token.objects.get(key=token_key)

print(f"Testing API with token for user: {token.user.username}")
print("=" * 50)

# Test products endpoint
print("1. Testing /api/v1/products/")
response = client.get(
    '/api/v1/products/',
    HTTP_AUTHORIZATION=f'Token {token_key}',
    HTTP_ACCEPT='application/json'
)

print(f"Status Code: {response.status_code}")
print(f"Content-Type: {response.get('Content-Type', 'Not set')}")

if response.status_code == 200:
    try:
        data = response.json()
        if isinstance(data, dict) and 'results' in data:
            print(f"Total products: {data.get('count', 0)}")
            print(f"Products in this page: {len(data['results'])}")
            if data['results']:
                print("First product:")
                print(json.dumps(data['results'][0], indent=2, ensure_ascii=False))
        elif isinstance(data, list):
            print(f"Products returned: {len(data)}")
            if data:
                print("First product:")
                print(json.dumps(data[0], indent=2, ensure_ascii=False))
    except json.JSONDecodeError:
        print(f"Response content: {response.content.decode()[:500]}")
else:
    print(f"Error content: {response.content.decode()}")

print("\n" + "=" * 50)

# Test stats endpoint
print("2. Testing /api/v1/products/stats/")
response = client.get(
    '/api/v1/products/stats/',
    HTTP_AUTHORIZATION=f'Token {token_key}',
    HTTP_ACCEPT='application/json'
)

print(f"Status Code: {response.status_code}")

if response.status_code == 200:
    try:
        data = response.json()
        print("Stats:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except json.JSONDecodeError:
        print(f"Response content: {response.content.decode()}")
else:
    print(f"Error content: {response.content.decode()}")

print("\n" + "=" * 50)

# Test available URLs
print("3. Testing URL patterns")
from django.urls import get_resolver
from django.conf import settings

resolver = get_resolver()

def collect_urls(urlpatterns, prefix=''):
    urls = []
    for pattern in urlpatterns:
        if hasattr(pattern, 'url_patterns'):
            urls.extend(collect_urls(pattern.url_patterns, prefix + str(pattern.pattern)))
        else:
            urls.append(prefix + str(pattern.pattern))
    return urls

all_urls = collect_urls(resolver.url_patterns)
api_urls = [url for url in all_urls if 'api/v1' in url and 'product' in url]
print("Available product API URLs:")
for url in api_urls:
    print(f"  {url}")