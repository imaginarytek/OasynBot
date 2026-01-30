#!/usr/bin/env python3
"""
Dataset Comparison & Quality Report
Shows side-by-side comparison of all event datasets
"""
import sqlite3
from datetime import datetime

def analyze_dataset(cursor, table_name, description):
    """Analyze a single dataset table"""
    print(f"\n{'='*100}")
    print(f"📊 {table_name.upper()}: {description}")
    print(f"{'='*100}")
    
    # Get count
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    print(f"Total Events: {count}")
    
    if count == 0:
        print("   (Empty table)")
        return
    
    # Check for price data (handle different column names)
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE sol_price_data IS NOT NULL AND sol_price_data != ''")
        with_price_data = cursor.fetchone()[0]
        print(f"With Price Data: {with_price_data}/{count} ({with_price_data/count*100:.1f}%)")
    except sqlite3.OperationalError:
        # Column doesn't exist in this table
        print(f"With Price Data: N/A (not applicable for this table)")
    
    # Check for AI scores
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE ai_score IS NOT NULL")
        with_ai = cursor.fetchone()[0]
        print(f"With AI Scores: {with_ai}/{count} ({with_ai/count*100:.1f}%)")
    except:
        print(f"With AI Scores: N/A (column doesn't exist)")
    
    # Date range
    try:
        cursor.execute(f"SELECT MIN(timestamp), MAX(timestamp) FROM {table_name} WHERE timestamp IS NOT NULL")
        result = cursor.fetchone()
        if result and result[0] and result[1]:
            min_date, max_date = result
            print(f"Date Range: {min_date[:10]} to {max_date[:10]}")
    except:
        try:
            cursor.execute(f"SELECT MIN(datetime), MAX(datetime) FROM {table_name} WHERE datetime IS NOT NULL")
            result = cursor.fetchone()
            if result and result[0] and result[1]:
                min_date, max_date = result
                print(f"Date Range: {min_date[:10]} to {max_date[:10]}")
        except:
            pass
    
    # Sample events
    print(f"\n📋 Sample Events (first 5):")
    try:
        cursor.execute(f"SELECT title, timestamp FROM {table_name} LIMIT 5")
        for i, (title, ts) in enumerate(cursor.fetchall(), 1):
            ts_str = ts[:10] if ts else 'N/A'
            print(f"   {i}. {title[:60]} ({ts_str})")
    except:
        try:
            cursor.execute(f"SELECT news_event, datetime FROM {table_name} WHERE news_event IS NOT NULL LIMIT 5")
            for i, (title, ts) in enumerate(cursor.fetchall(), 1):
                ts_str = ts[:10] if ts else 'N/A'
                print(f"   {i}. {title[:60]} ({ts_str})")
        except:
            print("   (Unable to display sample events)")


def main():
    print("="*100)
    print("🔍 DATASET COMPARISON & QUALITY REPORT")
    print("="*100)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    conn = sqlite3.connect('data/hedgemony.db')
    c = conn.cursor()
    
    # Dataset 1: Original Curated Events
    analyze_dataset(c, 'curated_events', 
                   '🔴 Level 0 - Original hand-picked events (ARCHIVE)')
    
    # Dataset 2: Gold Events
    analyze_dataset(c, 'gold_events', 
                   '🟡 Level 1 - Verified but low-impact events (KEEP FOR TESTING)')
    
    # Dataset 3: Optimized Events
    analyze_dataset(c, 'optimized_events', 
                   '🟢 Level 2 - Spike-first methodology (ACTIVE DEVELOPMENT)')
    
    # Dataset 4: Volatility Spikes
    analyze_dataset(c, 'hourly_volatility_spikes', 
                   '🔵 Level 3 - Raw detected spikes (RESEARCH SOURCE)')
    
    # Summary comparison
    print(f"\n{'='*100}")
    print("📊 SUMMARY COMPARISON")
    print(f"{'='*100}\n")
    
    c.execute("SELECT COUNT(*) FROM curated_events")
    curated_count = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM gold_events")
    gold_count = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM optimized_events")
    optimized_count = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM hourly_volatility_spikes WHERE verified = 1")
    verified_spikes = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM hourly_volatility_spikes")
    total_spikes = c.fetchone()[0]
    
    print(f"{'Dataset':<30} | {'Count':<8} | {'Quality':<15} | {'Status':<20}")
    print("-" * 100)
    print(f"{'curated_events':<30} | {curated_count:<8} | {'🔴 Mixed':<15} | {'Archive only':<20}")
    print(f"{'gold_events':<30} | {gold_count:<8} | {'🟡 Good':<15} | {'Keep for testing':<20}")
    print(f"{'optimized_events':<30} | {optimized_count:<8} | {'🟢 High':<15} | {'Active development':<20}")
    print(f"{'hourly_volatility_spikes':<30} | {f'{verified_spikes}/{total_spikes}':<8} | {'🔵 Raw':<15} | {'Research source':<20}")
    
    print(f"\n{'='*100}")
    print("💡 RECOMMENDATIONS")
    print(f"{'='*100}\n")
    
    print("1. 🎯 For Strategy Development:")
    print(f"   Use: gold_events ({gold_count} events)")
    print(f"   Why: Large sample size, verified quality\n")
    
    print("2. 🚀 For High-Impact Validation:")
    print(f"   Use: optimized_events ({optimized_count} events)")
    print(f"   Why: Major market movers, spike-first methodology")
    print(f"   Action Needed: Refine timestamps, verify 16 more events\n")
    
    print("3. 🔬 For Finding New Events:")
    print(f"   Use: hourly_volatility_spikes ({total_spikes - verified_spikes} unverified)")
    print(f"   Why: Comprehensive volatility detection")
    print(f"   Process: Research → Verify → Add to optimized_events\n")
    
    print("4. 📚 For Learning/Comparison:")
    print(f"   Use: curated_events ({curated_count} events)")
    print(f"   Why: Shows evolution of methodology")
    print(f"   Purpose: Prove spike-first is better\n")
    
    conn.close()
    
    print(f"{'='*100}")
    print("✅ Report Complete")
    print(f"{'='*100}\n")

if __name__ == "__main__":
    main()
