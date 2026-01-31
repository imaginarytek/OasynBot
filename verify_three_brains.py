#!/usr/bin/env python3
"""
Verify all three AI brains are voting in the Council.
"""
import asyncio
import sys
import os
from dotenv import load_dotenv

load_dotenv()
sys.path.append('.')

from src.brain.sentiment import SentimentEngine

async def verify_council():
    print("=" * 80)
    print("VERIFYING COUNCIL OF THREE AI BRAINS")
    print("=" * 80)

    engine = SentimentEngine()

    # Check which brains are active
    print("\n📋 Brain Status:")
    print(f"   🧠 Groq:    {'✅ ACTIVE' if engine.groq_analyzer else '❌ INACTIVE'}")
    print(f"   🧠 FinBERT: {'✅ ACTIVE' if hasattr(engine, 'finbert_pipe') and engine.finbert_pipe else '❌ INACTIVE'}")
    print(f"   🧠 DeBERTa: {'✅ ACTIVE' if hasattr(engine, 'deberta_pipe') and engine.deberta_pipe else '❌ INACTIVE'}")

    # Test the council
    test_text = "SEC Approves Bitcoin ETF - The Securities and Exchange Commission has approved the first Bitcoin spot ETF, marking a historic victory for cryptocurrency adoption."

    print(f"\n📰 Test News:")
    print(f"   {test_text[:100]}...")

    print(f"\n⚙️  Running Council Analysis...")
    result = await engine.analyze(test_text)

    print(f"\n📊 COUNCIL DECISION:")
    print(f"   Label:      {result['label'].upper()}")
    print(f"   Score:      {result['score']:.2f}")
    print(f"   Confidence: {result['confidence']:.2f}")
    print(f"   Reasoning:  {result['reasoning']}")

    # Check for GOD MODE (unanimous)
    if "GOD MODE" in result.get('reasoning', ''):
        print(f"\n   🎯 GOD MODE ACTIVATED - All three brains agree!")
    elif "NO CONSENSUS" in result.get('reasoning', ''):
        print(f"\n   ⚠️  NO CONSENSUS - Brains disagree, trade skipped")
    else:
        print(f"\n   ✓ Majority consensus reached")

    print("\n" + "=" * 80)
    if engine.groq_analyzer and engine.finbert_pipe and engine.deberta_pipe:
        print("✅ ALL THREE BRAINS ARE OPERATIONAL AND VOTING!")
    else:
        missing = []
        if not engine.groq_analyzer:
            missing.append("Groq")
        if not (hasattr(engine, 'finbert_pipe') and engine.finbert_pipe):
            missing.append("FinBERT")
        if not (hasattr(engine, 'deberta_pipe') and engine.deberta_pipe):
            missing.append("DeBERTa")
        print(f"⚠️  Missing brains: {', '.join(missing)}")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(verify_council())
