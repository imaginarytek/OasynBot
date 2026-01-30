#!/usr/bin/env python3
"""
VERIFY TRI-AGENT VOTING COUNCIL
--------------------------------
Tests the new 3-model voting system on sample headlines.
"""

import sys
import os
import asyncio
import yaml

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

async def test_voting():
    print("=" * 70)
    print("TRI-AGENT VOTING COUNCIL TEST")
    print("=" * 70)
    
    # Load config
    with open('config/live_trading_config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Initialize Sentiment Engine
    from src.brain.sentiment import SentimentEngine
    engine = SentimentEngine(config)
    
    # Test Headlines
    test_cases = [
        "BREAKING: SEC Approves Bitcoin ETF - Historic Moment for Crypto",
        "FTX Files for Bankruptcy - Billions in Customer Funds Missing",
        "Bitcoin Price Unchanged After Fed Meeting",
        "Trump Announces Strategic Bitcoin Reserve for United States",
        "China Bans All Cryptocurrency Mining Operations"
    ]
    
    print("\n🧠 COUNCIL MEMBERS:")
    print("   1. Groq (Llama-3) - The Strategist")
    print("   2. FinBERT - The Banker")
    print("   3. DeBERTa - The Logician")
    print("\n" + "=" * 70)
    
    for i, headline in enumerate(test_cases, 1):
        print(f"\n📰 TEST {i}: {headline[:60]}...")
        print("-" * 70)
        
        try:
            result = await engine.analyze(headline)
            
            print(f"🏛️  VERDICT: {result['label'].upper()}")
            print(f"📊 Score: {result['score']:.3f}")
            print(f"🎯 Confidence: {result['confidence']:.2%}")
            print(f"💥 Impact: {result.get('impact', 0)}/10")
            print(f"💭 Reasoning: {result['reasoning']}")
            
        except Exception as e:
            print(f"❌ ERROR: {e}")
        
        print("-" * 70)
    
    print("\n✅ Voting Council Test Complete!")

if __name__ == "__main__":
    asyncio.run(test_voting())
