import asyncio
import logging
import yaml
import json
from src.ingestion.stream_manager import StreamManager
from src.brain.sentiment import SentimentEngine
from src.trading.executor import PaperTradingExecutor
from src.ingestion.base import NewsItem
from src.utils.db import Database

import os
from dotenv import load_dotenv

# Load env vars
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("hedgemony.core")

class HedgemonyEngine:
    def __init__(self, config_path="config/config.yaml"):
        self.config = self._load_config(config_path)
        logger.info("Initializing Hedgemony Engine...")
        
        # 0. Setup DB
        self.db = Database()
        self.db.init_db()

        # 1. Setup Brain (AI)
        self.brain = SentimentEngine(self.config.get("brain"))
        
        # 1.5 Setup Memory (Long-Term Vector Store)
        from src.brain.memory import MemoryManager
        self.memory = MemoryManager(self.config)
        
        # 2. Setup Execution (Trading)
        from src.trading.executor import PaperTradingExecutor
        from src.trading.live_executor import LiveTradingExecutor
        
        mode = self.config.get("system", {}).get("mode", "paper")
        
        if mode == "live":
            logger.warning("⚠️ ENGINE STARTING IN LIVE TRADING MODE")
            self.trader = LiveTradingExecutor(self.config, self.db)
        else:
            logger.info("Engine starting in PAPER Trading Mode")
            self.trader = PaperTradingExecutor(self.config, self.db)
        
        # 3. Setup Ingestion (Ears) - Process Split
        self.ingestion_config = self.config.get("ingestion", {})
        
        # Inject Secrets from Env for Worker
        if 'twitter' not in self.ingestion_config:
            self.ingestion_config['twitter'] = {}
        
        self.ingestion_config['twitter']['bearer_token'] = os.getenv("TWITTER_BEARER_TOKEN")
        self.ingestion_config['twitter']['api_key'] = os.getenv("TWITTER_API_KEY")
        self.ingestion_config['twitter']['api_secret'] = os.getenv("TWITTER_API_SECRET")
        self.ingestion_config['twitter']['access_token'] = os.getenv("TWITTER_ACCESS_TOKEN")
        self.ingestion_config['twitter']['access_token_secret'] = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

        # Load RSS sources needed for worker config
        rss_sources = self._load_rss_sources(self.ingestion_config.get("rss_sources_file"))
        self.ingestion_config["rss_sources"] = rss_sources
        
        # Initialize Queue for IPC which is PROCESS SAFE
        from multiprocessing import Queue
        self.news_queue = Queue()
        
        # Remove StreamManager init from main process (it moves to Worker)
        # self.stream_manager = StreamManager(ingestion_config)
        # self.stream_manager.set_callback(self.process_news_item)

    def _load_config(self, path):
        with open(path, 'r') as f:
            return yaml.safe_load(f)

    def _load_rss_sources(self, path):
        # Allow path to be relative or absolute
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception:
            # Fallback for dev if path is wrong
            logger.warning(f"Could not load RSS sources from {path}, using defaults.")
            return ["http://feeds.reuters.com/reuters/businessNews"]

    # Old process_news_item removed. Replaced by _handle_news_item.

    async def _handle_news_item(self, item: NewsItem):
        """
        The Core Pipeline Logic:
        Ingest -> Memory Context -> Analyze -> Decision -> Execute -> Store Memory
        """
        logger.info(f"Received News from Queue: {item.title}")
        
        loop = asyncio.get_event_loop()
        text_to_analyze = item.title + " " + item.content
        
        # 0. Retrieve Historical Context
        similar_events = []
        if self.memory.enabled:
            # Run in executor to avoid blocking loop (vector search calculation)
            similar_events = await loop.run_in_executor(None, self.memory.search_similar, text_to_analyze)
            if similar_events:
                logger.info(f"🧠 Found {len(similar_events)} similar past events")
        
        # 1. Analyze (with context)
        # Note: We must ensure brain.analyze accepts the new argument or we update SentimentEngine wrapper too
        # checking SentimentEngine wrapper... usually it just forwards or we call specific model.
        # Ideally SentimentEngine.analyze should accept **kwargs and pass to model.
        # For now, let's assume we need to update SentimentEngine.analyze sig as well, 
        # but let's check if we can pass it directly.
        # self.brain is 'SentimentEngine'.
        
        # 1. Analyze (Ensemble - runs parallel internally)
        analysis = await self.brain.analyze(text_to_analyze, similar_events)
        
        logger.info(f"Sentiment: {analysis['label'].upper()} ({analysis['score']:.2f})")
        
        # Log to DB
        item.impact_score = analysis.get('impact', 0)
        self.db.log_news(item, analysis)
        
        # 2. Decide & Execute
        signal = {
            'source_item': item,
            'analysis': analysis,
            'symbol': 'BTC-PERP' # Default for now
        }
        
        await self.trader.execute_signal(signal)
        
        # 3. Store in Memory (Async)
        if self.memory.enabled:
            # Store with impact score for future reference
            metadata = {
                "source": item.source,
                "impact": item.impact_score,
                "label": analysis['label'],
                "timestamp": item.published_at.timestamp() if item.published_at else 0
            }
            # Fire and forget (in executor)
            loop.run_in_executor(None, self.memory.add_event, text_to_analyze, metadata)

    async def start(self):
        logger.info("Starting Hedgemony Engine v2 (Resilient)...")
        
        # 1. Start Ingestion Process
        from src.ingestion.worker import start_ingestion_worker
        from multiprocessing import Process
        
        # Spawn the worker process
        self.ingest_proc = Process(target=start_ingestion_worker, args=(self.news_queue, self.config))
        self.ingest_proc.daemon = True # Kill if main dies
        self.ingest_proc.start()
        
        logger.info(f"Ingestion Worker PID: {self.ingest_proc.pid}")
        
        # 2. Main Event Loop (Consumes Queue)
        try:
            while True:
                # Non-blocking check of the queue
                try:
                    while not self.news_queue.empty():
                         item = self.news_queue.get_nowait()
                         await self._handle_news_item(item)
                except Exception:
                    pass
                
                await asyncio.sleep(0.1) # Yield control
                
        except asyncio.CancelledError:
            logger.info("Engine Shutdown requested.")
        finally:
            logger.info("Terminating Ingest Process...")
            self.ingest_proc.terminate()
            self.ingest_proc.join()

if __name__ == "__main__":
    # Needed for MacOS spawn method safety
    import multiprocessing
    multiprocessing.set_start_method("spawn", force=True)
    
    engine = HedgemonyEngine()
    try:
        asyncio.run(engine.start())
    except KeyboardInterrupt:
        pass
