"""
Binance Exchange Connector

Uses CCXT library for Binance Futures trading.
Defaults to testnet for safety.
"""

import os
import asyncio
from datetime import datetime
from typing import List, Optional
import logging

from dotenv import load_dotenv
load_dotenv()  # Load .env file

try:
    import ccxt.async_support as ccxt
    CCXT_AVAILABLE = True
except ImportError:
    CCXT_AVAILABLE = False
    ccxt = None

from .exchange import Exchange, OrderResult, Position


class BinanceConnector(Exchange):
    """
    Binance Futures connector using CCXT.
    
    By default, uses testnet mode for safety.
    Set testnet=False in config or BINANCE_TESTNET=false in .env for live trading.
    """
    
    def __init__(self, config: dict = None):
        super().__init__(config)
        
        if not CCXT_AVAILABLE:
            self.logger.error("ccxt not installed. Run: pip install ccxt")
            raise ImportError("ccxt library required for Binance integration")
        
        # Get credentials from config or environment
        self.api_key = self.config.get("api_key") or os.getenv("BINANCE_API_KEY", "")
        self.api_secret = self.config.get("api_secret") or os.getenv("BINANCE_SECRET", "")
        self.testnet = self.config.get("testnet", os.getenv("BINANCE_TESTNET", "true").lower() == "true")
        
        self.exchange = None
        self._connected = False
        
    def get_name(self) -> str:
        return "binance"
    
    async def connect(self) -> bool:
        """Initialize connection to Binance."""
        try:
            exchange_config = {
                'apiKey': self.api_key,
                'secret': self.api_secret,
                'enableRateLimit': True,
            }
            
            if self.testnet:
                self.logger.info("Connecting to Binance TESTNET (no real money)")
                # Use spot testnet (futures testnet deprecated)
                exchange_config['options'] = {'defaultType': 'spot'}
                self.exchange = ccxt.binance({
                    **exchange_config,
                    'sandbox': True,
                })
                self.exchange.set_sandbox_mode(True)
            else:
                self.logger.warning("⚠️ Connecting to Binance LIVE - REAL MONEY")
                exchange_config['options'] = {'defaultType': 'future'}
                self.exchange = ccxt.binance(exchange_config)
            
            # Test connection by loading markets
            await self.exchange.load_markets()
            self._connected = True
            self.logger.info(f"Connected to Binance ({'testnet' if self.testnet else 'LIVE'})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to Binance: {e}")
            return False
    
    async def disconnect(self):
        """Close the exchange connection."""
        if self.exchange:
            await self.exchange.close()
            self._connected = False
    
    async def get_balance(self, currency: str = "USDT") -> float:
        """Get available balance for a currency."""
        if not self._connected:
            await self.connect()
            
        try:
            balance = await self.exchange.fetch_balance()
            return float(balance.get(currency, {}).get('free', 0))
        except Exception as e:
            self.logger.error(f"Failed to fetch balance: {e}")
            return 0.0
    
    async def get_price(self, symbol: str) -> float:
        """Get current price for a symbol."""
        if not self._connected:
            await self.connect()
            
        try:
            ticker = await self.exchange.fetch_ticker(symbol)
            return float(ticker['last'])
        except Exception as e:
            self.logger.error(f"Failed to fetch price for {symbol}: {e}")
            return 0.0
            
    async def set_leverage(self, symbol: str, leverage: int):
        """Set leverage for a symbol."""
        if not self._connected:
            await self.connect()
            
        try:
            # Only supported on futures
            if not self.testnet: # Or proper check for futures mode
                await self.exchange.set_leverage(leverage, symbol)
                self.logger.info(f"Set leverage to {leverage}x for {symbol}")
        except Exception as e:
            self.logger.error(f"Failed to set leverage: {e}")
    
    async def place_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        order_type: str = "market",
        price: Optional[float] = None
    ) -> OrderResult:
        """Place an order on Binance."""
        if not self._connected:
            await self.connect()
            
        try:
            self.logger.info(f"Placing {order_type} {side} order: {quantity} {symbol}")
            
            if order_type == "market":
                order = await self.exchange.create_market_order(symbol, side, quantity)
            else:
                if price is None:
                    raise ValueError("Price required for limit orders")
                order = await self.exchange.create_limit_order(symbol, side, quantity, price)
            
            result = OrderResult(
                order_id=str(order['id']),
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=float(order.get('average', order.get('price', 0))),
                status='filled' if order['status'] == 'closed' else order['status'],
                timestamp=datetime.now(),
                raw_response=order
            )
            
            self.logger.info(f"Order placed: {result.order_id} - {result.status}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to place order: {e}")
            return OrderResult(
                order_id="",
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=0,
                status='failed',
                timestamp=datetime.now(),
                raw_response={'error': str(e)}
            )
    
    async def get_positions(self) -> List[Position]:
        """Get all open positions."""
        if not self._connected:
            await self.connect()
            
        try:
            positions = await self.exchange.fetch_positions()
            result = []
            
            for pos in positions:
                if float(pos['contracts']) > 0:
                    result.append(Position(
                        symbol=pos['symbol'],
                        side=pos['side'],
                        quantity=float(pos['contracts']),
                        entry_price=float(pos['entryPrice']),
                        current_price=float(pos['markPrice']),
                        unrealized_pnl=float(pos['unrealizedPnl']),
                        leverage=int(pos.get('leverage', 1))
                    ))
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to fetch positions: {e}")
            return []
    
    async def close_position(self, symbol: str) -> OrderResult:
        """Close an open position for a symbol."""
        positions = await self.get_positions()
        
        for pos in positions:
            if pos.symbol == symbol:
                # Close by placing opposite order
                side = 'sell' if pos.side == 'long' else 'buy'
                return await self.place_order(symbol, side, pos.quantity, "market")
        
        self.logger.warning(f"No open position found for {symbol}")
        return OrderResult(
            order_id="",
            symbol=symbol,
            side="",
            quantity=0,
            price=0,
            status='failed',
            timestamp=datetime.now(),
            raw_response={'error': 'No position found'}
        )
