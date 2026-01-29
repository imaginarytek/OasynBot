import logging
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Optional
from .polymarket import PolymarketHandler

@dataclass
class Trade:
    timestamp: datetime
    symbol: str
    side: str # 'buy' or 'sell'
    price: float
    quantity: float
    confidence: float
    pnl: float = 0.0
    status: str = 'open'

class PaperTradingExecutor:
    def __init__(self, config=None, db=None):
        self.logger = logging.getLogger("hedgemony.trading.paper")
        self.config = config or {}
        self.db = db
        
        # Initialize Polymarket Handler
        self.polymarket = PolymarketHandler(config)
        
        # Initialize Settings Manager
        from src.utils.settings import SettingsManager
        self.settings = SettingsManager()
        
        # Initialize Telegram Alerter
        from src.alerts.telegram import TelegramAlerter
        self.alerter = TelegramAlerter(config)
        
        # simulated account
        self.balance = 100000.0 # 100k USD start
        self.positions = {} # Symbol -> Quantity
        self.trade_history: List[Trade] = []
        
        self.logger.info(f"Paper Trader Initialized. Balance: ${self.balance:,.2f}")

    async def execute_signal(self, signal: dict):
        """
        signal format: {
            'source_item': NewsItem,
            'analysis': {'score': float, 'confidence': float, 'label': str},
            'symbol': 'BTC-USD' (derived or default)
        }
        """
        # Reload settings
        self.settings.reload()
        
        confidence = signal['analysis']['confidence']
        sentiment_score = signal['analysis']['score']
        label = signal['analysis']['label']
        
        # Dynamic Confidence Threshold
        min_confidence = self.settings.get("brain.confidence_threshold", 0.85)
        
        # Simple Logic: Only trade if confidence is high
        if confidence < min_confidence:
            self.logger.info(f"Skipping signal (Confidence {confidence:.2f} < Threshold {min_confidence})")
            return

        # Determine side
        side = None
        if label == 'positive':
            side = 'buy'
        elif label == 'negative':
            side = 'sell'
        else:
            return

        # "Prediction Market" style: Price is usually probability 0-1
        # Try to find a relevant market on simulated Polymarket
        market = await self.polymarket.find_market(signal['source_item'].title)
        
        market_id = "BTC-PERP" # Fallback
        current_price = 50000.0 # Fallback
        
        if market:
            market_id = market['id']
            # If side is 'buy' (positive), we buy 'Yes'. If 'sell' (negative), we buy 'No' (or short 'Yes')
            # Simplified: Buy the outcome matching sentiment
            outcome_idx = 0 if side == 'buy' else 1
            current_price = market['prices'][outcome_idx]
            self.logger.info(f"Found Market: {market['question']} | Price: {current_price}")
        else:
            self.logger.info("No matching prediction market found. Simulating generic BTC trade.")

        # v1.5 Impact Scaling
        impact = signal['analysis'].get('impact', 1)
        impact_multiplier = 1.0
        
        use_multiplier = self.settings.get("brain.use_impact_multiplier", True)
        if use_multiplier:
            if impact >= 8:
                impact_multiplier = 2.0 # Double size for high confidence events
                self.logger.info(f"High Impact Event ({impact}/10)! Doubling position size.")
            elif impact >= 5:
                impact_multiplier = 1.5

        # Position Sizing
        risk_pct = self.settings.get("trading.risk.max_position_size_pct", 0.05)
        base_trade_amount = self.balance * risk_pct
        trade_amount_usd = base_trade_amount * impact_multiplier
        
        # Cap at 20% max allocation per trade for safety
        max_alloc = self.balance * 0.20
        if trade_amount_usd > max_alloc:
            trade_amount_usd = max_alloc
            
        # Leverage (simulated effect)
        leverage = self.settings.get("trading.risk.max_leverage", 1)
        if leverage > 1:
            trade_amount_usd *= leverage
            self.logger.info(f"Applying {leverage}x Leverage. Effective Size: ${trade_amount_usd:,.2f}")
            
        quantity = trade_amount_usd / current_price

        # Execute via Polymarket Handler (Simulated)
        if market:
            await self.polymarket.place_paper_order(market_id, side, trade_amount_usd, current_price)

        # Log internally as usual
        trade = Trade(
            timestamp=datetime.now(),
            symbol=market_id,
            side=side,
            price=current_price,
            quantity=quantity,
            confidence=confidence
        )
        
        self.trade_history.append(trade)
        if self.db:
            self.db.log_trade(trade)
        
        # Send Alert
        await self.alerter.send_trade_alert({
            'symbol': market_id,
            'side': side,
            'price': current_price,
            'quantity': quantity,
            'confidence': confidence,
            'timestamp': trade.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        })
        
        self.logger.info(f"🔴 PAPER TRADE EXECUTION 🔴")
        self.logger.info(f"Side: {side.upper()} | Size: ${trade_amount_usd:,.2f} | Conf: {confidence:.2f}")
        
        return trade
