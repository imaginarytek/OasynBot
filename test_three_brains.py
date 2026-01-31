#!/usr/bin/env python3
"""
Test the Three Brains Council voting system.
"""
import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.append('.')

from src.brain.sentiment import SentimentEngine

async def test_three_brains():
    """Test the Council of Three on sample news."""

    print("=" * 80)
    print("TESTING THE COUNCIL OF THREE AI BRAINS")
    print("=" * 80)

    # Initialize the sentiment engine (loads all three brains)
    print("\nInitializing Council...\n")
    engine = SentimentEngine()

    # Test cases
    test_cases = [
        {
            'title': 'SEC Approves Bitcoin ETF',
            'text': 'SEC Approves Bitcoin ETF - The Securities and Exchange Commission has approved the first Bitcoin ETF, marking a major milestone for cryptocurrency adoption.',
            'expected': 'BULLISH'
        },
        {
            'title': 'Major Exchange Hacked',
            'text': 'Major Exchange Hacked - Binance reports $500M stolen in security breach, causing panic in crypto markets.',
            'expected': 'BEARISH'
        },
        {
            'title': 'FTX Founder Convicted of Fraud',
            'text': 'FTX Founder Convicted of Fraud - Sam Bankman-Fried found guilty on all charges of fraud and money laundering.',
            'expected': 'BEARISH'
        }
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"TEST {i}: {test['title']}")
        print(f"Expected: {test['expected']}")
        print('='*80)
        print(f"\nText: {test['text']}\n")

        # Run analysis with all three brains
        result = await engine.analyze(test['text'])

        print(f"\n📊 COUNCIL DECISION:")
        print(f"   Label:      {result['label'].upper()}")
        print(f"   Score:      {result['score']:.2f}")
        print(f"   Confidence: {result['confidence']:.2f}")
        print(f"   Impact:     {result.get('impact', 'N/A')}/10")
        print(f"   Reasoning:  {result.get('reasoning', 'N/A')}")

        # Check if matches expectation
        expected_label = 'positive' if test['expected'] == 'BULLISH' else 'negative'
        match = '✅ CORRECT' if result['label'] == expected_label else '❌ MISMATCH'
        print(f"\n   {match}")

    print("\n" + "="*80)
    print("THREE BRAINS COUNCIL TEST COMPLETE")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(test_three_brains())
