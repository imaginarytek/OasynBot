#!/usr/bin/env python3
"""
Test Telegram Alerts
"""

import asyncio
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.alerts.telegram import TelegramAlerter
from dotenv import load_dotenv

load_dotenv()

async def main():
    print("Testing Telegram Alerts...")
    
    config = {
        'bot_token': os.getenv('TELEGRAM_BOT_TOKEN'),
        'chat_id': os.getenv('TELEGRAM_CHAT_ID')
    }
    
    alerter = TelegramAlerter(config)
    
    if not alerter.enabled:
        print("❌ Alerts disabled! Check TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env")
        return

    # Test Trade Alert
    trade = {
        'symbol': 'BTC-PERP',
        'side': 'buy',
        'price': 69420.00,
        'quantity': 0.1,
        'confidence': 0.95,
        'timestamp': '2024-05-20 16:20:00'
    }
    
    print(f"Sending test alert to chat {config['chat_id']}...")
    result = await alerter.send_trade_alert(trade)
    
    # We can't easily check return value here since send_trade_alert returns None
    # But logs would show success/failure
    print("Done! Check your Telegram.")

if __name__ == "__main__":
    asyncio.run(main())
