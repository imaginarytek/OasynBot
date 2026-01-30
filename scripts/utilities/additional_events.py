# ADDITIONAL 34 EVENTS TO COMPLETE THE 100-EVENT DATASET

ADDITIONAL_EVENTS = [
    # Major Hacks 2024
    {"date": "2024-01-02", "time": "TBD", "title": "Orbit Chain Hack ($80M)", "source": "On-chain", "sentiment": "bearish"},
    {"date": "2024-02-13", "time": "TBD", "title": "PlayDapp Exploit ($32M)", "source": "On-chain", "sentiment": "bearish"},
    {"date": "2024-03-15", "time": "TBD", "title": "Munchables Hack ($62M)", "source": "On-chain", "sentiment": "bearish"},
    {"date": "2024-05-31", "time": "TBD", "title": "DMM Bitcoin Hack ($300M) - Largest 2024", "source": "DMM Bitcoin", "sentiment": "bearish"},
    {"date": "2024-07-18", "time": "TBD", "title": "WazirX Exchange Hack ($230M)", "source": "WazirX", "sentiment": "bearish"},
    {"date": "2024-10-16", "time": "TBD", "title": "Radiant Capital Hack ($51M)", "source": "On-chain", "sentiment": "bearish"},
    
    # Major Hacks 2025
    {"date": "2025-02-21", "time": "TBD", "title": "Bybit Hack ($1.4B) - Largest Ever", "source": "Bybit", "sentiment": "bearish"},
    {"date": "2025-04-15", "time": "TBD", "title": "Bitget Exploit ($100M)", "source": "Bitget", "sentiment": "bearish"},
    {"date": "2025-05-12", "time": "TBD", "title": "Cetus DEX Exploit ($223M)", "source": "On-chain", "sentiment": "bearish"},
    {"date": "2025-07-10", "time": "TBD", "title": "CoinDCX Security Breach ($44M)", "source": "CoinDCX", "sentiment": "bearish"},
    {"date": "2025-11-05", "time": "TBD", "title": "Balancer V2 Exploit ($128M)", "source": "On-chain", "sentiment": "bearish"},
    
    # Geopolitical Events 2024
    {"date": "2024-04-13", "time": "TBD", "title": "Iran-Israel Conflict Escalation", "source": "News Wires", "sentiment": "bearish"},
    {"date": "2024-10-01", "time": "TBD", "title": "Israel-Hezbollah Conflict Intensifies", "source": "News Wires", "sentiment": "bearish"},
    
    # Geopolitical Events 2025
    {"date": "2025-02-15", "time": "TBD", "title": "Russia-Ukraine Peace Talks Begin", "source": "News Wires", "sentiment": "bullish"},
    {"date": "2025-06-20", "time": "TBD", "title": "US-China Trade Deal Announced", "source": "White House", "sentiment": "bullish"},
    
    # Solana-Specific Events 2024
    {"date": "2024-01-25", "time": "TBD", "title": "Pump.fun Platform Launch", "source": "Solana Ecosystem", "sentiment": "bullish"},
    {"date": "2024-05-15", "time": "TBD", "title": "BlackRock BUIDL Fund on Solana", "source": "BlackRock", "sentiment": "bullish"},
    {"date": "2024-09-12", "time": "TBD", "title": "Securitize Adds Solana Support", "source": "Securitize", "sentiment": "bullish"},
    
    # Solana-Specific Events 2025
    {"date": "2025-01-15", "time": "TBD", "title": "Solana ETF Filings (VanEck, 21Shares)", "source": "SEC Filings", "sentiment": "bullish"},
    {"date": "2025-08-20", "time": "TBD", "title": "Solana Firedancer Testnet Launch", "source": "Jump Crypto", "sentiment": "bullish"},
    
    # Additional Economic Data 2024
    {"date": "2024-04-05", "time": "12:30:00", "title": "Jobs Report April 2024", "source": "BLS", "sentiment": "neutral"},
    {"date": "2024-05-03", "time": "12:30:00", "title": "Jobs Report May 2024", "source": "BLS", "sentiment": "neutral"},
    {"date": "2024-06-07", "time": "12:30:00", "title": "Jobs Report June 2024", "source": "BLS", "sentiment": "neutral"},
    {"date": "2024-07-05", "time": "12:30:00", "title": "Jobs Report July 2024", "source": "BLS", "sentiment": "neutral"},
    {"date": "2024-08-02", "time": "12:30:00", "title": "Jobs Report August 2024", "source": "BLS", "sentiment": "neutral"},
    {"date": "2024-09-06", "time": "12:30:00", "title": "Jobs Report September 2024", "source": "BLS", "sentiment": "neutral"},
    {"date": "2024-11-01", "time": "12:30:00", "title": "Jobs Report November 2024", "source": "BLS", "sentiment": "neutral"},
    {"date": "2024-12-06", "time": "13:30:00", "title": "Jobs Report December 2024", "source": "BLS", "sentiment": "neutral"},
    
    # Additional Economic Data 2025
    {"date": "2025-06-06", "time": "12:30:00", "title": "Jobs Report June 2025", "source": "BLS", "sentiment": "neutral"},
    {"date": "2025-07-03", "time": "12:30:00", "title": "Jobs Report July 2025", "source": "BLS", "sentiment": "neutral"},
    {"date": "2025-08-01", "time": "12:30:00", "title": "Jobs Report August 2025", "source": "BLS", "sentiment": "neutral"},
    {"date": "2025-09-05", "time": "12:30:00", "title": "Jobs Report September 2025", "source": "BLS", "sentiment": "neutral"},
    {"date": "2025-10-03", "time": "12:30:00", "title": "Jobs Report October 2025", "source": "BLS", "sentiment": "neutral"},
    {"date": "2025-11-07", "time": "13:30:00", "title": "Jobs Report November 2025", "source": "BLS", "sentiment": "neutral"},
]

print(f"Additional events: {len(ADDITIONAL_EVENTS)}")
print(f"Total with previous 66: {66 + len(ADDITIONAL_EVENTS)}")
