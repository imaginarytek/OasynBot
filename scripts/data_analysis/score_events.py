#!/usr/bin/env python3
import sys
import os
import sqlite3
import asyncio
import logging

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.brain.sentiment import SentimentEngine

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("score_events")

def add_columns_if_missing():
    conn = sqlite3.connect('data/hedgemony.db')
    c = conn.cursor()
    
    # Check existing columns
    c.execute("PRAGMA table_info(curated_events)")
    cols = [row[1] for row in c.fetchall()]
    
    if 'ai_score' not in cols:
        print("Adding ai_score column...")
        c.execute("ALTER TABLE curated_events ADD COLUMN ai_score REAL")
        
    if 'ai_confidence' not in cols:
        print("Adding ai_confidence column...")
        c.execute("ALTER TABLE curated_events ADD COLUMN ai_confidence REAL")
        
    if 'impact_score' not in cols:
        print("Adding impact_score column...")
        c.execute("ALTER TABLE curated_events ADD COLUMN impact_score INTEGER")
        
    conn.commit()
    conn.close()

async def score_all_events():
    add_columns_if_missing()
    
    # Initialize Brain
    print("🧠 Initializing Sentiment Engine (The Council)...")
    try:
        engine = SentimentEngine()
    except Exception as e:
        print(f"Failed to init engine: {e}")
        return

    conn = sqlite3.connect('data/hedgemony.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Get all events
    c.execute("SELECT rowid, title, description FROM curated_events")
    events = c.fetchall()
    
    print(f"📋 Found {len(events)} events to score.")
    
    updates = []
    
    for i, event in enumerate(events):
        text = event['description']
        if not text:
            print(f"Skipping empty text: {event['title']}")
            continue
            
        print(f"[{i+1}/{len(events)}] Scoring: {event['title']}")
        
        # Analyze
        try:
            # Engine.analyze is async
            result = await engine.analyze(text)
            
            ai_score = result.get('score', 0.0)
            ai_conf = result.get('confidence', 0.0)
            impact = result.get('impact', 5)
            
            # If impact is 0 or None, try to infer from key words or set default
            if not impact: impact = 5
            
            updates.append((ai_score, ai_conf, impact, event['rowid']))
            print(f"   -> Score: {ai_score:.2f} | Conf: {ai_conf:.2f} | Impact: {impact}")
            
        except Exception as e:
            print(f"   ❌ Error scoring: {e}")
            
    # Batch Update
    print(f"\n💾 Saving {len(updates)} scores to database...")
    c.executemany(
        "UPDATE curated_events SET ai_score = ?, ai_confidence = ?, impact_score = ? WHERE rowid = ?",
        updates
    )
    conn.commit()
    conn.close()
    print("✅ Scoring Complete.")

if __name__ == "__main__":
    asyncio.run(score_all_events())
