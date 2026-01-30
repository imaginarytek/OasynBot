#!/usr/bin/env python3
"""
Manually populate verbatim text for crypto and political events
"""
import sqlite3

MANUAL_EVENTS = {
    "Bitcoin Halving": {
        "text": "BLOCK 840,000 MINED - BITCOIN HALVING COMPLETE. Mining reward reduced to 3.125 BTC per block."
    },
    "Roaring Kitty Returns to Twitter": {
        "text": "@TheRoaringKitty posts on X for the first time since 2021. Image depicts a gamer leaning forward in their chair, signaling high focus."
    },
    "GameStop Meme Stock Rally": {
        "text": "GameStop Corp. (GME) shares triggered volatility halt, trading up significantly following social media activity from Keith Gill (Roaring Kitty)."
    },
    "Powell Dovish Testimony": {
        "text": "POWELL: ELEVATED INFLATION IS NOT THE ONLY RISK WE FACE. CUTTING RATES TOO LATE OR TOO LITTLE COULD UNDULY WEAKEN ECONOMIC ACTIVITY AND EMPLOYMENT."
    },
    "Ethereum ETF Trading Begins": {
        "text": "Spot Ethereum ETFs have begun trading on US exchanges including Nasdaq, CBOE and NYSE Arca."
    },
    "Bank of Japan Rate Hike": {
        "text": "At the Monetary Policy Meeting, the Policy Board of the Bank of Japan decided to raise the uncollateralized overnight call rate to around 0.25 percent."
    },
    "Nikkei 225 Crashes 12%": {
        "text": "Nikkei 225 Stock Average closes down 12.4%, the worst single-day percentage drop since the 1987 Black Monday crash."
    },
    "Powell Jackson Hole Speech": {
        "text": "POWELL: THE TIME HAS COME FOR POLICY TO ADJUST. THE DIRECTION OF TRAVEL IS CLEAR, AND THE TIMING AND PACE OF RATE CUTS WILL DEPEND ON INCOMING DATA."
    },
    "Fed December Rate Cut": {
        "text": "The Committee decided to lower the target range for the federal funds rate by 1/4 percentage point to 4-1/4 to 4-1/2 percent."
    },
    "Trump Inauguration": {
        "text": "I, Donald John Trump, do solemnly swear that I will faithfully execute the Office of President of the United States."
    },
    "Binance Announces BOME Listing": {
        "text": "Binance will list Book of Meme (BOME) and open trading for strict spot trading pairs at 2024-03-16 12:30 (UTC)."
    },
    "BOME Whale Accumulation Detected": {
        "text": "ALERT: Fresh wallet accumulated 12,721 SOL ($2.3M) worth of BOME in a single transaction block."
    },
    "SEC Closes Ethereum Investigation": {
        "text": "Consensys: The Enforcement Division of the SEC has notified us that it is closing its investigation into Ethereum 2.0."
    }
}

def update_manual_events():
    conn = sqlite3.connect("data/hedgemony.db")
    c = conn.cursor()
    
    updated = 0
    
    for title, data in MANUAL_EVENTS.items():
        # Update matching titles
        c.execute("UPDATE curated_events SET description = ? WHERE title = ? AND description IS NULL", 
                 (data['text'], title))
        
        if c.rowcount > 0:
            print(f"✅ Updated: {title}")
            updated += c.rowcount
        else:
            # Check if it was already updated
            c.execute("SELECT description FROM curated_events WHERE title = ?", (title,))
            res = c.fetchone()
            if res and res[0]:
                print(f"ℹ️  Skipped: {title} (Already has text)")
            else:
                print(f"⚠️  Not Found: {title}")
                
    conn.commit()
    conn.close()
    print(f"\nUpdated {updated} manual events.")

if __name__ == "__main__":
    update_manual_events()
