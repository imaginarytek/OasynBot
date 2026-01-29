import time
import asyncio
import logging
import traceback
from multiprocessing import Queue
from src.ingestion.stream_manager import StreamManager
from src.utils.db import Database

class IngestionWorker:
    """
    Standalone worker process that fetches news and pushes to a queue.
    Run this in a separate multiprocessing.Process.
    """
    def __init__(self, queue: Queue, config: dict):
        self.queue = queue
        self.config = config
        self.logger = logging.getLogger("hedgemony.ingestion.worker")
        
    def run(self):
        """Entry point for the worker process."""
        # Re-configure logging for this process
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - WORKER - %(levelname)s - %(message)s'
        )
        self.logger.info("🟢 Ingestion Worker Started")
        
        try:
            asyncio.run(self._async_run())
        except KeyboardInterrupt:
            self.logger.info("Worker stopped by user")
        except Exception as e:
            self.logger.error(f"Critical Worker Failure: {e}")
            traceback.print_exc()

    async def _handle_stream_item(self, item):
        """Callback for stream manager to push to queue."""
        try:
            self.queue.put(item)
            self.logger.info(f"Pushed item to queue: {item.title[:50]}...")
        except Exception as e:
            self.logger.error(f"Failed to push to queue: {e}")

    async def _async_run(self):
        """Async loop within the worker process."""
        self.db = Database() # New connection for this process
        self.stream_manager = StreamManager(self.config)
        
        # Connect Pipeline: Stream -> Worker Callback -> Multiprocessing Queue
        self.stream_manager.set_callback(self._handle_stream_item)
        
        # Start Ingesters (RSS, Twitter, etc. run as background tasks)
        await self.stream_manager.start()
        
        self.logger.info("🟢 Ingestion Streams Active. Waiting for events...")

        # Keep process alive
        try:
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            self.logger.info("Worker shutting down...")
            await self.stream_manager.stop()
# Helper for spawning
def start_ingestion_worker(queue, config):
    worker = IngestionWorker(queue, config)
    worker.run()
