import sqlite3
import logging

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def heuristic_score(text):
    if not text: return 0, 0, 5
    text = text.lower()
    score = 0
    
    # Bullish Terms (0.3 impact each)
    bulls = ['approved', 'increased', 'beat', 'gain', 'rose', 'cut rates', 'cooling', 'victory', 'accumul', 'listing', 'surge', 'jump', 'green']
    # Bearish Terms (-0.3 impact each)
    bears = ['miss', 'decreased', 'crash', 'investigation', 'shutdown', 'suspended', 'loss', 'hike', 'hotter', 'plunge', 'red', 'fear']
    
    for w in bulls: 
        if w in text: score += 0.3
    for w in bears: 
        if w in text: score -= 0.3
        
    score = max(-0.99, min(0.99, score))
    
    # Calculate Impact (Simple length/keyword heuristic)
    impact = 7
    if 'crash' in text or 'surge' in text: impact = 9
    if 'shutdown' in text: impact = 10
    
    return score, 0.85, impact

def score_all_events_simple():
    conn = sqlite3.connect('data/hedgemony.db')
    c = conn.cursor()
    
    # Check cols
    try:
        c.execute("ALTER TABLE curated_events ADD COLUMN ai_score REAL")
    except: pass
    try:
        c.execute("ALTER TABLE curated_events ADD COLUMN ai_confidence REAL")
    except: pass
    try:
        c.execute("ALTER TABLE curated_events ADD COLUMN impact_score INTEGER")
    except: pass
    
    c.execute("SELECT rowid, title, description FROM curated_events")
    rows = c.fetchall()
    
    print(f"📋 Found {len(rows)} events to score (Heuristic Mode).")
    
    updates = []
    for r in rows:
        rowid = r[0]
        title = r[1]
        text = r[2]
        
        score, conf, impact = heuristic_score(text)
        updates.append((score, conf, impact, rowid))
        
        # print(f"Scored {title}: {score:.2f}")
        
    c.executemany("UPDATE curated_events SET ai_score=?, ai_confidence=?, impact_score=? WHERE rowid=?", updates)
    conn.commit()
    conn.close()
    
    print(f"✅ Successfully updated {len(updates)} events.")

if __name__ == "__main__":
    score_all_events_simple()
