from abc import ABC, abstractmethod
from typing import List, Optional, Callable, Awaitable
from dataclasses import dataclass
from datetime import datetime
import asyncio
import logging

# Standard data format for the entire system
@dataclass
class NewsItem:
    source_id: str      # e.g., "rss:reuters", "twitter:user123"
    title: str          # Headline or tweet content
    url: str
    published_at: datetime
    content: str        # Full text or summary
    author: Optional[str] = None
    impact_score: int = 0 # 1-10 score (0 = unrated)
    ingested_at: Optional[datetime] = None # When WE saw it
    raw_data: Optional[dict] = None # Original payload for debugging

class BaseIngester(ABC):
    def __init__(self, name: str, config: dict):
        self.name = name
        self.config = config
        self.logger = logging.getLogger(f"hedgemony.ingest.{name}")
        self._callback: Optional[Callable[[NewsItem], Awaitable[None]]] = None

    def set_callback(self, callback: Callable[[NewsItem], Awaitable[None]]):
        """Set the async function to call when new data arrives."""
        self._callback = callback

    @abstractmethod
    async def start(self):
        """Start the ingestion process (polling loops or stream connections)."""
        pass

    @abstractmethod
    async def stop(self):
        """Gracefully stop the ingestion."""
        pass

    async def _emit(self, item: NewsItem):
        """Send standardized item to the main loop."""
        if not item.ingested_at:
            item.ingested_at = datetime.now()
            
        if self._callback:
            try:
                await self._callback(item)
            except Exception as e:
                self.logger.error(f"Error in callback for {item.source_id}: {e}")
