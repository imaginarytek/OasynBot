"""
Live Trading Executor (V2.9.2)

Upgraded Execution Engine handling:
1. Signal Confirmation (300s Polling)
2. Entry Execution (Hyperliquid)
3. Trailing Stop Management (Chaos Bracket)
"""

import logging
import asyncio
from datetime import datetime
from typing import Optional
import os
import json

from dotenv import load_dotenv

from .exchange import Exchange, OrderResult
from .binance import BinanceConnector
from .hyperliquid import HyperliquidConnector
from src.utils.db import Database

# Load environment variables
load_dotenv()


class LiveTradingExecutor:
    """
    Executes trades with V2.9.2 "Hunter" Strategy logic.
    """
    
    EXCHANGE_MAP = {
        'binance': BinanceConnector,
        'hyperliquid': HyperliquidConnector
    }
    
    def __init__(self, config: dict = None, db: Database = None):
        self.logger = logging.getLogger("hedgemony.trading.live")
        self.config = config or {}
        self.db = db
        
        trading_config = self.config.get("trading", {})
        self.exchange_name = trading_config.get("exchange", "hyperliquid")
        self.risk_config = trading_config.get("risk", {})
        
        # Risk parameters (From Config)
        self.max_leverage = self.risk_config.get("max_leverage", 3)
        self.position_size_pct = self.risk_config.get("max_position_size_pct", 0.10)
        
        # STRATEGY PARAMS V2.9.2 (From Config or Default)
        self.CONFIRM_WINDOW_SEC = 300 # Strategy Logic (Keep as Logic default)
        self.CONFIRM_THRESH = 0.0020
        self.STOP_LOSS_PCT = self.risk_config.get("global_stop_loss_pct", 0.035)
        
        # Initialize Settings Manager
        from src.utils.settings import SettingsManager
        self.settings = SettingsManager()
        
        # Initialize Telegram Alerter
        from src.alerts.telegram import TelegramAlerter
        self.alerter = TelegramAlerter(config)
        
        # Initialize exchange
        self.exchange: Optional[Exchange] = None
        self._init_exchange()
        
        # Active Management Tasks
        self.active_trades = {} # symbol -> asyncio.Task
        
    def _init_exchange(self):
        """Initialize the configured exchange."""
        exchange_class = self.EXCHANGE_MAP.get(self.exchange_name)
        
        if exchange_class is None:
            self.logger.error(f"Unknown exchange: {self.exchange_name}")
            return
            
        exchange_config = self.config.get(self.exchange_name, {})
        # Merge global keys if needed
        if self.exchange_name == 'hyperliquid':
            if not exchange_config.get('private_key'):
                 exchange_config['private_key'] = os.getenv("HYPERLIQUID_PRIVATE_KEY")
                 exchange_config['wallet_address'] = os.getenv("HYPERLIQUID_WALLET_ADDRESS")

        self.exchange = exchange_class(exchange_config)
        self.logger.info(f"Initialized {self.exchange_name} executor")
    
    async def connect(self) -> bool:
        if self.exchange:
            return await self.exchange.connect()
        return False
    
    async def execute_signal(self, signal: dict):
        """
        Entry point for Engine signals.
        Spawns an async task to handle the lifecycle (Wait -> Enter -> Manage).
        Does NOT block the engine.
        """
        if not self.exchange:
            self.logger.error("No exchange configured")
            return
            
        # Spawn execution task
        asyncio.create_task(self._process_trade_lifecycle(signal))
        
    async def _process_trade_lifecycle(self, signal: dict):
        """
        V2.9.2 Workflow:
        1. Wait for Price Confirmation
        2. Enter Position
        3. Manage Trailing Stop
        """
        symbol = signal.get('symbol', 'SOL/USD') # Default to SOL/USD
        if "SOL" in signal.get('source_item',{}).get('title',"").upper():
             symbol = "SOL/USD" # Force SOL for now as strategy is tuned for it
             
        conf = signal['analysis']['confidence']
        label = signal['analysis']['label']
        title = signal['source_item'].get('title', 'Unknown News')
        
        direction = 1 if label == 'positive' else -1
        side = 'buy' if direction == 1 else 'sell'
        
        self.logger.info(f"⏳ SIGNAL RECEIVED: {title[:30]}... Waiting for {self.CONFIRM_THRESH:.2%} move in 300s...")

        # ---------------------------------------------------------
        # PHASE 1: CONFIRMATION POLLER
        # ---------------------------------------------------------
        confirmed = await self._wait_for_confirmation(symbol, direction)
        
        if not confirmed:
            self.logger.info(f"❌ SIGNAL EXPIRED: Price did not confirm ({title[:20]})")
            return

        # ---------------------------------------------------------
        # PHASE 2: ENTRY
        # ---------------------------------------------------------
        self.logger.info(f"✅ CONFIRMED! Executing {side.upper()} on {symbol}")
        
        # Calculate Size
        balance = await self.exchange.get_balance("USDT") # Hyperliquid uses USDC but interface says USDT
        if balance <= 0:
            self.logger.error("Zero Balance. Cannot trade.")
            return

        trade_amount = balance * self.position_size_pct * self.max_leverage # 10% * 3x = 30% notional
        price = await self.exchange.get_price(symbol)
        quantity = trade_amount / price
        
        # Round quantity (SOL precision 2 decimals usually, safer to int or 1 decimal)
        quantity = round(quantity, 2) 

        # Execute
        result = await self.exchange.place_order(symbol, side, quantity, "market")
        
        if result.status != 'filled':
            self.logger.error(f"Entry Failed: {result.raw_response}")
            return
            
        entry_price = result.price
        self.logger.info(f"🚀 FILLED {side} {quantity} {symbol} @ {entry_price}")
        
        # Log Trade
        if self.db:
             from .executor import Trade
             self.db.log_trade(Trade(
                 timestamp=datetime.now(),
                 symbol=symbol,
                 side=side,
                 price=entry_price,
                 quantity=quantity,
                 confidence=conf,
                 status='filled'
             ))
             
        # Alert
        await self.alerter.send_trade_alert({
             'symbol': symbol, 'side': side, 'price': entry_price, 
             'quantity': quantity, 'confidence': conf, 'msg': f"Confirmed on: {title}"
        })

        # ---------------------------------------------------------
        # PHASE 3: CHAOS BRACKET MANAGEMENT
        # ---------------------------------------------------------
        await self._manage_trailing_stop(symbol, side, entry_price, quantity)

    async def _wait_for_confirmation(self, symbol: str, direction: int) -> bool:
        """Poll price for 300s. Return True if move > 0.20%."""
        start_price = await self.exchange.get_price(symbol)
        if start_price == 0: return False
        
        start_time = datetime.now()
        
        while (datetime.now() - start_time).total_seconds() < self.CONFIRM_WINDOW_SEC:
            current_price = await self.exchange.get_price(symbol)
            if current_price == 0: continue
            
            pnl_pct = (current_price - start_price)/start_price if direction == 1 else (start_price - current_price)/start_price
            
            if pnl_pct >= self.CONFIRM_THRESH:
                return True
                
            await asyncio.sleep(1) # Poll every 1s
            
        return False

    async def _manage_trailing_stop(self, symbol: str, side: str, entry_price: float, quantity: float):
        """
        Async loop to manage Stop Loss in memory.
        Triggers Market Close when stop hit.
        """
        direction = 1 if side == 'buy' else -1
        
        # Initial Stop
        current_stop = entry_price * (1 - self.STOP_LOSS_PCT) if direction == 1 else entry_price * (1 + self.STOP_LOSS_PCT)
        
        self.logger.info(f"🛡️ MANAGE: Initial Stop @ {current_stop:.4f}")
        
        highest_pnl = 0.0
        active = True
        
        while active:
            price = await self.exchange.get_price(symbol)
            if price == 0: 
                await asyncio.sleep(1)
                continue
                
            # Calc PnL
            if direction == 1:
                pnl = (price - entry_price) / entry_price
                # Check Stop
                if price <= current_stop:
                    self.logger.warning(f"🛑 STOP HIT @ {price:.4f} (PnL: {pnl:.2%})")
                    await self.exchange.close_position(symbol)
                    active = False
                    break
                
                highest_pnl = max(highest_pnl, pnl)
                
                # Update Stop (Standard Bracket)
                # 1. Moonbag (>6% -> Trail 0.5%)
                if highest_pnl > 0.06:
                     new_stop = price * (1 - 0.005)
                     if new_stop > current_stop:
                         current_stop = new_stop
                         self.logger.info(f"🌕 MOONBAG: Stop moved to {current_stop:.4f}")
                # 2. Lock (>3% -> Trail 1%)
                elif highest_pnl > 0.03:
                     new_stop = price * (1 - 0.010)
                     if new_stop > current_stop:
                         current_stop = new_stop
                         self.logger.info(f"🔒 LOCK: Stop moved to {current_stop:.4f}")
                # 3. Breakeven (>1.5% -> BE)
                elif highest_pnl > 0.015:
                     new_stop = max(current_stop, entry_price * 1.002)
                     if new_stop > current_stop:
                         current_stop = new_stop
                         self.logger.info(f"🛡️ BREAKEVEN: Stop moved to {current_stop:.4f}")

            else: # Short
                pnl = (entry_price - price) / entry_price
                if price >= current_stop:
                    self.logger.warning(f"🛑 STOP HIT @ {price:.4f}")
                    await self.exchange.close_position(symbol)
                    active = False
                    break
                    
                highest_pnl = max(highest_pnl, pnl)
                
                if highest_pnl > 0.06:
                     new_stop = price * (1 + 0.005)
                     if new_stop < current_stop: current_stop = new_stop
                elif highest_pnl > 0.03:
                     new_stop = price * (1 + 0.010)
                     if new_stop < current_stop: current_stop = new_stop
                elif highest_pnl > 0.015:
                     new_stop = min(current_stop, entry_price * 0.998)
                     if new_stop < current_stop: current_stop = new_stop
                     
            await asyncio.sleep(1) # Monitor every 1s
