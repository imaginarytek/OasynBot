"""
Base Exchange Interface

Abstract interface for exchange connectors.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict
import logging


@dataclass
class OrderResult:
    """Result of an order placement."""
    order_id: str
    symbol: str
    side: str
    quantity: float
    price: float
    status: str  # 'filled', 'pending', 'failed'
    timestamp: datetime
    raw_response: Optional[dict] = None


@dataclass
class Position:
    """Open position on an exchange."""
    symbol: str
    side: str
    quantity: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    leverage: int = 1


class Exchange(ABC):
    """
    Abstract base class for exchange connectors.
    
    All exchange implementations must implement these methods.
    """
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.logger = logging.getLogger(f"hedgemony.exchange.{self.get_name()}")
        self.testnet = self.config.get("testnet", True)  # Default to testnet for safety
        
    @abstractmethod
    def get_name(self) -> str:
        """Return the exchange name."""
        pass
    
    @abstractmethod
    async def connect(self) -> bool:
        """
        Connect to the exchange.
        Returns True if connection successful.
        """
        pass
    
    @abstractmethod
    async def get_balance(self, currency: str = "USDT") -> float:
        """Get available balance for a currency."""
        pass
    
    @abstractmethod
    async def get_price(self, symbol: str) -> float:
        """Get current price for a symbol."""
        pass
    
    @abstractmethod
    async def place_order(
        self,
        symbol: str,
        side: str,  # 'buy' or 'sell'
        quantity: float,
        order_type: str = "market",  # 'market' or 'limit'
        price: Optional[float] = None
    ) -> OrderResult:
        """
        Place an order on the exchange.
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            side: 'buy' or 'sell'
            quantity: Amount to trade
            order_type: 'market' or 'limit'
            price: Required for limit orders
            
        Returns:
            OrderResult with order details
        """
        pass
    
    @abstractmethod
    async def get_positions(self) -> List[Position]:
        """Get all open positions."""
        pass
    
    @abstractmethod
    async def close_position(self, symbol: str) -> OrderResult:
        """Close an open position for a symbol."""
        pass
    
    async def get_ticker(self, symbol: str) -> Dict:
        """Get full ticker data for a symbol."""
        price = await self.get_price(symbol)
        return {"symbol": symbol, "price": price}
