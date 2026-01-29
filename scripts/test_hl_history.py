
import requests
import time
from datetime import datetime

def test_hl_history():
    print("🔬 Testing Hyperliquid Historical Data Availability...")
    
    # Target: March 2, 2025 (The Big Rally) 
    # Timestamp in ms
    target_ts = int(datetime(2025, 3, 2, 15, 0, 0).timestamp() * 1000)
    end_ts = target_ts + (60 * 60 * 1000) # +1 Hour
    
    url = "https://api.hyperliquid.xyz/info"
    headers = {'Content-Type': 'application/json'}
    
    # Correct endpoint for candles is /info with type 'candleSnapshot'
    payload = {
        "type": "candleSnapshot",
        "req": {
            "coin": "SOL",
            "interval": "1m", # Checking 1m first (1s unlikely for deep history)
            "startTime": target_ts,
            "endTime": end_ts
        }
    }
    
    try:
        r = requests.post(url, json=payload, headers=headers)
        data = r.json()
        
        if isinstance(data, list) and len(data) > 0:
            print(f"✅ SUCCESS: Retrieved {len(data)} candles.")
            print(f"Sample: {data[0]}")
            return True
        else:
            print(f"❌ FAILURE: Response empty or invalid: {data}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    test_hl_history()
