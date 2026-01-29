#!/usr/bin/env python3
"""
Verify Logic: Memory Manager (ChromaDB)
"""
import sys
import os
import shutil
import time

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.brain.memory import MemoryManager

def test_memory():
    print("🧠 Testing Memory Manager (ChromaDB)...")
    
    # Clean run
    persist_path = "data/chromadb_test"
    if os.path.exists(persist_path):
        shutil.rmtree(persist_path)
        
    config = {
        "brain": {
            "memory": {
                "enabled": True,
                "collection_name": "test_events",
                "path": persist_path
            }
        }
    }
    
    memory = MemoryManager(config)
    
    # 1. Add Events
    events = [
        ("Bitcoin surges after Elon Musk tweets rocket emoji", {"impact": 9, "label": "positive"}),
        ("SEC sues Coinbase over unregistered securities", {"impact": 10, "label": "negative"}),
        ("Federal Reserve keeps rates unchanged", {"impact": 5, "label": "neutral"}),
        ("China bans crypto mining again", {"impact": 10, "label": "negative"})
    ]
    
    print("Writing events to memory...")
    for text, meta in events:
        memory.add_event(text, meta)
        
    print("Waiting for persistence...")
    time.sleep(1) # Allow slight indexing time
    
    # 2. Search
    query = "Regulators crackdown on crypto exchanges"
    print(f"\n🔍 Query: '{query}'")
    
    results = memory.search_similar(query, n_results=2)
    
    print(f"Found {len(results)} matches:")
    for r in results:
        print(f" - [{r['similarity']:.3f}] {r['text']} (Impact: {r['metadata']['impact']})")
        
    # Verify Content
    if len(results) > 0 and "SEC sues" in results[0]['text']:
        print("\n✅ SUCCESS: Semantic Retrieval works (SEC lawsuit is similar to crackdown)")
    else:
        print("\n❌ FAILED: Did not retrieve expected event")

if __name__ == "__main__":
    test_memory()
