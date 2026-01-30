#!/usr/bin/env python3
"""
MEMORY TRAINER (RAG)
--------------------
Reads 'gold_events' (News + Price Data).
Calculates realized price impact (30m outcome).
Indexes the lesson into ChromaDB for future retrieval.
"""

import sys
import os
import json
import sqlite3
import pandas as pd
import numpy as np
import logging
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.utils.db import Database
from src.brain.memory import MemoryManager

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("memory_trainer")

class MemoryTrainer:
    def __init__(self):
        self.db = Database()
        # Load config to get memory settings (passing mock config if needed)
        self.config = {
            "brain": {
                "memory": {
                    "enabled": True,
                    "collection_name": "market_events",
                    "path": "data/chromadb"
                }
            }
        }
        self.memory = MemoryManager(self.config)

    def calculate_outcome(self, price_data):
        """
        Calculate the 30-minute price change percentage.
        Returns: (pct_change, label)
        """
        if not price_data:
            return 0.0, "NEUTRAL"
            
        try:
            df = pd.DataFrame(price_data)
            if df.empty:
                return 0.0, "NEUTRAL"
                
            # Assume price_data covers -5m to +30m. 
            # Event is roughly around index 5 (5 minutes in).
            # We want change from Event Start (Open at ~5m) to End of Window (30m later).
            
            # Simple heuristic: Start at index 5, End at last index
            start_price = df.iloc[5]['open'] if len(df) > 5 else df.iloc[0]['open']
            end_price = df.iloc[-1]['close']
            
            pct_change = ((end_price - start_price) / start_price) * 100
            
            label = "NEUTRAL"
            if pct_change > 0.5:
                label = "BULLISH"
            elif pct_change < -0.5:
                label = "BEARISH"
                
            return pct_change, label
            
        except Exception as e:
            logger.error(f"Error calculating outcome: {e}")
            return 0.0, "NEUTRAL"

    def run(self):
        logger.info("🧠 Starting Memory Training...")
        
        # 1. Fetch Gold Events
        conn = self.db.get_connection()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM gold_events")
        events = [dict(row) for row in c.fetchall()]
        conn.close()
        
        logger.info(f"Found {len(events)} events to learn from.")
        
        count = 0
        for event in events:
            try:
                title = event['title']
                
                # Check if price data exists
                if not event['price_data']:
                    logger.warning(f"Skipping {title} (No price data)")
                    continue
                    
                price_data = json.loads(event['price_data'])
                
                # 2. Calculate Outcome
                pct_change, label = self.calculate_outcome(price_data)
                
                # 3. Create Memory Item
                # We store the *Outcome* as metadata so the Brain knows what happened.
                metadata = {
                    "impact": event['impact_score'],
                    "outcome_pct": round(pct_change, 2),
                    "outcome_label": label,
                    "timestamp": datetime.fromisoformat(event['timestamp']).timestamp()
                }
                
                # The text to embed is the News Title itself
                # The ID matches the gold event ID
                self.memory.add_event(
                    text=title,
                    metadata=metadata,
                    event_id=event['id']
                )
                
                logger.info(f"✅ Learned: {title[:40]}... -> {label} ({pct_change:+.2f}%)")
                count += 1
                
            except Exception as e:
                logger.error(f"Failed to process event: {e}")
                
        logger.info(f"🎉 Training Complete. {count} events indexed into Vector Memory.")

if __name__ == "__main__":
    trainer = MemoryTrainer()
    trainer.run()
