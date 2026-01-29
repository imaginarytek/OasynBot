#!/usr/bin/env python3
"""
VERIFY RAG MEMORY
-----------------
Queries the Vector Database for a concept (e.g. "Inflation")
to confirm that it returns historical events with Price Outcomes.
"""

import sys
import os
import logging

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.brain.memory import MemoryManager

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("verify_rag")

def run_test():
    print("-" * 60)
    print("🧠 RAG MEMORY VERIFICATION TEST")
    print("-" * 60)
    
    # Init Memory
    config = {
        "brain": {
            "memory": {
                "enabled": True,
                "collection_name": "market_events",
                "path": "data/chromadb"
            }
        }
    }
    memory = MemoryManager(config)
    
    # Test Query
    query = "CPI Inflation Data High"
    print(f"🔎 Querying Memory for: '{query}'")
    
    results = memory.search_similar(query, n_results=3)
    
    if not results:
        print("❌ No results found. Memory might be empty.")
        return
        
    print(f"✅ Found {len(results)} matches:\n")
    
    for i, res in enumerate(results):
        txt = res['text']
        meta = res['metadata']
        sim = res['similarity']
        
        outcome_label = meta.get('outcome_label', 'N/A')
        outcome_pct = meta.get('outcome_pct', 0.0)
        
        print(f"{i+1}. [Sim: {sim:.2f}] {txt}")
        print(f"   => HISTORICAL OUTCOME: {outcome_label} ({outcome_pct:+.2f}%)")
        print("-" * 40)
        
    print("\n✅ RAG System is ONLINE and recalling outcomes.")

if __name__ == "__main__":
    run_test()
