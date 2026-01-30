#!/usr/bin/env python3
"""
AGGRESSIVE Historical News Backfiller
Fetches THOUSANDS of crypto news items from multiple sources
Designed for intensive data mining to build a comprehensive backtest dataset
"""
import sys
import os
import asyncio
from datetime import datetime, timedelta
import logging
from typing import List
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.db import Database
from src.ingestion.base import NewsItem
from src.brain.sentiment import SentimentEngine
import aiohttp
import feedparser
from concurrent.futures import ThreadPoolExecutor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("aggressive_backfill")

class AggressiveNewsBackfiller:
    """Intensive multi-source historical news fetcher"""
    
    def __init__(self, db: Database, brain: SentimentEngine):
        self.db = db
        self.brain = brain
        self.total_fetched = 0
        self.total_stored = 0
        
    async def fetch_cryptocompare_paginated(self, days_back: int = 365):
        """Fetch CryptoCompare with pagination - can get 1+ year of data"""
        logger.info(f"🔍 CryptoCompare: Mining {days_back} days of history...")
        base_url = "https://min-api.cryptocompare.com/data/v2/news/"
        
        news_items = []
        
        async with aiohttp.ClientSession() as session:
            # CryptoCompare returns ~50 items per page, we can paginate
            # by using before_ts parameter
            current_ts = int(time.time())
            target_ts = current_ts - (days_back * 86400)
            
            page = 0
            while current_ts > target_ts and page < 100:  # Safety limit
                params = {
                    'lang': 'EN',
                    'sortOrder': 'latest',
                    'lTs': current_ts
                }
                
                try:
                    async with session.get(base_url, params=params) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            articles = data.get('Data', [])
                            
                            if not articles:
                                break
                            
                            for article in articles:
                                pub_time = datetime.fromtimestamp(article.get('published_on', 0))
                                
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
                            
                            # Update timestamp for next page
                            current_ts = articles[-1].get('published_on', 0) - 1
                            page += 1
                            
                            logger.info(f"  Page {page}: +{len(articles)} articles (total: {len(news_items)})")
                            
                            # Rate limit respect
                            await asyncio.sleep(0.5)
                        else:
                            logger.warning(f"CryptoCompare returned {resp.status}")
                            break
                            
                except Exception as e:
                    logger.error(f"CryptoCompare page {page} failed: {e}")
                    await asyncio.sleep(2)
                    
        logger.info(f"✅ CryptoCompare: Fetched {len(news_items)} articles")
        return news_items
    
    async def fetch_newsapi(self, api_key: str = None, days_back: int = 30):
        """Fetch from NewsAPI.org (requires free API key)"""
        if not api_key:
            api_key = os.getenv("NEWSAPI_KEY")
            
        if not api_key:
            logger.warning("⚠️ NewsAPI: No API key found, skipping")
            return []
        
        logger.info(f"🔍 NewsAPI: Mining {days_back} days...")
        base_url = "https://newsapi.org/v2/everything"
        
        news_items = []
        
        # Split into weekly chunks to maximize results
        end_date = datetime.now()
        
        async with aiohttp.ClientSession() as session:
            for week in range(0, days_back // 7):
                week_end = end_date - timedelta(days=week * 7)
                week_start = week_end - timedelta(days=7)
                
                params = {
                    'q': 'bitcoin OR ethereum OR crypto OR cryptocurrency',
                    'from': week_start.strftime('%Y-%m-%d'),
                    'to': week_end.strftime('%Y-%m-%d'),
                    'language': 'en',
                    'sortBy': 'publishedAt',
                    'pageSize': 100,
                    'apiKey': api_key
                }
                
                try:
                    async with session.get(base_url, params=params) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            articles = data.get('articles', [])
                            
                            for article in articles:
                                pub_time = datetime.fromisoformat(article['publishedAt'].replace('Z', '+00:00'))
                                
                                item = NewsItem(
                                    source_id=f"newsapi:{article.get('url', '')}",
                                    title=article.get('title', ''),
                                    url=article.get('url', ''),
                                    published_at=pub_time,
                                    content=article.get('description', '')[:500],
                                    author=article.get('author', 'NewsAPI'),
                                    impact_score=0,
                                    ingested_at=datetime.now(),
                                    raw_data=article
                                )
                                news_items.append(item)
                            
                            logger.info(f"  Week {week+1}: +{len(articles)} articles")
                            await asyncio.sleep(1)  # Rate limit
                        else:
                            logger.warning(f"NewsAPI returned {resp.status}")
                            break
                except Exception as e:
                    logger.error(f"NewsAPI week {week} failed: {e}")
                    
        logger.info(f"✅ NewsAPI: Fetched {len(news_items)} articles")
        return news_items
    
    def fetch_rss_aggressive(self, feeds: List[str], items_per_feed: int = 100):
        """Fetch maximum items from RSS feeds"""
        logger.info(f"🔍 RSS: Mining {len(feeds)} feeds ({items_per_feed} items each)...")
        news_items = []
        
        for feed_url in feeds:
            try:
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries[:items_per_feed]:
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
                    
                logger.info(f"  {feed.feed.get('title', 'RSS')[:30]}: +{len(feed.entries[:items_per_feed])} items")
                time.sleep(0.2)  # Be respectful
            except Exception as e:
                logger.error(f"RSS {feed_url[:40]} failed: {e}")
        
        logger.info(f"✅ RSS: Fetched {len(news_items)} articles")
        return news_items
    
    async def process_batch(self, news_items: List[NewsItem], batch_size: int = 20):
        """Process news items in parallel batches for speed"""
        logger.info(f"⚙️ Processing {len(news_items)} items in batches of {batch_size}...")
        
        stored_count = 0
        loop = asyncio.get_running_loop()
        
        for i in range(0, len(news_items), batch_size):
            batch = news_items[i:i+batch_size]
            tasks = []
            
            for item in batch:
                # Run sentiment analysis in thread pool (FinBERT is CPU-bound)
                text = f"{item.title}. {item.content}"
                task = loop.run_in_executor(None, self.brain.analyze, text, None)
                tasks.append((item, task))
            
            # Wait for batch to complete
            for item, task in tasks:
                try:
                    analysis = await task
                    self.db.log_news(item, analysis)
                    stored_count += 1
                except Exception as e:
                    logger.error(f"Failed to process {item.title[:50]}: {e}")
            
            if (i + batch_size) % 100 == 0:
                logger.info(f"  Processed {min(i+batch_size, len(news_items))}/{len(news_items)}...")
        
        logger.info(f"✅ Stored {stored_count} items in database")
        return stored_count

async def main():
    import argparse
    parser = argparse.ArgumentParser(description='Aggressive News Backfiller')
    parser.add_argument('--days', type=int, default=365, help='Days of history to fetch')
    parser.add_argument('--newsapi-key', type=str, help='NewsAPI.org API key (optional)')
    args = parser.parse_args()
    
    logger.info("="*60)
    logger.info("🚀 AGGRESSIVE HISTORICAL NEWS BACKFILLER")
    logger.info("="*60)
    
    # Initialize
    db = Database()
    db.init_db()
    
    brain = SentimentEngine({'brain': {'model_type': 'groq'}})
    backfiller = AggressiveNewsBackfiller(db, brain)
    
    logger.info(f"📅 Target: {args.days} days of historical data")
    logger.info("⚡ Initiating multi-source data mining...")
    
    all_news = []
    
    # Source 1: CryptoCompare (Paginated - can go back 1+ year)
    crypto_news = await backfiller.fetch_cryptocompare_paginated(days_back=args.days)
    all_news.extend(crypto_news)
    
    # Source 2: NewsAPI (if key provided)
    newsapi_items = await backfiller.fetch_newsapi(
        api_key=args.newsapi_key, 
        days_back=min(args.days, 30)  # Free tier limited to 30 days
    )
    all_news.extend(newsapi_items)
    
    # Source 3: RSS Feeds (Aggressive scraping)
    rss_feeds = [
        "https://cointelegraph.com/rss",
        "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "https://cryptonews.com/news/feed/",
        "https://decrypt.co/feed",
        "https://bitcoinmagazine.com/feed",
        "https://www.theblockcrypto.com/rss.xml",
        "https://cryptopotato.com/feed/",
        "https://cryptoslate.com/feed/",
    ]
    
    # Run RSS in thread pool since feedparser is blocking
    loop = asyncio.get_running_loop()
    rss_news = await loop.run_in_executor(
        None, 
        backfiller.fetch_rss_aggressive, 
        rss_feeds, 
        200  # items per feed
    )
    all_news.extend(rss_news)
    
    # Deduplicate
    logger.info(f"🔧 Deduplicating {len(all_news)} articles...")
    seen_urls = set()
    unique_news = []
    for item in all_news:
        if item.url and item.url not in seen_urls:
            seen_urls.add(item.url)
            unique_news.append(item)
    
    logger.info(f"📰 Total unique articles: {len(unique_news)}")
    
    # Process and store in batches
    stored = await backfiller.process_batch(unique_news, batch_size=20)
    
    logger.info("="*60)
    logger.info(f"✅ BACKFILL COMPLETE: {stored} historical news items stored")
    logger.info("="*60)
    logger.info("💡 You can now run backtests on this historical data!")

if __name__ == "__main__":
    asyncio.run(main())
