
import sqlite3
import json
import pandas as pd
from datetime import datetime, timezone, timedelta

def generate_verification_queries():
    """
    For each price impulse, generate exact search queries to find the true Tier 1 source
    """
    print("🔍 GENERATING VERIFICATION QUERIES FOR ALL EVENTS\n")
    print("="*100)
    
    conn = sqlite3.connect("data/hedgemony.db")
    c = conn.cursor()
    
    # Get all events with price data
    c.execute("""
        SELECT rowid, title, timestamp, sol_price_data 
        FROM gold_events 
        WHERE sol_price_data IS NOT NULL
        ORDER BY timestamp ASC
    """)
    
    rows = c.fetchall()
    
    verification_tasks = []
    
    for idx, row in enumerate(rows, 1):
        rowid, title, ts_str, raw_data = row
        
        try:
            candles = json.loads(raw_data)
            if len(candles) < 100:
                continue
                
            df = pd.DataFrame(candles)
            df['ts_obj'] = pd.to_datetime(df['timestamp'])
            df['price_change'] = df['close'].pct_change().abs()
            df['volume'] = pd.to_numeric(df['volume'])
            
            # Find first major spike
            df['vol_avg'] = df['volume'].rolling(60, min_periods=1).mean()
            df['vol_spike'] = df['volume'] / df['vol_avg']
            
            anomalies = df[(df['vol_spike'] > 5) | (df['price_change'] > 0.003)]
            
            if anomalies.empty:
                continue
                
            first_impulse = anomalies.iloc[0]
            impulse_time = first_impulse['ts_obj']
            
            # Generate search window: 2 minutes before impulse
            search_start = impulse_time - timedelta(minutes=2)
            search_end = impulse_time
            
            # Extract keywords from title
            keywords = []
            if "Trump" in title:
                keywords = ["Trump", "crypto", "reserve", "bitcoin", "executive order"]
            elif "Powell" in title or "Jackson" in title:
                keywords = ["Powell", "Fed", "Jackson Hole", "interest rate", "policy"]
            elif "ETF" in title:
                keywords = ["Bitcoin ETF", "SEC", "approval", "Gensler"]
            elif "Ethereum" in title:
                keywords = ["Ethereum", "ETH", "SEC", "investigation"]
            elif "Nikkei" in title:
                keywords = ["Nikkei", "Japan", "crash", "market"]
            elif "BOME" in title:
                keywords = ["BOME", "Book of Meme", "Binance", "listing", "Solana"]
            elif "Roaring Kitty" in title or "GameStop" in title:
                keywords = ["Roaring Kitty", "GameStop", "GME", "Keith Gill"]
            elif "CPI" in title or "FOMC" in title:
                keywords = ["CPI", "inflation", "FOMC", "Fed", "economic data"]
            else:
                keywords = ["Solana", "SOL", "crypto", "breaking"]
            
            task = {
                'event_id': rowid,
                'title': title,
                'current_db_timestamp': ts_str,
                'actual_impulse_time': impulse_time.strftime('%Y-%m-%d %H:%M:%S UTC'),
                'search_window_start': search_start.strftime('%Y-%m-%d %H:%M:%S UTC'),
                'search_window_end': search_end.strftime('%Y-%m-%d %H:%M:%S UTC'),
                'keywords': keywords,
                'twitter_query': f"({' OR '.join(keywords)}) since:{search_start.strftime('%Y-%m-%d_%H:%M:%S_UTC')} until:{search_end.strftime('%Y-%m-%d_%H:%M:%S_UTC')}",
                'google_query': f"{' '.join(keywords[:3])} {search_start.strftime('%B %d %Y %H:%M')} UTC",
                'price_move': f"{first_impulse['price_change']*100:.2f}%",
                'volume_spike': f"{first_impulse['vol_spike']:.1f}x"
            }
            
            verification_tasks.append(task)
            
            print(f"\n{'='*100}")
            print(f"EVENT #{idx}: {title[:70]}")
            print(f"{'='*100}")
            print(f"Current DB Timestamp:  {ts_str}")
            print(f"Actual Price Impulse:  {task['actual_impulse_time']}")
            print(f"Price Move:            {task['price_move']} | Volume Spike: {task['volume_spike']}")
            print(f"\n🔍 SEARCH WINDOW: {task['search_window_start']} → {task['search_window_end']}")
            print(f"\n📱 Twitter Advanced Search:")
            print(f"   {task['twitter_query']}")
            print(f"\n🌐 Google Search:")
            print(f"   {task['google_query']}")
            print(f"\n🎯 Keywords: {', '.join(keywords)}")
            print(f"\n📋 VERIFICATION CHECKLIST:")
            print(f"   [ ] Find earliest tweet/article in search window")
            print(f"   [ ] Verify it's from Tier 1 source (official account, Bloomberg, Reuters)")
            print(f"   [ ] Extract exact timestamp (to the second if possible)")
            print(f"   [ ] Confirm sentiment matches price direction")
            print(f"   [ ] Calculate lag: (impulse_time - news_time)")
            
        except Exception as e:
            print(f"Error processing event {title}: {e}")
            continue
    
    conn.close()
    
    # Save to file for manual research
    print(f"\n\n{'='*100}")
    print(f"SUMMARY: Generated {len(verification_tasks)} verification tasks")
    print(f"{'='*100}")
    
    # Export to JSON for easy reference
    import json as json_lib
    with open('data/verification_tasks.json', 'w') as f:
        json_lib.dump(verification_tasks, f, indent=2)
    
    print(f"\n✅ Saved verification tasks to: data/verification_tasks.json")
    print(f"\nNEXT STEPS:")
    print(f"1. For each event, use the Twitter/Google queries to find the actual news")
    print(f"2. Record the exact timestamp of the first Tier 1 mention")
    print(f"3. Update the database with the verified timestamp")
    print(f"4. Calculate final lag statistics")

if __name__ == "__main__":
    generate_verification_queries()
