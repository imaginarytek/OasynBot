
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import subprocess

def fetch_content(url):
    cmd = [
        'curl', '-L', '-s',
        '-A', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        url
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout

def debug_content():
    # Jobs Report March 2024 (Data from Feb)
    url = "https://www.bls.gov/news.release/archives/empsit_03082024.htm"
    print(f"Fetching {url}")
    
    content = fetch_content(url)
    soup = BeautifulSoup(content, 'html.parser')
    
    # Print paragraphs
    print("\n--- SCANNING ALL PARAGRAPHS ---")
    paragraphs = soup.find_all('p')
    for i, p in enumerate(paragraphs):
        text = p.get_text().strip()
        if "Total nonfarm payroll employment" in text:
            print(f"✅ MATCH AT P{i}:")
            print(f"{text[:200]}...")
            
    # Check PRE content
    print("\n--- SCANNING PRE TAGS ---")
    pre = soup.find_all('pre')
    for i, p in enumerate(pre):
        text = p.get_text().strip()
        if "Total nonfarm payroll employment" in text:
            print(f"✅ MATCH AT PRE{i}:")
            print(f"{text[:200]}...")

if __name__ == "__main__":
    debug_content()
