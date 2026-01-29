import asyncio
import aiohttp
import feedparser
from datetime import datetime
from dateutil import parser as date_parser
from typing import List, Set
from .base import BaseIngester, NewsItem

class AsyncRSSIngester(BaseIngester):
    def __init__(self, config: dict, feed_urls: List[str]):
        super().__init__("rss", config)
        self.feed_urls = feed_urls
        self.is_running = False
        self.seen_urls: Set[str] = set()
        self.poll_interval = config.get("rss_poll_interval", 60)

    async def fetch_feed(self, session: aiohttp.ClientSession, url: str):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            async with session.get(url, timeout=10, headers=headers) as response:
                if response.status != 200:
                    self.logger.warning(f"Failed to fetch {url}: Status {response.status}")
                    return
                
                content = await response.text()
                # Feedparser is blocking, but fast for small XML. 
                # For massive scale, run in executor.
                loop = asyncio.get_event_loop()
                feed = await loop.run_in_executor(None, feedparser.parse, content)
                
                for entry in feed.entries:
                    link = entry.get('link', '')
                    if not link or link in self.seen_urls:
                        continue
                        
                    self.seen_urls.add(link)
                    
                    # Parse date safely
                    pub_date = datetime.now()
                    if 'published' in entry:
                        try:
                            pub_date = date_parser.parse(entry.published)
                        except:
                            pass
                            
                    item = NewsItem(
                        source_id=f"rss:{feed.feed.get('title', 'unknown')}",
                        title=entry.get('title', ''),
                        url=link,
                        published_at=pub_date,
                        content=entry.get('summary', '') or entry.get('description', ''),
                        author=entry.get('author', None),
                        raw_data=dict(entry)
                    )
                    
                    await self._emit(item)
                    
        except Exception as e:
            self.logger.error(f"Error fetching {url}: {e}")

    async def loop(self):
        conn = aiohttp.TCPConnector(limit=100) # Connection pooling
        async with aiohttp.ClientSession(connector=conn) as session:
            while self.is_running:
                tasks = [self.fetch_feed(session, url) for url in self.feed_urls]
                await asyncio.gather(*tasks)
                
                self.logger.info(f"RSS Poll complete. Sleeping {self.poll_interval}s")
                await asyncio.sleep(self.poll_interval)

    async def start(self):
        self.is_running = True
        self.logger.info(f"Starting RSS Ingester with {len(self.feed_urls)} feeds")
        asyncio.create_task(self.loop())

    async def stop(self):
        self.is_running = False
        self.logger.info("Stopping RSS Ingester")
