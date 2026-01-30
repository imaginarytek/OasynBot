#!/usr/bin/env python3
"""
Historical News Backfiller
Populates database with past crypto news events for backtesting
"""
import sys
import os
import asyncio
from datetime import datetime, timedelta
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.db import Database
from src.ingestion.base import NewsItem
from src.brain.sentiment import SentimentEngine
import aiohttp
import feedparser

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("backfill_news")

class NewsBackfiller:
    """Fetch historical news from free sources"""
    
    def __init__(self, db: Database, brain: SentimentEngine):
        self.db = db
        self.brain = brain
        self.session = None
        
    async def fetch_cryptocompare_news(self, start_date: datetime, end_date: datetime):
        """Fetch from CryptoCompare API (free tier available)"""
        base_url = "https://min-api.cryptocompare.com/data/v2/news/"
        
        async with aiohttp.ClientSession() as session:
            params = {
                'lang': 'EN',
                'sortOrder': 'latest'
            }
            
            try:
                async with session.get(base_url, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        news_items = []
                        
                        for article in data.get('Data', [])[:100]:  # Limit to recent 100
                            pub_time = datetime.fromtimestamp(article.get('published_on', 0))
                            
                            if start_date <= pub_time <= end_date:
                                item = NewsItem(
                                    source_id=f"cryptocompare:{article.get('id')}",
                                    title=article.get('title', ''),
                                    url=article.get('url', ''),
                                    published_at=pub_time,
                                    content=article.get('body', '')[:500],
                                    author=article.get('source', 'CryptoCompare'),
                                    impact_score=0,
                                    ingested_at=datetime.now(),
                                    raw_data=article
                                )
                                news_items.append(item)
                        
                        logger.info(f"✅ CryptoCompare: Fetched {len(news_items)} articles")
                        return news_items
            except Exception as e:
                logger.error(f"CryptoCompare fetch failed: {e}")
                return []
    
    async def fetch_rss_archives(self, feeds: list):
        """Fetch from RSS feeds (recent history only)"""
        news_items = []
        
        for feed_url in feeds:
            try:
                # feedparser is synchronous, but fast enough
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries[:50]:  # Limit per feed
                    pub_date = datetime(*entry.published_parsed[:6]) if hasattr(entry, 'published_parsed') else datetime.now()
                    
                    item = NewsItem(
                        source_id=f"rss:{entry.get('id', entry.get('link'))}",
                        title=entry.get('title', ''),
                        url=entry.get('link', ''),
                        published_at=pub_date,
                        content=entry.get('summary', '')[:500],
                        author=feed.feed.get('title', 'RSS'),
                        impact_score=0,
                        ingested_at=datetime.now(),
                        raw_data=None
                    )
                    news_items.append(item)
                    
                logger.info(f"✅ RSS {feed_url[:30]}...: Fetched {len(feed.entries[:50])} items")
            except Exception as e:
                logger.error(f"RSS fetch failed for {feed_url}: {e}")
        
        return news_items
    
    async def process_and_store(self, news_items: list):
        """Analyze and store news items"""
        stored_count = 0
        
        for item in news_items:
            try:
                # Analyze sentiment
                text = f"{item.title}. {item.content}"
                analysis = await self.brain.analyze(text)
                
                # Store in DB
                self.db.log_news(item, analysis)
                stored_count += 1
                
                if stored_count % 10 == 0:
                    logger.info(f"Processed {stored_count}/{len(news_items)} items...")
                    
            except Exception as e:
                logger.error(f"Failed to process item {item.title[:50]}: {e}")
        
        logger.info(f"🎯 Stored {stored_count} historical news items")
        return stored_count

async def main():
    logger.info("🚀 Starting Historical News Backfill...")
    
    # Initialize components
    db = Database()
    db.init_db()
    
    brain = SentimentEngine({'brain': {'model_type': 'groq'}})
    backfiller = NewsBackfiller(db, brain)
    
    # Define date range (last 30 days for free sources)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    logger.info(f"📅 Fetching news from {start_date.date()} to {end_date.date()}")
    
    all_news = []
    
    # Source 1: CryptoCompare
    crypto_news = await backfiller.fetch_cryptocompare_news(start_date, end_date)
    all_news.extend(crypto_news)
    
    # Source 2: RSS Feeds
    rss_feeds = [
        "https://cointelegraph.com/rss",
        "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "https://cryptonews.com/news/feed/",
    ]
    rss_news = await backfiller.fetch_rss_archives(rss_feeds)
    all_news.extend(rss_news)
    
    # Remove duplicates by URL
    seen_urls = set()
    unique_news = []
    for item in all_news:
        if item.url not in seen_urls:
            seen_urls.add(item.url)
            unique_news.append(item)
    
    logger.info(f"📰 Total unique articles: {len(unique_news)}")
    
    # Process and store
    await backfiller.process_and_store(unique_news)
    
    logger.info("✅ Historical backfill complete!")

if __name__ == "__main__":
    asyncio.run(main())
