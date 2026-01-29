"""
Hyperliquid Exchange Connector (SDK Integrated)

Uses hyperliquid-python-sdk to handle EIP-712 Signing and Order Execution.
"""

import logging
import asyncio
from datetime import datetime
from typing import Optional, List, Dict
import eth_utils
from eth_account import Account
import json

# SDK Imports
from hyperliquid.utils import constants
from hyperliquid.info import Info
from hyperliquid.exchange import Exchange as HLExchange # Rename to avoid conflict with Base Class

from .exchange import Exchange, OrderResult, Position

class HyperliquidConnector(Exchange):
    def __init__(self, config: dict = None):
        super().__init__(config)
        self.base_url = constants.MAINNET_API_URL
        self.wallet_private_key = self.config.get("private_key")
        self.wallet_address = self.config.get("wallet_address")
        
        # Initialize Info (Public Data)
        self.info = Info(self.base_url, skip_ws=True)
        
        # Initialize Exchange (Authenticated Actions)
        if self.wallet_private_key:
            self.account = Account.from_key(self.wallet_private_key)
            self.hl_exchange = HLExchange(self.account, self.base_url, account_address=self.wallet_address)
            self.logger.info(f"Hyperliquid Signer Loaded: {self.wallet_address[:6]}...")
        else:
            self.hl_exchange = None
            self.logger.warning("No Private Key. Hyperliquid is READ-ONLY.")

    def get_name(self) -> str:
        return "hyperliquid"
        
    async def connect(self) -> bool:
        """Test connection via Info API."""
        try:
            # Synchronous call in separate thread to avoid blocking? 
            # SDK is synchronous requests based. We wrapp in asyncio.to_thread if heavy.
            # Simple check
            meta = self.info.meta()
            if meta:
                self.logger.info("Connected to Hyperliquid L1 (SDK).")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Hyperliquid Connection Error: {e}")
            return False

    async def get_price(self, symbol: str) -> float:
        """Get Mid Price for symbol (e.g. 'SOL/USD')."""
        coin = symbol.split("/")[0] # 'SOL'
        try:
            all_mids = self.info.all_mids()
            price = float(all_mids.get(coin, 0.0))
            return price
        except Exception as e:
             self.logger.error(f"Price Fetch Fail: {e}")
             return 0.0

    async def get_balance(self, currency: str = "USDT") -> float:
        """Get USDC Equity."""
        if not self.wallet_address: return 0.0
        try:
            state = self.info.user_state(self.wallet_address)
            margin_summary = state.get("marginSummary", {})
            equity = float(margin_summary.get("accountValue", 0.0))
            return equity
        except Exception as e:
             self.logger.error(f"Balance Fetch Fail: {e}")
             return 0.0

    async def place_order(self, symbol: str, side: str, quantity: float, order_type: str = "market", price: Optional[float] = None) -> OrderResult:
        """
        Execute Order via SDK.
        """
        if not self.hl_exchange:
             return OrderResult(
                 order_id="fail", symbol=symbol, side=side, quantity=quantity, price=0, 
                 status="failed", timestamp=datetime.now(), raw_response={"error": "no_key"}
             )

        coin = symbol.split("/")[0] # 'SOL'
        is_buy = (side.lower() == "buy")
        
        try:
            # Market Order in Hyperliquid is Limit Order with huge slippage/crossing
            # SDK Helper: exchange.market_open(coin, is_buy, sz, px, slippage)
            # We need current price
            current_price = await self.get_price(symbol)
            if current_price == 0: raise ValueError("Price is zero")
            
            # Execute
            self.logger.info(f"Placing Order: {side} {quantity} {coin} @ {current_price}")
            
            # SDK call is blocking IO, wrap it?
            # For now, just call it. Speed is key.
            # slippage 5% for market
            result = self.hl_exchange.market_open(coin, is_buy, quantity, current_price, 0.05)
            
            # Parse result
            status = result.get("status")
            if status == "ok":
                # Extract details
                # statuses: [{'filled': {'totalSz': '1.0', 'avgPx': '20.5', 'oid': 123}}]
                statuses = result.get("response", {}).get("data", {}).get("statuses", [])
                if statuses and "filled" in statuses[0]:
                    fill = statuses[0]["filled"]
                    avg_px = float(fill["avgPx"])
                    oid = str(fill["oid"])
                    
                    return OrderResult(
                        order_id=oid,
                        symbol=symbol,
                        side=side,
                        quantity=quantity,
                        price=avg_px,
                        status="filled",
                        timestamp=datetime.now(),
                        raw_response=result
                    )
            
            # Failed
            return OrderResult(
                order_id="error", symbol=symbol, side=side, quantity=quantity, price=0,
                status="failed", timestamp=datetime.now(), raw_response=result
            )

        except Exception as e:
            self.logger.error(f"Order Placement Error: {e}")
            return OrderResult(
                order_id="except", symbol=symbol, side=side, quantity=quantity, price=0,
                status="failed", timestamp=datetime.now(), raw_response={"error": str(e)}
            )

    async def get_positions(self) -> List[Position]:
        """Get Open Positions."""
        if not self.wallet_address: return []
        
        try:
            state = self.info.user_state(self.wallet_address)
            raw_positions = state.get("assetPositions", [])
            
            positions = []
            for p in raw_positions:
                pos = p.get("position", {})
                coin = pos.get("coin")
                sze = float(pos.get("sze", 0))
                entry = float(pos.get("entryPx", 0))
                pnl = float(pos.get("unrealizedPnl", 0))
                
                if sze != 0:
                    positions.append(Position(
                        symbol=f"{coin}/USD",
                        side="buy" if sze > 0 else "sell",
                        quantity=abs(sze),
                        entry_price=entry,
                        current_price=entry + (pnl/sze) if sze!=0 else entry,
                        unrealized_pnl=pnl,
                        leverage=3 # Default
                    ))
            return positions
        except Exception as e:
             self.logger.error(f"Positions Fetch Fail: {e}")
             return []

    async def close_position(self, symbol: str) -> OrderResult:
        """Close position via Market Order."""
        positions = await self.get_positions()
        target_pos = next((p for p in positions if p.symbol == symbol), None)
        
        if not target_pos:
            return OrderResult("no_pos", symbol, "none", 0, 0, "failed", datetime.now())
            
        # Determine strict side to close
        close_side = "sell" if target_pos.quantity > 0 else "buy"
        
        # Execute Closing Order
        # Hyperliquid 'market_close' exists in SDK?
        # Use market_close helper if available, else manual
        try:
            coin = symbol.split("/")[0]
            # exchange.market_close(coin)
            result = self.hl_exchange.market_close(coin)
            if result['status'] == 'ok':
                 return OrderResult(
                     order_id="close_success", symbol=symbol, side=close_side, quantity=target_pos.quantity,
                     price=0, status="filled", timestamp=datetime.now(), raw_response=result
                 )
            else:
                 return OrderResult("close_fail", symbol, close_side, 0, 0, "failed", datetime.now(), raw_response=result)
        except Exception as e:
            self.logger.error(f"Close Position Fail: {e}")
            return OrderResult("close_except", symbol, close_side, 0, 0, "failed", datetime.now())
