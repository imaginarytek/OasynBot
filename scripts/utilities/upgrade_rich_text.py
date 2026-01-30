#!/usr/bin/env python3
"""
Upgrade event descriptions to 'Rich Verbatim' (Headlines + Full Paragraphs)
"""
import sqlite3

# Format: Title -> "HEADLINE\n\nBODY_TEXT"
RICH_TEXT_UPDATES = {
    "SEC Twitter Hack - Fake Bitcoin ETF Approval": 
        "HEADLINE: @SECGov Account Compromised: Fake Approval Tweet\n\nThe SEC has approved the listing and trading of spot bitcoin ETFs. [This tweet was posted from the compromised @SECGov account and was not authorized by the SEC. The unauthorized access was terminated shortly after the tweet was posted.]",

    "Bitcoin Spot ETF Approved by SEC":
        "HEADLINE: Statement on the Approval of Spot Bitcoin Exchange-Traded Products\n\nToday, the Commission approved the listing and trading of a number of spot bitcoin exchange-traded product (ETP) shares. I have often said that the Commission acts within the law and how the courts interpret the law. Beginning under Chair Jay Clayton in 2018 and through March 2023, the Commission disapproved more than 20 exchange rule filings for spot bitcoin ETPs.",

    "Bitcoin ETF Trading Begins":
        "HEADLINE: Spot Bitcoin ETFs Begin Trading on Major U.S. Exchanges\n\nSpot Bitcoin ETFs began trading today across major U.S. exchanges including NYSE, Nasdaq, and CBOE. Trading volumes exceeded $4.6 billion on the first day, with Grayscale's GBTC, BlackRock's IBIT, and Fidelity's FBTC leading the activity. This marks the first time U.S. investors can access Bitcoin exposure through regulated brokerage accounts.",

    "Bitcoin Halving":
        "HEADLINE: Bitcoin Network Completes Fourth Halving Event\n\nBitcoin's fourth halving event has been successfully executed at block height 840,000. The block subsidy reward for miners has been reduced from 6.25 BTC to 3.125 BTC per block. This programmatic monetary policy update occurs approximately every four years and is designed to control the issuance of new supply.",

    "Roaring Kitty Returns to Twitter":
        "HEADLINE: 'Roaring Kitty' Posts for First Time in Three Years\n\nKeith Gill, known online as Roaring Kitty and DeepFuckingValue, posted on X (formerly Twitter) for the first time since 2021. The post contained no text, only an image of a video game player leaning forward in their chair, properly signaling focused attention. GameStop (GME) shares spiked immediately following the post.",
        
    "GameStop Meme Stock Rally":
        "HEADLINE: GameStop Shares Halted for Volatility Amid Meme Rally\n\nGameStop Corp. (GME) shares triggered multiple volatility trading halts today, surging over 70% in pre-market trading. The rally follows the return of 'Roaring Kitty' to social media. Other meme stocks including AMC Entertainment likewise saw significant price appreciation in sympathetic movement.",

    "Ethereum ETF Trading Begins":
        "HEADLINE: Spot Ethereum ETFs Launch on U.S. Markets\n\nSpot Ethereum exchange-traded funds (ETFs) have begun trading on U.S. exchanges today following SEC effective approval. The products from issuers including BlackRock, Fidelity, and Grayscale allow direct exposure to Ether through traditional brokerage accounts. This follows the unexpected approval of 19b-4 filings in May.",

    "Trump Election Called":
        "HEADLINE: Donald Trump Wins 2024 Presidential Election\n\nDonald Trump has won the 2024 presidential election, securing the necessary 270 electoral votes to defeat Vice President Kamala Harris. The Associated Press called the race after Trump secured key battleground states including Pennsylvania and Wisconsin. Markets have reacted with a surge in dollar strength and crypto assets.",
        
    "Fed December Rate Cut":
         "HEADLINE: Federal Reserve Issues FOMC Statement\n\nRecent indicators suggest that economic activity has continued to expand at a solid pace. Job gains have slowed, and the unemployment rate has moved up but remains low. Inflation has made progress toward the Committee's 2 percent objective but remains somewhat elevated.\n\nThe Committee decided to lower the target range for the federal funds rate by 1/4 percentage point to 4-1/4 to 4-1/2 percent."
}

def upgrade_text():
    conn = sqlite3.connect("data/hedgemony.db")
    c = conn.cursor()
    
    updated = 0
    for title, full_text in RICH_TEXT_UPDATES.items():
        c.execute("UPDATE curated_events SET description = ? WHERE title = ?", (full_text, title))
        if c.rowcount > 0:
            print(f"✅ Upgraded text for: {title}")
            updated += 1
            
    conn.commit()
    conn.close()
    print(f"\nTotal events upgraded: {updated}")

if __name__ == "__main__":
    upgrade_text()
