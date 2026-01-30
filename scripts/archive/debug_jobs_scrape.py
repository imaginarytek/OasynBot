import requests
from bs4 import BeautifulSoup
from datetime import datetime

def debug_jobs_scrape():
    date_str = "2024-03-08"
    dt = datetime.fromisoformat(date_str)
    url = f"https://www.bls.gov/news.release/archives/empsit_{dt.strftime('%m%d%Y')}.htm"
    print(f"Testing URL: {url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Print page title
            print(f"Page Title: {soup.title.string if soup.title else 'No title'}")
            
            # Print first few paragraphs to see structure
            print("\nFirst 5 paragraphs found:")
            paragraphs = soup.find_all('p')
            for i, p in enumerate(paragraphs[:5]):
                print(f"{i}: {p.get_text().strip()[:100]}...")
                
            # Test my extraction logic
            body_text = ""
            for p in paragraphs:
                text = p.get_text().strip()
                if "Total nonfarm payroll employment" in text:
                    body_text = text
                    print(f"\n✅ FOUND MATCH:\n{body_text[:200]}...")
                    break
            
            if not body_text:
                print("\n❌ Extraction logic failed to find match")
                
        else:
            print("Failed to fetch page")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_jobs_scrape()
