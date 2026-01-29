
import asyncio
import logging
from datetime import datetime
import tweepy
import tweepy.asynchronous
from typing import List, Optional
from .base import BaseIngester, NewsItem

class HFTTwitterStreamer(tweepy.asynchronous.AsyncStreamingClient):
    """
    Subclass of AsyncStreamingClient to handle incoming tweets.
    """
    def __init__(self, bearer_token, parent_monitor):
        super().__init__(bearer_token)
        self.parent = parent_monitor
        self.logger = logging.getLogger("hedgemony.ingest.twitter.stream")

    async def on_tweet(self, tweet):
        """Called when a new tweet is received."""
        # This is where the magic happens - real-time!
        await self.parent._process_tweet(tweet)

    async def on_error(self, status_code):
        self.logger.error(f"Stream Error: {status_code}")
        if status_code == 420:
            # Rate limit - disconnect (Enhancement: Implement exponential backoff)
            return False

class TwitterMonitor(BaseIngester):
    """
    Ingests tweets using Tweepy (Twitter API v2).
    Supports both Polling and Streaming (Filtered Stream).
    """
    def __init__(self, config: dict):
        super().__init__("twitter", config)
        self.client: Optional[tweepy.Client] = None
        self.stream_client: Optional[HFTTwitterStreamer] = None
        
        self.poll_interval = config.get("poll_interval", 60)
        self.query = config.get("query", "crypto -is:retweet")
        self.max_results = config.get("max_results", 10)
        self.use_streaming = config.get("use_streaming", True) # Default to streaming for speed
        
        self.running = False
        self._task = None
        
        self.bearer_token = config.get("bearer_token")

    async def start(self):
        """Start the ingestion process."""
        if self.running:
            return

        if not self.bearer_token:
             self.logger.warning("No Bearer Token found. Twitter ingestion disabled.")
             return

        self.running = True
        
        if self.use_streaming:
            self.logger.info("Initializing HFT Twitter Stream...")
            await self._start_streaming()
        else:
            self.logger.info(f"Starting Polling Monitor (every {self.poll_interval}s)")
            self.client = tweepy.Client(bearer_token=self.bearer_token)
            self._task = asyncio.create_task(self._poll_loop())

    async def _start_streaming(self):
        """Setup and start the filtered stream."""
        self.stream_client = HFTTwitterStreamer(self.bearer_token, self)
        
        # 1. Clear existing rules to avoid duplication
        try:
            current_rules = await self.stream_client.get_rules()
            if current_rules and current_rules.data:
                rule_ids = [r.id for r in current_rules.data]
                if rule_ids:
                    await self.stream_client.delete_rules(rule_ids)
                    self.logger.info(f"Cleared {len(rule_ids)} old rules.")
        except Exception as e:
            self.logger.warning(f"Could not clear rules: {e}")

        # 2. Add our specific highly-targeted alpha rule
        try:
            # Tweepy async add_rules
            rule = tweepy.StreamRule(value=self.query, tag="hedgemony-alpha")
            await self.stream_client.add_rules([rule])
            self.logger.info(f"Added Stream Rule: {self.query}")
        except Exception as e:
            self.logger.error(f"Failed to add rule: {e}")
            return

        # 3. Start the stream in background task
        # filter() is long-running
        self._task = asyncio.create_task(self.stream_client.filter(tweet_fields=["created_at", "author_id", "lang"]))
        self.logger.info("Twitter Stream ACTIVE. Listening for events...")

    async def stop(self):
        self.running = False
        
        if self.stream_client:
            self.logger.info("Disconnecting Stream...")
            self.stream_client.disconnect()
            
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self.logger.info("Twitter Monitor stopped.")

    async def _process_tweet(self, tweet):
        """Convert tweet to NewsItem and emit."""
        # Basic deduplication could happen here if needed
        item = NewsItem(
            source_id=f"twitter:{tweet.id}",
            title=tweet.text[:100] + "..." if len(tweet.text) > 100 else tweet.text,
            url=f"https://twitter.com/user/status/{tweet.id}",
            published_at=tweet.created_at or datetime.now(),
            content=tweet.text,
            author=str(tweet.author_id),
            raw_data=tweet.data
        )
        self.logger.info(f"🐦 ALERT: {item.title}")
        await self._emit(item)

    async def _poll_loop(self):
        """Main polling loop (Fallback)."""
        # Keep track of the newest tweet ID we've seen to avoid duplicates
        since_id = None

        while self.running:
            try:
                # Need to run synchronous tweepy call in a thread
                response = await asyncio.to_thread(
                    self.client.search_recent_tweets,
                    query=self.query,
                    max_results=self.max_results,
                    since_id=since_id,
                    tweet_fields=["created_at", "author_id", "lang"]
                )
                
                if response and response.data:
                    newest_id = max(t.id for t in response.data)
                    since_id = newest_id

                    for tweet in response.data:
                        await self._process_tweet(tweet)
                
            except Exception as e:
                self.logger.error(f"Error polling Twitter: {e}")

            await asyncio.sleep(self.poll_interval)
