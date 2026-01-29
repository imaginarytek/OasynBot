import aiohttp
import asyncio
import logging
from datetime import datetime
from typing import Optional
from .base import BaseIngester, NewsItem

class CryptoPanicIngester(BaseIngester):
    BASE_URL = "https://cryptopanic.com/api/v1/posts/"

    def __init__(self, config: dict):
        super().__init__("cryptopanic", config)
        self.api_key = config.get("api_key")
        self.interval = config.get("interval", 60) # Poll every 60s by default
        self._running = False
        self._task: Optional[asyncio.Task] = None
        
        if not self.api_key:
            self.logger.warning("No API Key provided for CryptoPanic. Ingestion will be disabled.")

    async def start(self):
        if not self.api_key:
            return
            
        self._running = True
        self._task = asyncio.create_task(self._poll_loop())
        self.logger.info("CryptoPanic Ingester Started.")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self.logger.info("CryptoPanic Ingester Stopped.")

    async def _poll_loop(self):
        async with aiohttp.ClientSession() as session:
            while self._running:
                try:
                    await self._fetch_posts(session)
                except Exception as e:
                    self.logger.error(f"Error polling CryptoPanic: {e}")
                
                await asyncio.sleep(self.interval)

    async def _fetch_posts(self, session):
        params = {
            "auth_token": self.api_key,
            "public": "true",
            "kind": "news" # or 'media', 'news' covers most
        }
        
        async with session.get(self.BASE_URL, params=params) as resp:
            if resp.status != 200:
                self.logger.error(f"Failed to fetch: {resp.status} - {await resp.text()}")
                return
            
            data = await resp.json()
            results = data.get("results", [])
            
            # Inverse order to process oldest first if needed, but newest is fine
            # We need a way to deduplicate. Ideally the Manager handles it, or we track last_id.
            # For v1 simple: just emit everything and let the DB/Manager dedup if possible,
            # BUT raw polling will re-emit same news every minute. We MUST track last_id.
            
            # Use the first item as the "latest" marker after processing
            # But since we're async, just dedupe by ID in memory for now.
            
            # Simple in-memory dedup for this session
            if not hasattr(self, '_seen_ids'):
                self._seen_ids = set()

            new_count = 0
            for post in results:
                post_id = post.get("id")
                if post_id in self._seen_ids:
                    continue
                
                self._seen_ids.add(post_id)
                new_count += 1
                
                # Convert to NewsItem
                item = NewsItem(
                    source_id=f"cryptopanic:{post_id}",
                    title=post.get("title", ""),
                    url=post.get("url", ""),
                    published_at=datetime.now(), # CryptoPanic gives 'created_at' but format varies, safe to use now() for ingestion time
                    content=post.get("title", ""), # Content is usually link-only
                    author=post.get("domain", "cryptopanic"),
                    raw_data=post
                )
                
                await self._emit(item)
            
            if new_count > 0:
                self.logger.info(f"Fetched {new_count} new items.")
