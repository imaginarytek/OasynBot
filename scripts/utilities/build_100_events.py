"""
CURATED 100 EVENT DATASET - SYSTEMATIC BUILDER
This script will help us build and verify the 100-event dataset
"""

# Key events identified from research:

EVENTS_2024 = [
    # JANUARY - Bitcoin ETF Saga
    {"date": "2024-01-09", "time": "21:11:00", "title": "SEC Twitter Hack - Fake BTC ETF Approval", "source": "@SECGov", "tier1": True},
    {"date": "2024-01-10", "time": "21:30:00", "title": "Bitcoin Spot ETF Approved", "source": "SEC.gov", "tier1": True},
    {"date": "2024-01-11", "time": "14:30:00", "title": "Bitcoin ETF Trading Begins", "source": "NYSE/NASDAQ", "tier1": True},
    
    # FEBRUARY - Network & Inflation
    {"date": "2024-02-06", "time": "TBD", "title": "Solana Network Outage (5+ hours)", "source": "Solana Status", "tier1": True},
    {"date": "2024-02-13", "time": "13:30:00", "title": "CPI Report - Hotter Than Expected", "source": "BLS", "tier1": True},
    {"date": "2024-02-21", "time": "19:00:00", "title": "FOMC Minutes Release", "source": "Federal Reserve", "tier1": True},
    
    # MARCH - Meme Coin Mania
    {"date": "2024-03-11", "time": "06:58:00", "title": "BOME Whale Accumulation Detected", "source": "On-chain", "tier1": True},
    {"date": "2024-03-16", "time": "10:00:00", "title": "Binance Lists BOME", "source": "Binance", "tier1": True},
    {"date": "2024-03-20", "time": "TBD", "title": "SOL Hits $200 (First Time Since 2021)", "source": "Market Data", "tier1": True},
    
    # APRIL - Bitcoin Halving
    {"date": "2024-04-20", "time": "00:09:00", "title": "Bitcoin Halving (Block 840,000)", "source": "Bitcoin Blockchain", "tier1": True},
    
    # MAY - ETH ETF & Meme Stocks
    {"date": "2024-05-12", "time": "00:00:00", "title": "Roaring Kitty Returns", "source": "@TheRoaringKitty", "tier1": True},
    {"date": "2024-05-20", "time": "TBD", "title": "ETH ETF Approval Rumors", "source": "Bloomberg", "tier1": True},
    {"date": "2024-05-23", "time": "20:58:00", "title": "Ethereum ETF Approved", "source": "SEC.gov", "tier1": True},
    
    # JUNE - Market Correction
    {"date": "2024-06-12", "time": "12:30:00", "title": "CPI Cooling - Rate Cut Hopes", "source": "BLS", "tier1": True},
    {"date": "2024-06-18", "time": "TBD", "title": "SOL Crashes Below $130 (-39%)", "source": "Market Data", "tier1": True},
    
    # JULY - Institutional Adoption
    {"date": "2024-07-09", "time": "14:00:00", "title": "Powell Dovish Testimony", "source": "Federal Reserve", "tier1": True},
    {"date": "2024-07-15", "time": "TBD", "title": "Hamilton Lane Launches Private Credit Fund on Solana", "source": "Hamilton Lane", "tier1": True},
    {"date": "2024-07-31", "time": "03:00:00", "title": "Bank of Japan Rate Hike", "source": "BoJ", "tier1": True},
    
    # AUGUST - Carry Trade Unwind
    {"date": "2024-08-05", "time": "00:00:00", "title": "Nikkei 225 Crashes 12%", "source": "TSE", "tier1": True},
    {"date": "2024-08-23", "time": "14:00:00", "title": "Powell Jackson Hole Speech", "source": "Federal Reserve", "tier1": True},
    
    # SEPTEMBER - Rate Cuts Begin
    {"date": "2024-09-18", "time": "18:00:00", "title": "Fed Cuts Rates 50bps", "source": "Federal Reserve", "tier1": True},
    
    # OCTOBER - Pre-Election Rally
    {"date": "2024-10-04", "time": "12:30:00", "title": "Jobs Report Miss", "source": "BLS", "tier1": True},
    
    # NOVEMBER - Trump Victory
    {"date": "2024-11-06", "time": "10:34:00", "title": "Trump Election Called", "source": "Associated Press", "tier1": True},
    {"date": "2024-11-14", "time": "TBD", "title": "Trump Announces Pro-Crypto Cabinet", "source": "Truth Social", "tier1": True},
    {"date": "2024-11-23", "time": "TBD", "title": "SOL Hits All-Time High $263", "source": "Market Data", "tier1": True},
    
    # DECEMBER - Year-End
    {"date": "2024-12-05", "time": "TBD", "title": "Bitcoin Breaks $100K", "source": "Market Data", "tier1": True},
    {"date": "2024-12-18", "time": "19:00:00", "title": "Fed December Rate Cut", "source": "Federal Reserve", "tier1": True},
]

EVENTS_2025 = [
    # JANUARY - Trump Inauguration
    {"date": "2025-01-20", "time": "17:00:00", "title": "Trump Inauguration", "source": "Official Ceremony", "tier1": True},
    {"date": "2025-01-23", "time": "TBD", "title": "Trump Signs Crypto Executive Order", "source": "White House", "tier1": True},
    
    # MARCH - Crypto Reserve
    {"date": "2025-03-02", "time": "12:24:00", "title": "Trump Announces U.S. Crypto Reserve", "source": "Truth Social", "tier1": True},
    {"date": "2025-03-07", "time": "TBD", "title": "White House Crypto Summit", "source": "White House", "tier1": True},
    
    # APRIL - SEC Policy Shift
    {"date": "2025-04-09", "time": "10:58:00", "title": "SEC Closes Ethereum Investigation", "source": "SEC.gov", "tier1": True},
]

print(f"2024 Events: {len(EVENTS_2024)}")
print(f"2025 Events: {len(EVENTS_2025)}")
print(f"Total: {len(EVENTS_2024) + len(EVENTS_2025)}")
print(f"\nNeed {50 - len(EVENTS_2024)} more 2024 events")
print(f"Need {50 - len(EVENTS_2025)} more 2025 events")
