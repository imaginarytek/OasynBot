#!/usr/bin/env python3
"""
Test Dynamic Settings
"""

import sys
import os
import time

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.settings import SettingsManager

def main():
    print("🧪 Testing Dynamic Settings...")
    
    # 1. Initialize Manager
    settings = SettingsManager()
    
    # 2. Read Default
    leverage = settings.get("trading.risk.max_leverage", 1)
    print(f"Current Leverage: {leverage}x")
    
    # 3. Change Setting
    print("Updating leverage to 10x...")
    settings.set("trading.risk.max_leverage", 10)
    
    # 4. Verify Update Persistence
    settings.reload()
    new_leverage = settings.get("trading.risk.max_leverage") 
    print(f"New Leverage: {new_leverage}x")
    
    if new_leverage == 10:
        print("✅ SUCCESS: Settings updated correctly")
    else:
        print("❌ FAILURE: Settings did not update")
        
    # Reset
    print("Resetting to 1x...")
    settings.set("trading.risk.max_leverage", 1)

if __name__ == "__main__":
    main()
