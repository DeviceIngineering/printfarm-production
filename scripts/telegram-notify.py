#!/usr/bin/env python3
"""
Скрипт уведомлений в Telegram о статусе развертывания
"""

import json
import requests
import sys
import os
import argparse
from datetime import datetime

# Конфигурация Telegram (заполните эти значения)
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')

def send_telegram_message(message, parse_mode='Markdown'):
    """Отправляет сообщение в Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram bot token или chat_id не настроены")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    data = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': parse_mode,
        'disable_web_page_preview': True
    }
    
    try:
        response = requests.post(url, data=data, timeout=10)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"Ошибка отправки в Telegram: {e}")
        return False

def get_deployment_status():
    """Получает статус последнего развертывания"""
    status_file = '/opt/printfarm/logs/last_deployment.json'
    
    if not os.path.exists(status_file):
        return None
    
    try:
        with open(status_file, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None

def format_deployment_message(status_data, message_type='status'):
    """Форматирует сообщение о развертывании"""
    if not status_data:
        return "❓ Статус развертывания недоступен"
    
    status = status_data.get('status', 'unknown')
    branch = status_data.get('branch', 'unknown')
    commit = status_data.get('commit', 'unknown')[:8]
    timestamp = status_data.get('timestamp', '')
    
    # Форматируем время
    try:
        if timestamp:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            time_str = dt.strftime('%d.%m.%Y %H:%M:%S')
        else:
            time_str = 'неизвестно'
    except:
        time_str = timestamp
    
    if status == 'success':
        icon = "✅"
        status_text = "Успешно"
    elif status == 'failed':
        icon = "❌"
        status_text = "Ошибка"
    else:
        icon = "⚠️"
        status_text = "Неизвестно"
    
    message = f"{icon} *PrintFarm Развертывание*\n\n"
    message += f"*Статус:* {status_text}\n"
    message += f"*Ветка:* `{branch}`\n"
    message += f"*Коммит:* `{commit}`\n"
    message += f"*Время:* {time_str}\n"
    
    if 'duration' in status_data:
        duration = status_data['duration']
        message += f"*Длительность:* {duration:.1f} сек\n"
    
    if status == 'failed' and 'error' in status_data:
        error = status_data['error'][:200]  # Обрезаем длинные ошибки
        message += f"\n*Ошибка:*\n```\n{error}\n```"
    
    return message

def get_server_status():
    """Получает общий статус сервера"""
    try:
        # Проверяем webhook сервис
        webhook_status = os.system('systemctl is-active --quiet printfarm-webhook.service') == 0
        
        # Проверяем Docker контейнеры (если есть)
        docker_status = "unknown"
        if os.path.exists('/opt/printfarm/docker-compose.prod.yml'):
            result = os.system('cd /opt/printfarm && docker-compose -f docker-compose.prod.yml ps | grep -q Up')
            docker_status = "running" if result == 0 else "stopped"
        
        return {
            'webhook': 'active' if webhook_status else 'inactive',
            'docker': docker_status
        }
    except:
        return {'webhook': 'unknown', 'docker': 'unknown'}

def format_status_message():
    """Форматирует сообщение о статусе сервера"""
    server_status = get_server_status()
    deployment_status = get_deployment_status()
    
    message = "📊 *PrintFarm Статус Сервера*\n\n"
    
    # Статус сервисов
    webhook_icon = "✅" if server_status['webhook'] == 'active' else "❌"
    message += f"{webhook_icon} *Webhook:* {server_status['webhook']}\n"
    
    docker_icon = "✅" if server_status['docker'] == 'running' else "❌" if server_status['docker'] == 'stopped' else "❓"
    message += f"{docker_icon} *Docker:* {server_status['docker']}\n"
    
    # Последнее развертывание
    if deployment_status:
        status = deployment_status.get('status', 'unknown')
        timestamp = deployment_status.get('timestamp', '')
        
        try:
            if timestamp:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                time_str = dt.strftime('%d.%m.%Y %H:%M:%S')
            else:
                time_str = 'неизвестно'
        except:
            time_str = timestamp
        
        deploy_icon = "✅" if status == 'success' else "❌" if status == 'failed' else "❓"
        message += f"\n{deploy_icon} *Последний деплой:* {status}\n"
        message += f"📅 *Время:* {time_str}"
    else:
        message += "\n❓ *Последний деплой:* данных нет"
    
    return message

def main():
    parser = argparse.ArgumentParser(description='Отправка уведомлений о развертывании в Telegram')
    parser.add_argument('action', choices=['deploy', 'status', 'test'], 
                       help='Тип уведомления')
    parser.add_argument('--message', help='Произвольное сообщение')
    
    args = parser.parse_args()
    
    # Проверяем конфигурацию
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Настройте переменные окружения TELEGRAM_BOT_TOKEN и TELEGRAM_CHAT_ID")
        return 1
    
    if args.action == 'test':
        message = args.message if args.message else "🧪 Тестовое сообщение от PrintFarm"
        if send_telegram_message(message):
            print("Тестовое сообщение отправлено успешно")
            return 0
        else:
            print("Ошибка отправки тестового сообщения")
            return 1
    
    elif args.action == 'deploy':
        deployment_status = get_deployment_status()
        message = format_deployment_message(deployment_status)
        
        if send_telegram_message(message):
            print("Уведомление о развертывании отправлено")
            return 0
        else:
            print("Ошибка отправки уведомления")
            return 1
    
    elif args.action == 'status':
        message = format_status_message()
        
        if send_telegram_message(message):
            print("Статус сервера отправлен")
            return 0
        else:
            print("Ошибка отправки статуса")
            return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())