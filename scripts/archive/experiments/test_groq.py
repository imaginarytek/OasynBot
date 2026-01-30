#!/usr/bin/env python3
"""
Test Groq Integration (with Fallback)
"""
import sys
import os
import logging
from dotenv import load_dotenv

# Load env immediately
load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_groq")

import yaml
from src.brain.sentiment import SentimentEngine

def load_config():
    with open("config/config.yaml", "r") as f:
        return yaml.safe_load(f)

def main():
    print("🧠 Testing Sentiment Engine (Dual Core)...")
    
    # Load Config
    config = load_config()
    
    # Initialize Engine
    engine = SentimentEngine(config)
    
    print(f"Active Model Config: {engine.model_type}")
    
    # Test Data
    test_headline = "Trump announces immediate 25% tariffs on all imports from China, markets tumble."
    print(f"\nAnalyzing: '{test_headline}'")
    
    # Run Analysis
    result = engine.analyze(test_headline)
    
    print("\n✅ Result:")
    print(f"Label: {result['label'].upper()}")
    print(f"Score: {result['score']:.2f}")
    print(f"Impact: {result.get('impact')}/10")
    print(f"Reasoning: {result.get('reasoning')}")
    
    # Check if we used Groq or FinBERT
    if "FinBERT" in result.get('reasoning', ''):
        print("\n⚠️  Used FINBERT (Fallback Mode). Did you set GROQ_API_KEY?")
    else:
        print("\n🚀 Used GROQ (Llama-3).")

if __name__ == "__main__":
    main()
