#!/usr/bin/env python3
"""
GOLD NEWS BURST GENERATOR (High Fidelity)
Simulates realistic 'News Bursts' for the Gold Standard dataset.
Generates 5-10 distinct news items per event from a pool of 15+ sources.
"""

import sys
import os
import random
from datetime import datetime, timedelta
import json
import sqlite3

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.utils.db import Database

# --- SOURCE POOLS ---
TIER_1_FAST = [
    {"id": "twitter_DeItaone", "name": "Walter Bloomberg", "type": "terminal"},
    {"id": "twitter_FirstSquawk", "name": "First Squawk", "type": "terminal"},
    {"id": "twitter_Tier10k", "name": "Tier10k", "type": "aggregator"},
    {"id": "twitter_Tree_of_Alpha", "name": "Tree of Alpha", "type": "aggregator"},
]

TIER_2_MAINSTREAM = [
    {"id": "rss_reuters", "name": "Reuters", "type": "news"},
    {"id": "rss_bloomberg", "name": "Bloomberg", "type": "news"},
    {"id": "rss_wsj", "name": "WSJ Markets", "type": "news"},
    {"id": "rss_cnbc", "name": "CNBC Fast Money", "type": "news"},
]

TIER_3_CRYPTO = [
    {"id": "rss_coindesk", "name": "CoinDesk", "type": "crypto_news"},
    {"id": "rss_theblock", "name": "The Block", "type": "crypto_news"},
    {"id": "rss_cointelegraph", "name": "CoinTelegraph", "type": "crypto_news"},
    {"id": "rss_decrypt", "name": "Decrypt", "type": "crypto_news"},
]

TIER_4_NOISE = [
    {"id": "twitter_whale_alert", "name": "Whale Alert", "type": "bot"},
    {"id": "twitter_influencer", "name": "CryptoKey", "type": "influencer"},
    {"id": "twitter_random", "name": "BitcoinArchive", "type": "influencer"},
    {"id": "twitter_reddit_bot", "name": "Reddit Crypto", "type": "bot"},
    {"id": "twitter_moon_lambo", "name": "Moon Lambo", "type": "influencer"},
    {"id": "twitter_wsb_chairman", "name": "WSB Chairman", "type": "influencer"},
]

class GoldNewsBurstGenerator:
    def __init__(self):
        self.db = Database()

    def generate_burst(self, event_row):
        """Generate 5-10 news items for a single event"""
        title = event_row['title']
        try:
            base_time = datetime.fromisoformat(event_row['timestamp'])
        except ValueError:
            # Handle potential non-iso formats if any crept in
             base_time = datetime.strptime(event_row['timestamp'], "%Y-%m-%d %H:%M:%S")

        impact = event_row['impact_score']
        
        burst_items = []
        
        # 1. ALWAYS select 1-2 Tier 1 Sources (The "Signal")
        # Ensure k <= len(TIER_1_FAST)
        t1_count = min(len(TIER_1_FAST), random.randint(1, 2))
        t1_sources = random.sample(TIER_1_FAST, k=t1_count)
        
        for src in t1_sources:
            # Terminal style: Uppercase, terse
            headline = f"*{title.upper()}"
            if src['id'] == "twitter_Tier10k":
                headline = f"{title} [Ref]"
            
            latency = random.uniform(0.1, 3.0) # 100ms to 3s
            burst_items.append({
                "source": src['id'],
                "text": headline,
                "time": base_time + timedelta(seconds=latency),
                "confidence": 0.99
            })
            
        # 2. Add 2-3 Tier 2/3 Sources (The "Confirmation")
        t23_pool = TIER_2_MAINSTREAM + TIER_3_CRYPTO
        t23_count = min(len(t23_pool), random.randint(2, 4))
        t23_sources = random.sample(t23_pool, k=t23_count)
        
        for src in t23_sources:
            headline = f"{title}: Full report and market impact."
            latency = random.uniform(5.0, 45.0) # 5s to 45s
            burst_items.append({
                "source": src['id'],
                "text": headline,
                "time": base_time + timedelta(seconds=latency),
                "confidence": 0.95
            })
            
        # 3. Add 2-4 Noise Sources (The "Crowd")
        t4_count = min(len(TIER_4_NOISE), random.randint(2, 4))
        t4_sources = random.sample(TIER_4_NOISE, k=t4_count)
        
        for src in t4_sources:
            reaction = random.choice(["Huge!", "It's happening", "Market moving", "Liquidation cascade incoming", "FUD?", "Buy the dip!"])
            headline = f"{title} - {reaction}"
            latency = random.uniform(2.0, 30.0) # Fast but noisy
            burst_items.append({
                "source": src['id'],
                "text": headline,
                "time": base_time + timedelta(seconds=latency),
                "confidence": 0.60
            })

        # Sort by time
        burst_items.sort(key=lambda x: x['time'])
        return burst_items

    def run(self):
        print("🚀 Generating Gold Standard News Bursts (5-10 Sources/Event)...")
        
        conn = self.db.get_connection()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Get events
        try:
            c.execute("SELECT * FROM gold_events")
            events = [dict(row) for row in c.fetchall()]
        except Exception as e:
            print(f"Error reading gold_events: {e}")
            return

        print(f"Found {len(events)} events to process.")
        
        total_news = 0
        for event in events:
            burst = self.generate_burst(event)
            
            for item in burst:
                c.execute('''
                    INSERT INTO news (source_id, title, published_at, sentiment_score, sentiment_label, confidence, impact_score, ingested_at, raw_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    item['source'],
                    item['text'],
                    item['time'].isoformat(),
                    0, # Placeholder score - The Analysis Engine will compute based on title
                    "neutral",
                    item['confidence'],
                    event['impact_score'], # Pass the "Truth" impact for validation logic
                    item['time'].isoformat(),
                    json.dumps({"is_gold_standard": True, "event_id": event['id']})
                ))
                total_news += 1
                
        conn.commit()
        conn.close()
        print(f"✅ Generated {total_news} news items for {len(events)} events.")

if __name__ == "__main__":
    gen = GoldNewsBurstGenerator()
    gen.run()
