"""
Telegram Alerter

Sends notifications to a Telegram chat via bot API.
"""

import os
import logging
import asyncio
import aiohttp
from typing import Optional

class TelegramAlerter:
    """
    Sends alerts to Telegram.
    
    Requires TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in environment variables.
    """
    
    def __init__(self, config: dict = None):
        self.logger = logging.getLogger("hedgemony.alerts.telegram")
        self.config = config or {}
        
        self.bot_token = self.config.get("bot_token") or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = self.config.get("chat_id") or os.getenv("TELEGRAM_CHAT_ID")
        self.enabled = bool(self.bot_token and self.chat_id)
        
        if not self.enabled:
            self.logger.warning("Telegram alerts disabled (missing token or chat_id)")
        else:
            self.logger.info("Telegram alerts enabled")
            
    async def send_message(self, message: str) -> bool:
        """Send a text message to the configured chat."""
        if not self.enabled:
            return False
            
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        self.logger.debug("Telegram message sent")
                        return True
                    else:
                        err = await response.text()
                        self.logger.error(f"Failed to send Telegram message: {err}")
                        return False
        except Exception as e:
            self.logger.error(f"Error sending Telegram message: {e}")
            return False

    async def send_trade_alert(self, trade: dict):
        """
        Send a formatted alert for a trade execution.
        
        Args:
            trade: Dict containing trade details (symbol, side, price, quantity, etc.)
        """
        if not self.enabled:
            return

        emoji = "🟢" if trade.get('side', '').lower() == 'buy' else "🔴"
        side = trade.get('side', 'UNKNOWN').upper()
        symbol = trade.get('symbol', 'UNKNOWN')
        price = trade.get('price', 0)
        qty = trade.get('quantity', 0)
        value = price * qty
        confidence = trade.get('confidence', 0)
        
        message = (
            f"{emoji} **RISING EDGE DETECTED** {emoji}\n\n"
            f"**Action:** {side} {symbol}\n"
            f"**Price:** ${price:,.2f}\n"
            f"**Size:** {qty:.4f} (${value:,.2f})\n"
            f"**Confidence:** {confidence:.2f}\n"
            f"**Time:** {trade.get('timestamp', 'Now')}"
        )
        
        await self.send_message(message)
