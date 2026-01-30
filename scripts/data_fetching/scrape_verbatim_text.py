#!/usr/bin/env python3
"""
Automated scraper to fetch exact verbatim text from BLS and Federal Reserve
This covers ~60 of our 80 events (CPI, Jobs, FOMC)
"""
import sqlite3
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time

class VerbatimTextScraper:
    def __init__(self):
        self.db = sqlite3.connect("data/hedgemony.db")
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://www.bls.gov/',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1'
        })
        
    def fetch_url(self, url):
        """Fetch URL content using requests, falling back to curl on failure"""
        try:
            # Method 1: Requests
            try:
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    return response.text
                print(f"      ⚠️  HTTP {response.status_code} with requests, trying curl...")
            except Exception as e:
                print(f"      ⚠️  Requests error: {e}, trying curl...")
                
            # Method 2: Curl Fallback
            import subprocess
            cmd = [
                'curl', '-L', '-s',
                '-A', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                url
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0 and result.stdout:
                return result.stdout
            else:
                print(f"      ❌ Curl failed: RC={result.returncode}, Stderr: {result.stderr[:100]}")
                
        except Exception as e:
            print(f"      Error fetching {url}: {e}")
            
        return None
    
    def scrape_bls_cpi(self, date_str):
        """Scrape CPI report from BLS - EXACT VERBATIM - WITH DATE FUZZING"""
        target_dt = datetime.fromisoformat(date_str)
        
        # Ranges to check: target, -1, +1, -2, +2, +3 days (covering weekends)
        offsets = [0, 1, -1, 2, -2, 3, 4]
        
        for offset in offsets: # Fuzz dates
            from datetime import timedelta
            check_dt = target_dt + timedelta(days=offset)
            url = f"https://www.bls.gov/news.release/archives/cpi_{check_dt.strftime('%m%d%Y')}.htm"
            if offset != 0:
                 print(f"      Trying alt date {check_dt.date()}: {url}")
            else:
                 print(f"      Trying URL: {url}")
            
            content = self.fetch_url(url)
            if content:
                # Validate it's not a generic error page if fetch_url missed it
                if "Page not found" in content or "404" in content[:200]:
                    continue
                    
                soup = BeautifulSoup(content, 'html.parser')
                
            headline = soup.find('h1')
            headline_text = headline.get_text().strip() if headline else "Consumer Price Index"
            
            # --- EXTRACT RICH BODY (Headline + First 3 Paragraphs) ---
            summary_paragraphs = []
            
            # Method 1: Check <p> tags
            paragraphs = soup.find_all('p')
            capturing = False
            for p in paragraphs:
                text = p.get_text().strip()
                if "The Consumer Price Index" in text and "seasonally adjusted" in text:
                    capturing = True
                
                if capturing and len(text) > 20:
                    summary_paragraphs.append(text)
                    if len(summary_paragraphs) >= 3:
                        break
            
            # Method 2: Check <pre> tags
            if not summary_paragraphs:
                pre_tags = soup.find_all('pre')
                for pre in pre_tags:
                    text = pre.get_text()
                    chunks = text.split('\n\n')
                    capturing = False
                    for chunk in chunks:
                        clean_chunk = ' '.join(chunk.split())
                        if "The Consumer Price Index" in clean_chunk and "seasonally adjusted" in clean_chunk:
                            capturing = True
                        
                        if capturing and len(clean_chunk) > 20:
                            summary_paragraphs.append(clean_chunk)
                            if len(summary_paragraphs) >= 3:
                                break
                    if summary_paragraphs: break
            
            # If standard phrase not found, get the first substantial paragraph
            if not summary_paragraphs:
                for p in paragraphs:
                        text = p.get_text().strip()
                        if len(text) > 100 and "Bureau of Labor Statistics" in text:
                            summary_paragraphs.append(text)
                            break
            
            if summary_paragraphs:
                formatted_text = f"HEADLINE: {headline_text}\n\n" + "\n\n".join(summary_paragraphs)
                print(f"      ✅ Captured Rich Text: {len(formatted_text)} chars")
                return {
                    'headline': headline_text,
                    'body': formatted_text,
                    'url': url,
                    'source': 'Bureau of Labor Statistics'
                }
        
        return None
    
    def scrape_bls_jobs(self, date_str):
        """Scrape Jobs report from BLS - EXACT VERBATIM - WITH FUZZING"""
        target_dt = datetime.fromisoformat(date_str)
        
        # Check standard date then +/- 7 days (Jobs is first Friday, might be shifted)
        offsets = [0, 7, -7, 1, -1] 
        
        for offset in offsets:
            from datetime import timedelta
            check_dt = target_dt + timedelta(days=offset)
            url = f"https://www.bls.gov/news.release/archives/empsit_{check_dt.strftime('%m%d%Y')}.htm"
            if offset != 0:
                 print(f"      Trying alt date {check_dt.date()}: {url}")
            else:
                 print(f"      Trying URL: {url}")
            
            content = self.fetch_url(url)
            if content:
                 if "Page not found" in content or "404" in content[:200]:
                    continue
                    
                 soup = BeautifulSoup(content, 'html.parser')
                 
                 # Verify it's actually an Employment Situation page
                 if "Employment Situation" not in str(soup.title) and "Employment Situation" not in str(soup.find('h1')):
                     continue
                
            headline = soup.find('h1')
            headline_text = headline.get_text().strip() if headline else "The Employment Situation"
                
            # --- EXTRACT RICH BODY (Headline + First 3 Paragraphs) ---
            summary_paragraphs = []
            
            # Method 1: Check <p> tags
            paragraphs = soup.find_all('p')
            capturing = False
            for p in paragraphs:
                text = p.get_text().strip()
                
                # Skip embargo warnings
                if "Transmission of material" in text or "embargoed" in text.lower():
                    continue
                    
                if "Total nonfarm payroll employment" in text:
                    capturing = True
                
                if capturing and len(text) > 20 and len(text) < 2000: 
                    # Clean up any whitespace mess
                    clean_text = ' '.join(text.split())
                    summary_paragraphs.append(clean_text)
                    if len(summary_paragraphs) >= 3: # Get top 3 paragraphs
                        break
            
            # Method 2: Check <pre> tags (legacy format)
            if not summary_paragraphs:
                pre_tags = soup.find_all('pre')
                for pre in pre_tags:
                    text = pre.get_text()
                    chunks = text.split('\n\n')
                    capturing = False
                    for chunk in chunks:
                        clean_chunk = ' '.join(chunk.split())
                        
                        if "Transmission of material" in clean_chunk: continue
                        
                        if "Total nonfarm payroll employment" in clean_chunk:
                            capturing = True
                        
                        if capturing and len(clean_chunk) > 20:
                            summary_paragraphs.append(clean_chunk)
                            if len(summary_paragraphs) >= 3:
                                break
                    if summary_paragraphs: break
            
            if summary_paragraphs:
                formatted_text = f"HEADLINE: {headline_text}\n\n" + "\n\n".join(summary_paragraphs)
                print(f"      ✅ Captured Rich Text: {len(formatted_text)} chars")
                return {
                    'headline': headline_text,
                    'body': formatted_text,
                    'url': url,
                    'source': 'Bureau of Labor Statistics'
                }
            else:
                 print(f"      ❌ Parsing failed. Content len: {len(content)}. Encoded title: {soup.title}")

        return None
    
    def scrape_fomc(self, date_str):
        """Scrape FOMC statement from Federal Reserve - EXACT VERBATIM"""
        dt = datetime.fromisoformat(date_str)
        url = f"https://www.federalreserve.gov/newsevents/pressreleases/monetary{dt.strftime('%Y%m%d')}a.htm"
        
        content = self.fetch_url(url)
        if content:
            soup = BeautifulSoup(content, 'html.parser')
                
            headline = "Federal Reserve issues FOMC statement"
                
            # --- EXTRACT RICH BODY (Headline + First 3 Paragraphs) ---
            summary_paragraphs = []
            paragraphs = soup.find_all('p')
            capturing = False
            
            # Start capturing from the first substantive paragraph
            for p in paragraphs:
                text = p.get_text().strip()
                if "economic activity" in text or "Committee decided to" in text:
                    capturing = True
                
                if capturing and len(text) > 20: 
                    summary_paragraphs.append(text)
                    if len(summary_paragraphs) >= 3: 
                        break
            
            # Fallback if standard start not found
            if not summary_paragraphs:
                 for p in paragraphs:
                        text = p.get_text().strip()
                        if len(text) > 100 and "Federal Reserve" in text:
                            summary_paragraphs.append(text)
                            break
                            
            if summary_paragraphs:
                formatted_text = f"HEADLINE: {headline}\n\n" + "\n\n".join(summary_paragraphs)
                print(f"      ✅ Captured Rich Text: {len(formatted_text)} chars")
                return {
                    'headline': headline,
                    'body': formatted_text,
                    'url': url,
                    'source': 'Federal Reserve'
                }
        
        return None
    
    def process_all_events(self):
        """Process all events in database and fetch verbatim text"""
        print("🔍 FETCHING VERBATIM TEXT FROM OFFICIAL SOURCES\n")
        print("="*80)
        
        c = self.db.cursor()
        
        # Get all events
        c.execute("""
            SELECT rowid, title, timestamp
            FROM curated_events
            WHERE description IS NULL
            ORDER BY timestamp
        """)
        
        events = c.fetchall()
        
        updated = 0
        failed = 0
        
        for rowid, title, ts_str in events:
            print(f"\n[{rowid}] {title}")
            print(f"   Date: {ts_str[:10]}")
            
            data = None
            
            # Determine event type and scrape
            if 'CPI' in title:
                data = self.scrape_bls_cpi(ts_str)
            elif 'Jobs' in title or 'Employment' in title:
                data = self.scrape_bls_jobs(ts_str)
            elif 'FOMC' in title:
                data = self.scrape_fomc(ts_str)
            else:
                print("   ⏭️  Skipping (not BLS/Fed)")
                continue
            
            if data and data['body']:
                # Update database
                c.execute("""
                    UPDATE curated_events
                    SET description = ?
                    WHERE rowid = ?
                """, (data['body'], rowid))
                
                self.db.commit()
                updated += 1
                print(f"   ✅ Fetched from {data['source']}")
                print(f"   Text: {data['body'][:100]}...")
            else:
                failed += 1
                print(f"   ❌ Failed to fetch")
            
            # Rate limiting
            time.sleep(1)
        
        self.db.close()
        
        print(f"\n{'='*80}")
        print(f"COMPLETE:")
        print(f"  ✅ Updated: {updated}")
        print(f"  ❌ Failed: {failed}")
        print(f"  ⏭️  Skipped: {len(events) - updated - failed}")
        print(f"{'='*80}")

if __name__ == "__main__":
    scraper = VerbatimTextScraper()
    scraper.process_all_events()
