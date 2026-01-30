#!/usr/bin/env python3
"""
SPIKE REALIGNMENT - Find exact spike moment within event windows
"""
import sqlite3
import json
from datetime import datetime, timedelta

def realign_events_to_spikes():
    print("=" * 100)
    print("SPIKE REALIGNMENT - Finding exact moment of maximum price action")
    print("=" * 100)
    
    conn = sqlite3.connect('data/hedgemony.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute("SELECT rowid, title, timestamp, sol_price_data FROM curated_events WHERE sol_price_data IS NOT NULL")
    events = c.fetchall()
    
    print(f"\n🔍 Analyzing {len(events)} events to find spike moments...")
    
    realignments = []
    
    for event in events:
        try:
            price_data = json.loads(event['sol_price_data'])
            
            if len(price_data) < 100:
                continue
            
            # Find maximum absolute move within first 30 minutes
            base_price = price_data[0]['close']
            max_move = 0
            max_idx = 0
            max_time = None
            
            search_window = min(1800, len(price_data))  # 30 minutes or available data
            
            for i in range(search_window):
                current_price = price_data[i]['close']
                move = abs((current_price - base_price) / base_price * 100)
                
                if move > max_move:
                    max_move = move
                    max_idx = i
                    max_time = price_data[i]['timestamp']
            
            # Calculate 30s move from spike point
            spike_price = price_data[max_idx]['close']
            move_30s_from_spike = 0
            
            if max_idx + 30 < len(price_data):
                price_30s_later = price_data[max_idx + 30]['close']
                move_30s_from_spike = abs((price_30s_later - spike_price) / spike_price * 100)
            
            original_time = datetime.fromisoformat(event['timestamp'])
            spike_time = datetime.fromisoformat(max_time.replace('Z', '+00:00'))
            time_offset = (spike_time - original_time).total_seconds()
            
            realignments.append({
                'rowid': event['rowid'],
                'title': event['title'],
                'original_time': original_time,
                'spike_time': spike_time,
                'offset_seconds': time_offset,
                'max_move': max_move,
                'spike_idx': max_idx,
                'move_30s_from_spike': move_30s_from_spike
            })
            
        except Exception as e:
            print(f"   Error processing {event['title']}: {e}")
            continue
    
    # Sort by maximum move
    realignments.sort(key=lambda x: x['max_move'], reverse=True)
    
    print(f"\n🎯 TOP 30 EVENTS BY MAXIMUM INTRA-WINDOW MOVE:")
    print(f"   {'RANK':<5} | {'EVENT':<45} | {'MAX MOVE':<10} | {'SPIKE AT':<10} | {'OFFSET':<8}")
    print("   " + "-" * 95)
    
    for i, r in enumerate(realignments[:30], 1):
        offset_str = f"{r['offset_seconds']:+.0f}s" if r['offset_seconds'] != 0 else "0s"
        spike_at_str = f"{r['spike_idx']}s"
        print(f"   {i:<5} | {r['title'][:43]:<45} | {r['max_move']:>8.2f}% | {spike_at_str:>8} | {offset_str:>6}")
    
    # Identify events where spike is significantly offset
    significant_offsets = [r for r in realignments if abs(r['offset_seconds']) > 60]
    
    print(f"\n⚠️  EVENTS WITH SIGNIFICANT TIME OFFSET (>60 seconds):")
    print(f"   Found {len(significant_offsets)} events where spike occurred {'>60s'} from event timestamp")
    
    if significant_offsets:
        print(f"\n   {'EVENT':<50} | {'OFFSET':<10} | {'MAX MOVE':<10}")
        print("   " + "-" * 75)
        for r in sorted(significant_offsets, key=lambda x: abs(x['offset_seconds']), reverse=True)[:15]:
            offset_str = f"{r['offset_seconds']:+.0f}s"
            print(f"   {r['title'][:48]:<50} | {offset_str:>8} | {r['max_move']:>8.2f}%")
    
    # Check if realignment would improve 30s moves
    improved_count = 0
    for r in realignments:
        if r['move_30s_from_spike'] > 0.5:  # Significant improvement
            improved_count += 1
    
    print(f"\n📊 REALIGNMENT IMPACT:")
    print(f"   Events with spike offset >60s: {len(significant_offsets)}")
    print(f"   Events that would show >0.5% 30s move if realigned: {improved_count}")
    
    # Recommendation
    print(f"\n💡 RECOMMENDATIONS:")
    
    if len(significant_offsets) > 20:
        print(f"   🔴 CRITICAL: {len(significant_offsets)} events have poor timestamp alignment")
        print(f"   Action: Re-fetch price data starting from spike moment, not event announcement")
        print(f"   This will capture the actual market reaction window")
    
    if improved_count < 10:
        print(f"   ⚠️  WARNING: Even with realignment, only {improved_count} events show strong 30s moves")
        print(f"   This suggests:")
        print(f"      1. SOL may not react immediately to all these events")
        print(f"      2. Some events may not be tier-1 SOL catalysts")
        print(f"      3. Consider filtering to only crypto-specific events")
    
    # Show events with best 30s reaction from spike
    best_reactions = sorted(realignments, key=lambda x: x['move_30s_from_spike'], reverse=True)[:10]
    
    if best_reactions:
        print(f"\n✅ EVENTS WITH STRONGEST 30s REACTION FROM SPIKE:")
        print(f"   {'EVENT':<50} | {'30s MOVE':<10}")
        print("   " + "-" * 65)
        for r in best_reactions:
            print(f"   {r['title'][:48]:<50} | {r['move_30s_from_spike']:>8.3f}%")
    
    print("\n" + "=" * 100)
    
    conn.close()
    return realignments

if __name__ == "__main__":
    results = realign_events_to_spikes()
    
    print(f"\n📋 SUMMARY:")
    print(f"   Total events analyzed: {len(results)}")
    print(f"   Average spike offset: {sum(abs(r['offset_seconds']) for r in results) / len(results):.0f} seconds")
    print(f"   Maximum spike offset: {max(abs(r['offset_seconds']) for r in results):.0f} seconds")
