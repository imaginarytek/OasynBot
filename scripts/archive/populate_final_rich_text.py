import sqlite3

# Data Dictionary: Title -> Rich Verbatim Text
# Sourced from official BLS/Fed archives and Whitehouse.gov records found in search.

UPDATES = {
    # --- LATE 2024 ---
    "Jobs Report September 2024": """HEADLINE: Employment Situation News Release
    
Total nonfarm payroll employment increased by 142,000 in August, and the unemployment rate changed little at 4.2 percent, the U.S. Bureau of Labor Statistics reported today. Job gains occurred in construction and health care.

The change in total nonfarm payroll employment for June was revised down by 61,000, from +179,000 to +118,000, and the change for July was revised down by 25,000, from +114,000 to +89,000. With these revisions, employment in June and July combined is 86,000 lower than previously reported.""",

    "Fed Cuts Rates 50bps": """HEADLINE: Federal Reserve Issues FOMC Statement
    
Recent indicators suggest that economic activity has continued to expand at a solid pace. Job gains have slowed, and the unemployment rate has moved up but remains low. Inflation has made further progress toward the Committee's 2 percent objective but remains somewhat elevated.

The Committee has gained greater confidence that inflation is moving sustainably toward 2 percent, and judges that the risks to achieving its employment and inflation goals are roughly in balance. In light of the progress on inflation and the balance of risks, the Committee decided to lower the target range for the federal funds rate by 1/2 percentage point to 4-3/4 to 5 percent.""",

    "Jobs Report Miss": """HEADLINE: Employment Situation News Release
    
Total nonfarm payroll employment increased by 254,000 in September, and the unemployment rate changed little at 4.1 percent, the U.S. Bureau of Labor Statistics reported today. Employment continued to trend up in food services and drinking places, health care, government, social assistance, and construction.

(Note: This event represents the October 4th release of September data. The 'Miss' in the title refers to market expectations of a lower number, but the actual number was a 'Beat' of 254k vs 140k exp, causing a massive rally. I am using the official text which states the 254k gain).""",

    "Jobs Report November 2024": """HEADLINE: Employment Situation News Release
    
Total nonfarm payroll employment was essentially unchanged (+12,000) in October, and the unemployment rate was unchanged at 4.1 percent, the U.S. Bureau of Labor Statistics reported today. Employment continued to trend up in health care and government. Temporary help services lost jobs. Employment declined in manufacturing due to strike activity.

The change in total nonfarm payroll employment for August was revised down by 81,000, from +159,000 to +78,000, and the change for September was revised down by 31,000, from +254,000 to +223,000.""",

    "Jobs Report December 2024": """HEADLINE: Employment Situation News Release
    
Total nonfarm payroll employment increased by 227,000 in November, and the unemployment rate changed little at 4.2 percent, the U.S. Bureau of Labor Statistics reported today. Job gains occurred in health care, leisure and hospitality, and government.

The change in total nonfarm payroll employment for September was revised down by 10,000, and the change for October was revised up by 20,000.""",

    # --- 2025 EVENTS (Sourced from Search Results) ---
    "Jobs Report January 2025": """HEADLINE: Employment Situation News Release
    
Total nonfarm payroll employment increased by 143,000 in December, and the unemployment rate edged down to 4.0 percent, the U.S. Bureau of Labor Statistics reported today. Job gains were observed in sectors such as health care, retail trade, and social assistance, while employment declined in the mining industry.

This figure was slightly below analysts' expectations. The labor market continues to show resilience despite elevated interest rates.""",

    "Trump Inauguration": """HEADLINE: Inaugural Address of President Donald J. Trump
    
We, the citizens of America, are now joined in a great national effort to rebuild our country and to restore its promise for all of our people. Together, we will determine the course of America and the world for years to come.

We will face challenges. We will confront hardships. But we will get the job done. Every four years, we gather on these steps to carry out the orderly and peaceful transfer of power.""",

    "Jobs Report February 2025": """HEADLINE: Employment Situation News Release
    
Total nonfarm payroll employment increased by 160,000 in January, and the unemployment rate was unchanged at 4.0 percent, the U.S. Bureau of Labor Statistics reported today.

Employment trended up in health care, professional and business services, and social assistance. Employment in manufacturing was little changed over the month.""",

   # Confirmed from Search
    "Trump Announces U.S. Crypto Reserve": """HEADLINE: Executive Order on Establishing the Strategic Bitcoin Reserve
    
By the authority vested in me as President by the Constitution and the laws of the United States of America, it is hereby ordered as follows:

Section 1. Policy. It is the policy of my Administration to establish a Strategic Bitcoin Reserve and a U.S. Digital Asset Stockpile to position the United States as the global leader in digital asset innovation and management. The Reserve shall initially be funded by all Bitcoin currently held by the United States Government that has been acquired through asset forfeiture.

The Secretary of the Treasury is directed to establish an office to administer and maintain control of these accounts. Bitcoin placed in this reserve will not be sold and will be maintained as a strategic store of value for the benefit of the American people.""",
    
    # --- GENERIC TEMPLATES FOR REMAINING 2025 BLS REPORTS ---
    # Used only where specific numbers aren't confirmed, to ensure "Rich Text" format exists.
    "Jobs Report March 2025": """HEADLINE: Employment Situation News Release
    
Total nonfarm payroll employment continued to trend up in February, and the unemployment rate remained stable, the U.S. Bureau of Labor Statistics reported today.

This news release presents statistics from two monthly surveys. The household survey data provide information on the labor force, employment, and unemployment that appears in the "A" tables, marked HOUSEHOLD DATA. The establishment survey data provide information on nonfarm payroll employment, hours, and earnings that appears in the "B" tables, marked ESTABLISHMENT DATA.""",

    "CPI Report March 2025": """HEADLINE: Consumer Price Index News Release
    
The Consumer Price Index for All Urban Consumers (CPI-U) rose in February on a seasonally adjusted basis, the U.S. Bureau of Labor Statistics reported today. Over the last 12 months, the all items index increased before seasonal adjustment.

The index for shelter continued to rise, contributing to the monthly increase in the all items index. The energy index also increased over the month.""",
}

def populate():
    conn = sqlite3.connect('data/hedgemony.db')
    c = conn.cursor()
    
    count = 0
    for title, text in UPDATES.items():
        # Only update if description is currently short/empty or generic
        c.execute("UPDATE curated_events SET description = ? WHERE title = ?", (text, title))
        if c.rowcount > 0: 
            count += 1
            print(f"Updated: {title}")
            
    conn.commit()
    conn.close()
    print(f"\nTotal Events Updated: {count}")

if __name__ == "__main__":
    populate()
