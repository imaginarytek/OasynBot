import asyncio
import logging
from typing import List, Dict, Type
from .base import BaseIngester
from .direct import DirectIngester
from .rss_fetcher import AsyncRSSIngester
from .cryptopanic import CryptoPanicIngester
from .twitter_monitor import TwitterMonitor
import json

class StreamManager:
    """
    Orchestrates multiple ingestion streams (RSS, API, Websockets).
    """
    def __init__(self, config: dict):
        self.logger = logging.getLogger("hedgemony.ingest.manager")
        self.config = config
        self.ingesters: List[BaseIngester] = []
        self._callback = None
        
        # Initialize Ingesters based on config
        self._init_ingesters()

    def _init_ingesters(self):
        # 1. RSS (Aggregators/Slow)
        rss_config = self.config.get("rss", {})
        rss_sources = self.config.get("rss_sources", [])
        if rss_sources:
            self.ingesters.append(AsyncRSSIngester(rss_config, rss_sources))
        
        # 2. CryptoPanic
        cp_config = self.config.get("cryptopanic")
        if cp_config and cp_config.get("enabled", False):
            self.ingesters.append(CryptoPanicIngester(cp_config))
            
        # 3. Twitter
        tw_config = self.config.get("twitter")
        if tw_config and tw_config.get("enabled", False):
            self.ingesters.append(TwitterMonitor(tw_config))
            
        # 4. Direct HFT (New Tier 1 Hunter)
        # Load targets from file
        try:
            with open("config/sources/direct_targets.json", "r") as f:
                direct_targets = json.load(f)
                if direct_targets:
                    # Pass global config for proxy settings if we add them later
                    self.ingesters.append(DirectIngester(self.config, direct_targets))
        except FileNotFoundError:
            self.logger.warning("config/sources/direct_targets.json not found. Skipping HFT Direct Ingester.")
        except Exception as e:
            self.logger.error(f"Failed to load Direct targets: {e}")
            
        self.logger.info(f"Initialized {len(self.ingesters)} ingesters.")

    def set_callback(self, callback):
        self._callback = callback
        for ingester in self.ingesters:
            ingester.set_callback(callback)

    # poll_sources method removed (incompatible with updated Async Architecture)

    async def start(self):
        self.logger.info("Starting Stream Manager...")
        if not self.ingesters:
            self.logger.warning("No ingesters configured!")
            return

        # Start all ingesters concurrently
        tasks = [ingester.start() for ingester in self.ingesters]
        await asyncio.gather(*tasks)

    async def stop(self):
        self.logger.info("Stopping Stream Manager...")
        tasks = [ingester.stop() for ingester in self.ingesters]
        await asyncio.gather(*tasks)
