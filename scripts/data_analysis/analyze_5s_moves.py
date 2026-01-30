#!/usr/bin/env python3
"""
Analyze price movement in first 5 seconds after news for all 80 events
Rank from highest to lowest absolute price change
"""
import sqlite3
import json
import pandas as pd
from datetime import datetime, timedelta

def analyze_5s_moves():
    print("📊 ANALYZING FIRST 5-SECOND PRICE MOVES\n")
    print("="*90)
    
    conn = sqlite3.connect("data/hedgemony.db")
    c = conn.cursor()
    
    # Get all events with price data
    c.execute("""
        SELECT title, timestamp, sentiment, sol_price_data
        FROM curated_events
        WHERE sol_price_data IS NOT NULL
        ORDER BY timestamp
    """)
    
    events = c.fetchall()
    conn.close()
    
    results = []
    
    for title, ts_str, sentiment, raw_data in events:
        try:
            # Parse news time
            news_time = datetime.fromisoformat(ts_str)
            
            # Load candles
            candles = json.loads(raw_data)
            df = pd.DataFrame(candles)
            df['ts_obj'] = pd.to_datetime(df['timestamp'])
            
            # Find candle at news time
            news_candle = df[df['ts_obj'] >= news_time].iloc[0] if len(df[df['ts_obj'] >= news_time]) > 0 else None
            if news_candle is None:
                continue
            
            price_at_news = news_candle['close']
            
            # Find price 5 seconds later
            five_sec_later = news_time + timedelta(seconds=5)
            later_candles = df[df['ts_obj'] <= five_sec_later]
            
            if len(later_candles) > 0:
                price_5s = later_candles.iloc[-1]['close']
                
                # Calculate percentage change
                pct_change = ((price_5s - price_at_news) / price_at_news) * 100
                
                # Also get high and low in first 5s
                window_5s = df[(df['ts_obj'] >= news_time) & (df['ts_obj'] <= five_sec_later)]
                high_5s = window_5s['high'].max()
                low_5s = window_5s['low'].min()
                
                high_pct = ((high_5s - price_at_news) / price_at_news) * 100
                low_pct = ((low_5s - price_at_news) / price_at_news) * 100
                
                # Max absolute move
                max_abs_move = max(abs(high_pct), abs(low_pct))
                
                results.append({
                    'title': title,
                    'date': ts_str[:10],
                    'sentiment': sentiment,
                    'price_at_news': price_at_news,
                    'price_5s': price_5s,
                    'pct_change': pct_change,
                    'high_pct': high_pct,
                    'low_pct': low_pct,
                    'max_abs_move': max_abs_move,
                    'direction': 'UP' if pct_change > 0 else 'DOWN'
                })
                
        except Exception as e:
            print(f"Error processing {title}: {e}")
            continue
    
    # Create DataFrame and sort by absolute move
    df_results = pd.DataFrame(results)
    df_results = df_results.sort_values('max_abs_move', ascending=False)
    
    # Print ranked results
    print(f"{'Rank':<5} {'Event':<45} {'Date':<12} {'5s Move':<10} {'Max Move':<10} {'Dir':<5}")
    print("="*90)
    
    for idx, row in df_results.iterrows():
        rank = df_results.index.get_loc(idx) + 1
        event_short = row['title'][:43]
        
        # Color coding
        if abs(row['pct_change']) > 1.0:
            emoji = "🔥"
        elif abs(row['pct_change']) > 0.5:
            emoji = "⚡"
        elif abs(row['pct_change']) > 0.2:
            emoji = "✅"
        else:
            emoji = "📊"
        
        print(f"{rank:<5} {emoji} {event_short:<43} {row['date']:<12} {row['pct_change']:+6.2f}%   {row['max_abs_move']:6.2f}%   {row['direction']:<5}")
    
    # Statistics
    print(f"\n{'='*90}")
    print("SUMMARY STATISTICS (First 5 Seconds)")
    print(f"{'='*90}")
    print(f"Total events: {len(df_results)}")
    print(f"\nPrice Change (Close to Close):")
    print(f"  Mean: {df_results['pct_change'].mean():+.3f}%")
    print(f"  Median: {df_results['pct_change'].median():+.3f}%")
    print(f"  Std Dev: {df_results['pct_change'].std():.3f}%")
    print(f"  Max Up: {df_results['pct_change'].max():+.3f}%")
    print(f"  Max Down: {df_results['pct_change'].min():+.3f}%")
    
    print(f"\nMax Absolute Move (High/Low):")
    print(f"  Mean: {df_results['max_abs_move'].mean():.3f}%")
    print(f"  Median: {df_results['max_abs_move'].median():.3f}%")
    print(f"  Max: {df_results['max_abs_move'].max():.3f}%")
    
    print(f"\nMove Categories:")
    huge = len(df_results[df_results['max_abs_move'] > 1.0])
    large = len(df_results[(df_results['max_abs_move'] > 0.5) & (df_results['max_abs_move'] <= 1.0)])
    medium = len(df_results[(df_results['max_abs_move'] > 0.2) & (df_results['max_abs_move'] <= 0.5)])
    small = len(df_results[df_results['max_abs_move'] <= 0.2])
    
    print(f"  🔥 Huge (>1.0%): {huge} ({huge/len(df_results)*100:.1f}%)")
    print(f"  ⚡ Large (0.5-1.0%): {large} ({large/len(df_results)*100:.1f}%)")
    print(f"  ✅ Medium (0.2-0.5%): {medium} ({medium/len(df_results)*100:.1f}%)")
    print(f"  📊 Small (<0.2%): {small} ({small/len(df_results)*100:.1f}%)")
    
    print(f"\nDirection:")
    up = len(df_results[df_results['pct_change'] > 0])
    down = len(df_results[df_results['pct_change'] < 0])
    print(f"  Up: {up} ({up/len(df_results)*100:.1f}%)")
    print(f"  Down: {down} ({down/len(df_results)*100:.1f}%)")
    
    # Save results
    df_results.to_csv('data/5s_price_moves.csv', index=False)
    print(f"\n💾 Saved detailed results to: data/5s_price_moves.csv")
    print(f"{'='*90}\n")
    
    # Top 10 biggest movers
    print("🔥 TOP 10 BIGGEST 5-SECOND MOVERS:")
    print("="*90)
    for idx, row in df_results.head(10).iterrows():
        print(f"{df_results.index.get_loc(idx) + 1}. {row['title'][:60]}")
        print(f"   {row['date']} | 5s: {row['pct_change']:+.2f}% | Max: {row['max_abs_move']:.2f}% | {row['direction']}")
        print()

if __name__ == "__main__":
    analyze_5s_moves()
