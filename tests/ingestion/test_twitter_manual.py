import asyncio
import logging
from src.ingestion.twitter_monitor import TwitterMonitor

# Configure logging
logging.basicConfig(level=logging.INFO)

import os
from dotenv import load_dotenv

load_dotenv()

async def test_twitter_auth():
    print("Testing Twitter Monitor Initialization...")
    
    # Config with real keys from env
    config = {
        "enabled": True,
        "poll_interval": 60,
        "query": "test",
        "bearer_token": os.getenv("TWITTER_BEARER_TOKEN"),
        "api_key": os.getenv("TWITTER_API_KEY"),
        "api_secret": os.getenv("TWITTER_API_SECRET"),
        "access_token": os.getenv("TWITTER_ACCESS_TOKEN"),
        "access_token_secret": os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
    }
    
    monitor = TwitterMonitor(config)
    
    print("Starting monitor (expecting success if keys are valid)...")
    await monitor.start()
    
    # Use internal state to verify it started
    if monitor.running:
        print("SUCCESS: Monitor started successfully with valid keys.")
        await monitor.stop()
    else:
        print("FAILURE: Monitor failed to start.")

if __name__ == "__main__":
    asyncio.run(test_twitter_auth())
