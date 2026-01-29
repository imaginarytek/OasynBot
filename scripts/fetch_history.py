
import sys
import os
import asyncio
import argparse
import sys
import yaml

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from src.utils.backfill import BackfillEngine

def load_config(path="config/config.yaml"):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

async def main():
    parser = argparse.ArgumentParser(description="Hedgemony Data Backfiller")
    parser.add_argument("--source", type=str, choices=["cryptopanic", "csv"], required=True, help="Source to backfill from")
    parser.add_argument("--file", type=str, help="Path to CSV file (if source=csv)")
    parser.add_argument("--pages", type=int, default=5, help="Number of pages to fetch (if source=cryptopanic)")
    
    args = parser.parse_args()
    config = load_config()
    
    engine = BackfillEngine(config)
    
    if args.source == "cryptopanic":
        print(f"Starting CryptoPanic Backfill (Pages: {args.pages})...")
        await engine.fetch_cryptopanic_history(pages=args.pages)
    elif args.source == "csv":
        if not args.file:
            print("Error: --file argument required for CSV source")
            return
        engine.import_csv(args.file)
        
    print("Backfill Complete.")

if __name__ == "__main__":
    asyncio.run(main())
