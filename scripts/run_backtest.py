
import logging
import sys
import os
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.backtest.engine import BacktestEngine
from src.backtest.strategy import SentimentStrategy
from src.utils.db import Database

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("hedgemony.run_backtest")

def main():
    logger.info("Initializing Backtest...")
    
    db = Database()
    
    # 1. Setup Strategy
    # Confidence threshold 0.8 to only trade strongly on our fake news
    strategy = SentimentStrategy({"confidence_threshold": 0.8})
    
    # 2. Setup Engine
    engine = BacktestEngine(strategy, db, initial_balance=100000.0, position_size_pct=0.1)
    
    # 3. Load Sentiment Data
    # In real world, we query DB for news in that range.
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 1, 31)
    
    logger.info(f"Loading News from DB: {start_date.date()} to {end_date.date()}")
    news_rows = db.get_news_by_date_range(start_date, end_date)
    
    # Convert DB rows to simplified sentiment signals list for the engine
    # Engine expects specific format or we pass raw and strategy handles it
    # Engine expects list of dicts.
    
    sentiment_data = []
    for row in news_rows:
        sentiment_data.append({
            'timestamp': row['published_at'],
            'label': row['sentiment_label'],
            'score': row['sentiment_score'],
            'confidence': row['confidence'],
            'impact': row['impact_score']
        })
        
    logger.info(f"Loaded {len(sentiment_data)} news items.")

    # 4. Run Backtest
    result = engine.run("BTC-USD", start_date, end_date, sentiment_data)
    
    # 5. Report
    print("\n" + "="*50)
    print(f"BACKTEST RESULTS: {result.strategy_name} on {result.symbol}")
    print("="*50)
    print(f"Period: {result.start_date.date()} - {result.end_date.date()}")
    print(f"Initial Balance: ${result.initial_balance:,.2f}")
    print(f"Final Balance:   ${result.final_balance:,.2f}")
    print(f"PnL:             ${result.metrics.total_pnl:,.2f} ({result.metrics.total_pnl_pct:.2f}%)")
    print(f"Win Rate:        {result.metrics.win_rate:.1f}% ({result.metrics.winning_trades}/{result.metrics.total_trades})")
    print("-" * 50)
    print("TRADES:")
    for trade in result.trades:
        print(f"{trade.timestamp.date()} | {trade.side.upper()} @ ${trade.entry_price:,.2f} | PnL: ${trade.pnl:,.2f} | {trade.reason}")
    print("="*50 + "\n")

if __name__ == "__main__":
    main()
