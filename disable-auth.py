#!/usr/bin/env python3
"""
Временный скрипт для отключения аутентификации в development режиме
"""
import os
import re

def disable_auth_in_file(filepath):
    """Отключает permission_classes в файле"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Паттерны для замены
    patterns = [
        # Для классов
        (r'(\s+)permission_classes = \[IsAuthenticated\]', r'\1# permission_classes = [IsAuthenticated]  # Временно отключено'),
        # Для декораторов
        (r'^@permission_classes\(\[IsAuthenticated\]\)', r'# @permission_classes([IsAuthenticated])  # Временно отключено'),
    ]
    
    modified = False
    for pattern, replacement in patterns:
        new_content, count = re.subn(pattern, replacement, content, flags=re.MULTILINE)
        if count > 0:
            content = new_content
            modified = True
    
    if modified:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"✅ Modified: {filepath}")
        return True
    return False

def main():
    # Список файлов для проверки
    files_to_check = [
        'backend/apps/products/views.py',
        'backend/apps/sync/views.py',
        'backend/apps/reports/views.py',
    ]
    
    modified_count = 0
    for filepath in files_to_check:
        if os.path.exists(filepath):
            if disable_auth_in_file(filepath):
                modified_count += 1
        else:
            print(f"⚠️  File not found: {filepath}")
    
    print(f"\n📝 Total files modified: {modified_count}")

if __name__ == '__main__':
    main()