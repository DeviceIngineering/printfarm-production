#!/usr/bin/env python3
import os
import django
import sys

# Setup Django
sys.path.append('/Users/dim11/Documents/myProjects/Factory_v2/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from rest_framework.authtoken.models import Token

token_key = '549ebaf641ffa608a26b79a21d72a296c99a02b7'

try:
    token = Token.objects.get(key=token_key)
    print(f'Token exists for user: {token.user.username}')
except Token.DoesNotExist:
    print('Frontend token not found - creating...')
    from django.contrib.auth.models import User
    
    # Create or get admin user
    user, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@printfarm.local',
            'is_staff': True,
            'is_superuser': True
        }
    )
    
    if created:
        user.set_password('admin')
        user.save()
    
    # Create the specific token
    token = Token.objects.create(user=user, key=token_key)
    print(f'Created token for user: {user.username}')