from src.core.engine import HedgemonyEngine
import asyncio

if __name__ == "__main__":
    engine = HedgemonyEngine()
    try:
        asyncio.run(engine.start())
    except KeyboardInterrupt:
        print("Stopping Hedgemony Bot...")
