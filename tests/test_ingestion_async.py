import pytest
import asyncio
from src.ingestion.stream_manager import StreamManager
from src.ingestion.cryptopanic import CryptoPanicIngester
from src.ingestion.base import NewsItem

# Mock Callback
class MockCallback:
    def __init__(self):
        self.items = []
        
    async def process(self, item: NewsItem):
        self.items.append(item)

@pytest.mark.asyncio
async def test_stream_manager_init():
    config = {
        "rss": {},
        "rss_sources": ["http://test.com/rss"],
        "cryptopanic": {"enabled": True, "api_key": "dummy"}
    }
    manager = StreamManager(config)
    assert len(manager.ingesters) == 2
    assert isinstance(manager.ingesters[1], CryptoPanicIngester)

@pytest.mark.asyncio
async def test_stream_manager_flow():
    # Setup
    config = {
        "rss": {},
        "rss_sources": [], # No RSS to keep it simple
        "cryptopanic": {"enabled": False} # Disable CP to test just manager logic first
    }
    manager = StreamManager(config)
    callback = MockCallback()
    manager.set_callback(callback.process)
    
    # Start (should exit immediately as no ingesters active or mocked)
    # But let's mock an ingester
    
    class MockIngester:
        def set_callback(self, cb): self.cb = cb
        async def start(self): 
            await self.cb(NewsItem("test", "Test Title", "http://url", None, "content"))
        async def stop(self): pass
        
    manager.ingesters = [MockIngester()]
    manager.set_callback(callback.process) # Re-bind
    
    await manager.start()
    assert len(callback.items) == 1
    assert callback.items[0].title == "Test Title"
