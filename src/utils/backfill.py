import csv
import asyncio
import logging
import aiohttp
from datetime import datetime
from typing import List, Optional
from src.utils.db import Database
from src.ingestion.base import NewsItem
from src.brain.sentiment import SentimentEngine # To score the backfilled items

class BackfillEngine:
    def __init__(self, config: dict):
        self.logger = logging.getLogger("hedgemony.backfill")
        self.config = config
        self.db = Database()
        self.brain = SentimentEngine(config.get("brain")) # Reuse brain to score history

    def import_csv(self, file_path: str):
        """
        Imports news from a CSV file.
        Expected format: title, url, published_at, source
        """
        self.logger.info(f"Importing from CSV: {file_path}")
        count = 0
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Parse date (assume ISO format or flexible)
                    try:
                        pub_at = datetime.fromisoformat(row.get('published_at', datetime.now().isoformat()))
                    except ValueError:
                        pub_at = datetime.now()

                    item = NewsItem(
                        source_id=f"csv:{row.get('source', 'unknown')}",
                        title=row.get('title', ''),
                        url=row.get('url', ''),
                        published_at=pub_at,
                        content=row.get('content', row.get('title', '')),
                        author=row.get('author')
                    )
                    
                    self._process_and_store(item)
                    count += 1
                    
            self.logger.info(f"Successfully imported {count} items from CSV.")
            
        except Exception as e:
            self.logger.error(f"Failed to import CSV: {e}")

    async def fetch_cryptopanic_history(self, pages: int = 5):
        """
        Fetches last N pages from CryptoPanic API.
        """
        api_key = self.config.get("ingestion", {}).get("cryptopanic", {}).get("api_key")
        if not api_key:
            self.logger.error("No CryptoPanic API key found.")
            return

        base_url = "https://cryptopanic.com/api/v1/posts"
        async with aiohttp.ClientSession() as session:
            for page in range(1, pages + 1):
                params = {
                    "auth_token": api_key,
                    "public": "true",
                    "kind": "news",
                    "page": page
                }
                
                self.logger.info(f"Fetching CryptoPanic Page {page}/{pages}...")
                async with session.get(base_url, params=params) as resp:
                    if resp.status != 200:
                        self.logger.error(f"Failed to fetch page {page}: {resp.status}")
                        break
                    
                    data = await resp.json()
                    results = data.get("results", [])
                    
                    if not results:
                        self.logger.info("No more results found.")
                        break
                        
                    for post in results:
                        item = NewsItem(
                            source_id=f"cryptopanic:{post.get('id')}",
                            title=post.get('title', ''),
                            url=post.get('url', ''),
                            published_at=datetime.now(), # Ideally parse post['created_at']
                            content=post.get('title', ''),
                            author=post.get('domain', 'cryptopanic'),
                            raw_data=post
                        )
                        self._process_and_store(item)
                
                # Be nice to the API
                await asyncio.sleep(1)

    def _process_and_store(self, item: NewsItem):
        """
        Runs the item through the Brain to get sentiment/impact, then saves to DB.
        """
        # 1. Analyze
        analysis = self.brain.analyze(item.title)
        
        # 2. Update Item Impact
        item.impact_score = analysis.get('impact', 0)
        
        # 3. Store
        self.db.log_news(item, analysis)
