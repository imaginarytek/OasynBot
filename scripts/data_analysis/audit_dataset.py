#!/usr/bin/env python3
"""
CURATED EVENTS DATASET AUDIT
Comprehensive analysis of data quality, correlation, and optimization status
"""
import sqlite3
import json
from datetime import datetime, timedelta
import statistics

def audit_dataset():
    conn = sqlite3.connect('data/hedgemony.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    print("=" * 100)
    print("CURATED EVENTS DATASET AUDIT REPORT")
    print("=" * 100)
    
    # 1. BASIC STATS
    c.execute("SELECT COUNT(*) FROM curated_events")
    total_events = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM curated_events WHERE sol_price_data IS NOT NULL")
    events_with_price = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM curated_events WHERE description IS NOT NULL AND length(description) > 200")
    events_with_rich_text = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM curated_events WHERE ai_score IS NOT NULL")
    events_with_sentiment = c.fetchone()[0]
    
    print(f"\n📊 DATASET OVERVIEW")
    print(f"   Total Events: {total_events}")
    print(f"   Events with Price Data: {events_with_price} ({events_with_price/total_events*100:.1f}%)")
    print(f"   Events with Rich Text (>200 chars): {events_with_rich_text} ({events_with_rich_text/total_events*100:.1f}%)")
    print(f"   Events with AI Sentiment: {events_with_sentiment} ({events_with_sentiment/total_events*100:.1f}%)")
    
    # 2. PRICE DATA QUALITY AUDIT
    print(f"\n📈 PRICE DATA QUALITY AUDIT")
    c.execute("SELECT title, timestamp, sol_price_data FROM curated_events WHERE sol_price_data IS NOT NULL")
    price_events = c.fetchall()
    
    resolution_1s = 0
    resolution_1m = 0
    resolution_unknown = 0
    candle_counts = []
    time_ranges = []
    
    for event in price_events:
        try:
            price_data = json.loads(event['sol_price_data'])
            if not price_data or len(price_data) < 2:
                resolution_unknown += 1
                continue
                
            candle_counts.append(len(price_data))
            
            # Check resolution
            t1 = datetime.fromisoformat(price_data[0]['timestamp'].replace('Z', '+00:00'))
            t2 = datetime.fromisoformat(price_data[1]['timestamp'].replace('Z', '+00:00'))
            diff = (t2 - t1).total_seconds()
            
            if diff <= 1.5:
                resolution_1s += 1
            elif diff <= 65:
                resolution_1m += 1
            else:
                resolution_unknown += 1
                
            # Time range
            t_first = datetime.fromisoformat(price_data[0]['timestamp'].replace('Z', '+00:00'))
            t_last = datetime.fromisoformat(price_data[-1]['timestamp'].replace('Z', '+00:00'))
            time_ranges.append((t_last - t_first).total_seconds())
            
        except Exception as e:
            resolution_unknown += 1
            
    print(f"   1-Second Resolution: {resolution_1s} events ({resolution_1s/events_with_price*100:.1f}%)")
    print(f"   1-Minute Resolution: {resolution_1m} events ({resolution_1m/events_with_price*100:.1f}%)")
    print(f"   Unknown/Invalid: {resolution_unknown} events")
    
    if candle_counts:
        print(f"\n   Candle Statistics:")
        print(f"      Average Candles per Event: {statistics.mean(candle_counts):.0f}")
        print(f"      Min Candles: {min(candle_counts)}")
        print(f"      Max Candles: {max(candle_counts)}")
        
    if time_ranges:
        print(f"\n   Time Coverage Statistics:")
        print(f"      Average Duration: {statistics.mean(time_ranges)/60:.1f} minutes")
        print(f"      Min Duration: {min(time_ranges)/60:.1f} minutes")
        print(f"      Max Duration: {max(time_ranges)/60:.1f} minutes")
    
    # 3. TEXT QUALITY AUDIT
    print(f"\n📝 VERBATIM TEXT QUALITY AUDIT")
    c.execute("SELECT title, length(description) as len FROM curated_events WHERE description IS NOT NULL ORDER BY len")
    text_data = c.fetchall()
    
    if text_data:
        lengths = [row['len'] for row in text_data]
        print(f"   Average Text Length: {statistics.mean(lengths):.0f} characters")
        print(f"   Median Text Length: {statistics.median(lengths):.0f} characters")
        print(f"   Shortest Text: {min(lengths)} chars")
        print(f"   Longest Text: {max(lengths)} chars")
        
        # Show shortest events
        print(f"\n   ⚠️  Events with Short Text (<300 chars):")
        short_events = [row for row in text_data if row['len'] < 300]
        for event in short_events[:5]:
            print(f"      - {event['title']}: {event['len']} chars")
        if len(short_events) > 5:
            print(f"      ... and {len(short_events)-5} more")
    
    # 4. CORRELATION ANALYSIS
    print(f"\n🎯 PRICE CORRELATION ANALYSIS")
    c.execute("""
        SELECT title, timestamp, sol_price_data 
        FROM curated_events 
        WHERE sol_price_data IS NOT NULL
    """)
    
    moves_5s = []
    moves_30s = []
    moves_5m = []
    moves_30m = []
    
    for event in c.fetchall():
        try:
            price_data = json.loads(event['sol_price_data'])
            if len(price_data) < 2:
                continue
                
            start_price = price_data[0]['close']
            
            # Calculate moves at different intervals
            if len(price_data) >= 5:
                price_5s = price_data[4]['close']
                moves_5s.append(abs((price_5s - start_price) / start_price * 100))
                
            if len(price_data) >= 30:
                price_30s = price_data[29]['close']
                moves_30s.append(abs((price_30s - start_price) / start_price * 100))
                
            if len(price_data) >= 300:
                price_5m = price_data[299]['close']
                moves_5m.append(abs((price_5m - start_price) / start_price * 100))
                
            if len(price_data) >= 1800:
                price_30m = price_data[1799]['close']
                moves_30m.append(abs((price_30m - start_price) / start_price * 100))
                
        except Exception as e:
            continue
    
    if moves_5s:
        print(f"   5-Second Moves:")
        print(f"      Average: {statistics.mean(moves_5s):.3f}%")
        print(f"      Median: {statistics.median(moves_5s):.3f}%")
        print(f"      Max: {max(moves_5s):.3f}%")
        
    if moves_30s:
        print(f"\n   30-Second Moves:")
        print(f"      Average: {statistics.mean(moves_30s):.3f}%")
        print(f"      Median: {statistics.median(moves_30s):.3f}%")
        print(f"      Max: {max(moves_30s):.3f}%")
        
    if moves_5m:
        print(f"\n   5-Minute Moves:")
        print(f"      Average: {statistics.mean(moves_5m):.3f}%")
        print(f"      Median: {statistics.median(moves_5m):.3f}%")
        print(f"      Max: {max(moves_5m):.3f}%")
        
    if moves_30m:
        print(f"\n   30-Minute Moves:")
        print(f"      Average: {statistics.mean(moves_30m):.3f}%")
        print(f"      Median: {statistics.median(moves_30m):.3f}%")
        print(f"      Max: {max(moves_30m):.3f}%")
    
    # 5. OPTIMIZATION STATUS
    print(f"\n🔧 OPTIMIZATION STATUS")
    
    issues = []
    
    if events_with_price < total_events:
        issues.append(f"❌ {total_events - events_with_price} events missing price data")
        
    if events_with_rich_text < total_events:
        issues.append(f"❌ {total_events - events_with_rich_text} events have insufficient text (<200 chars)")
        
    if events_with_sentiment < total_events:
        issues.append(f"❌ {total_events - events_with_sentiment} events missing AI sentiment scores")
        
    if resolution_1m > 0:
        issues.append(f"⚠️  {resolution_1m} events using 1-minute data (not optimal for high-frequency)")
        
    if resolution_unknown > 0:
        issues.append(f"⚠️  {resolution_unknown} events have invalid/unknown price data")
    
    if not issues:
        print("   ✅ DATASET FULLY OPTIMIZED")
        print("   All events have:")
        print("      - 1-second price resolution")
        print("      - Rich verbatim text (>200 chars)")
        print("      - AI sentiment scores")
    else:
        print("   Issues Found:")
        for issue in issues:
            print(f"      {issue}")
    
    # 6. RECOMMENDATIONS
    print(f"\n💡 RECOMMENDATIONS")
    
    if resolution_1s == events_with_price and events_with_rich_text == total_events and events_with_sentiment == total_events:
        print("   ✅ Dataset is production-ready")
        print("   ✅ All critical optimizations complete")
        print("   ✅ Ready for live trading deployment")
    else:
        if resolution_1m > 0:
            print("   🔄 Re-fetch price data for 1-minute resolution events to get 1-second data")
        if events_with_rich_text < total_events:
            print("   📝 Expand verbatim text for events with <200 characters")
        if events_with_sentiment < total_events:
            print("   🧠 Run sentiment scoring on remaining events")
    
    print("\n" + "=" * 100)
    
    conn.close()

if __name__ == "__main__":
    audit_dataset()
