
import asyncio
import logging
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.core.engine import HedgemonyEngine

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("hedgemony.verify")

async def main():
    logger.info("Starting HFT Pipeline Verification...")
    
    # Initialize Engine (loads config, models, and stream manager)
    try:
        engine = HedgemonyEngine()
        
        # Start Engine in background task
        task = asyncio.create_task(engine.start())
        
        logger.info("Engine started. Listening for 30 seconds...")
        await asyncio.sleep(30)
        
        # Shutdown
        logger.info("Stopping Engine...")
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            logger.info("Engine Stopped Cleanly.")
            
    except Exception as e:
        logger.error(f"Verification Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
