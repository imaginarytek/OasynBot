
import sqlite3
import json
import csv

def analyze_30m_impact():
    conn = sqlite3.connect('data/hedgemony.db')
    c = conn.cursor()
    
    # Check total count first
    c.execute("SELECT COUNT(*) FROM curated_events WHERE sol_price_data IS NOT NULL")
    count = c.fetchone()[0]
    print(f"DEBUG: Found {count} events with price data in DB")
    
    c.execute("SELECT title, timestamp, sol_price_data FROM curated_events WHERE sol_price_data IS NOT NULL")
    events = c.fetchall()
    
    impact_data = []
    
    print("Processing events...")
    for title, ts, price_json in events:
        try:
            if not price_json: continue
            
            prices = json.loads(price_json)
            
            # Index 300 is T=0 (Event Time)
            # We want T+30m = 30*60 = 1800 seconds later.
            # Target index = 300 + 1800 = 2100
            
            if len(prices) > 2100:
                p_start = prices[300]['close'] # Close price at T=0
                p_end = prices[2100]['close']  # Close price at T+30m
                
                pct_move = ((p_end - p_start) / p_start) * 100
                
                impact_data.append({
                    'Title': title,
                    'Date': ts[:10],
                    'Move_Pct': pct_move,
                    'Abs_Move': abs(pct_move),
                })
        except Exception as e:
            print(f"Error processing {title}: {e}")
            continue
            
    # Sort by Absolute Move (Magnitude) DESC
    impact_data.sort(key=lambda x: x['Abs_Move'], reverse=True)
    
    # Calculate Text Stats
    c.execute("SELECT length(description) FROM curated_events")
    lengths = c.fetchall()
    avg_len = sum(l[0] for l in lengths if l[0]) / len(lengths)
    
    print(f"\n✅ DATASET VERIFIED: {len(lengths)} Events. Avg Text Length: {avg_len:.0f} chars.")
    print("\n🏆 TOP 30 SOLANA MOVERS (30-Minute Impact)")
    print("=" * 80)
    print(f"{'RANK':<5} | {'DATE':<12} | {'MOVE %':<10} | {'EVENT TITLE'}")
    print("-" * 80)
    
    top_30 = impact_data[:30]
    for i, row in enumerate(top_30, 1):
        move_str = f"{row['Move_Pct']:+.2f}%"
        print(f"{i:<5} | {row['Date']:<12} | {move_str:<10} | {row['Title']}")
        
    print("=" * 80)
    
    # Save to CSV
    with open("data/top_30_impact_events.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["Rank", "Date", "Move_Pct", "Title"])
        writer.writeheader()
        for i, row in enumerate(top_30, 1):
            writer.writerow({
                "Rank": i,
                "Date": row['Date'],
                "Move_Pct": f"{row['Move_Pct']:.2f}%",
                "Title": row['Title']
            })
            
    print(f"\nSaved top 30 list to data/top_30_impact_events.csv")
    conn.close()

if __name__ == "__main__":
    analyze_30m_impact()
