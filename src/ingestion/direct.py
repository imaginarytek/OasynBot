
import asyncio
import aiohttp
import feedparser
import logging
from datetime import datetime
from typing import List, Dict, Optional
from .base import BaseIngester, NewsItem

class DirectIngester(BaseIngester):
    """
    "Hunter" styling polling for Tier-1 Critical Sources.
    
    Features:
    - Dedicated session per target for keep-alive.
    - ETag / Last-Modified support to minimize bandwidth.
    - Aggressive polling interval (configurable).
    - Proxy support structure (ready for residential proxies).
    """
    
    def __init__(self, config: dict, targets: List[Dict]):
        super().__init__("direct_hft", config)
        self.targets = targets
        self.logger = logging.getLogger("hedgemony.ingest.direct")
        self.running = False
        self.tasks = []
        
        # State tracking for diffing
        self.last_etags = {} # url -> etag
        self.last_modified = {} # url -> last_modified
        self.seen_guids = set() # global dedupe for session

    async def start(self):
        self.running = True
        self.logger.info(f"Starting Direct HFT Ingester with {len(self.targets)} targets.")
        
        # We spawn a dedicated continuous loop for EACH target
        # This ensures one slow server doesn't block others.
        for target in self.targets:
            task = asyncio.create_task(self._monitor_target(target))
            self.tasks.append(task)

    async def stop(self):
        self.running = False
        self.logger.info("Stopping Direct HFT Ingester...")
        for task in self.tasks:
            task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)

    async def _monitor_target(self, target: Dict):
        """
        Continuous monitoring loop for a single target.
        """
        url = target['url']
        interval = target.get('poll_interval', 5.0)
        name = target['name']
        
        # Use a dedicated session for keep-alive connection reuse
        # In production, we would inject proxy here: connector=aiohttp.TCPConnector(ssl=False)
        headers = {
             'User-Agent': 'Mozilla/5.0 (Compatible; HedgemonyBot/1.0; +http://hedgemony.ai)'
        }

        async with aiohttp.ClientSession(headers=headers) as session:
            self.logger.info(f"Ref: {name} | Monitoring started ({interval}s)")
            
            while self.running:
                try:
                    start_time = asyncio.get_event_loop().time()
                    
                    # 1. Prepare conditional headers
                    request_headers = {}
                    if url in self.last_etags:
                        request_headers['If-None-Match'] = self.last_etags[url]
                    if url in self.last_modified:
                        request_headers['If-Modified-Since'] = self.last_modified[url]

                    # 2. Fetch
                    async with session.get(url, headers=request_headers, timeout=5) as response:
                        
                        # 304 Not Modified - Minimal Bandwidth
                        if response.status == 304:
                            # self.logger.debug(f"{name}: No Change (304)")
                            pass
                            
                        elif response.status == 200:
                            # Extract Caching Headers
                            etag = response.headers.get('ETag')
                            lmod = response.headers.get('Last-Modified')
                            
                            if etag: self.last_etags[url] = etag
                            if lmod: self.last_modified[url] = lmod
                            
                            # Parse Content
                            content = await response.text()
                            
                            # Detect Type (RSS vs HTML)
                            # For MVP we treat all as feedparser compatible or raw text check
                            if target['type'] == 'rss':
                                await self._process_rss_content(name, url, content)
                            else:
                                # TODO: Implement HTML selector diffing for non-RSS pages
                                pass
                                
                        else:
                            self.logger.warning(f"{name}: Check failed. Status {response.status}")
                
                except asyncio.TimeoutError:
                     self.logger.warning(f"{name}: Timeout (5s)")
                except Exception as e:
                     self.logger.error(f"{name}: Error - {e}")

                # Smart Sleep: Adjust for time taken to request
                elapsed = asyncio.get_event_loop().time() - start_time
                sleep_time = max(0.1, interval - elapsed)
                await asyncio.sleep(sleep_time)

    async def _process_rss_content(self, name, url, content):
        """
        Parse RSS content in executor to avoid blocking the HFT loop.
        """
        loop = asyncio.get_event_loop()
        # Offload CPU-bound parsing
        feed = await loop.run_in_executor(None, feedparser.parse, content)
        
        # Process entries (Newest First usually)
        # We iterate and check if seen.
        new_items_count = 0
        
        for entry in feed.entries:
            item_id = entry.get('id', entry.get('link'))
            if not item_id or item_id in self.seen_guids:
                continue
            
            # New Item!
            self.seen_guids.add(item_id)
            new_items_count += 1
            
            # Create NewsItem
            item = NewsItem(
                source_id=f"direct:{name}",
                title=entry.get('title', 'No Title'),
                url=entry.get('link', url),
                published_at=datetime.now(), # Real-time detection time is what matters for HFT
                content=entry.get('summary', '') or entry.get('description', ''),
                author=name,
                raw_data=dict(entry)
            )
            
            self.logger.info(f"⚡️ DIRECT HIT [{name}]: {item.title}")
            await self._emit(item)
            
        if new_items_count > 0:
            self.logger.info(f"{name}: Emitted {new_items_count} new items.")
