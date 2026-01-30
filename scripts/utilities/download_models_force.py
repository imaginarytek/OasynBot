import os
from huggingface_hub import snapshot_download
import logging

logging.basicConfig(level=logging.INFO)

MODELS = [
    "ProsusAI/finbert",
    "MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli"
]

def force_download():
    print("🚀 Starting ROBUST Model Download...")
    
    for model_id in MODELS:
        print(f"\n⬇️  Downloading: {model_id}")
        try:
            path = snapshot_download(repo_id=model_id, resume_download=True, max_workers=8)
            print(f"✅ Successfully downloaded {model_id} to {path}")
        except Exception as e:
            print(f"❌ Failed to download {model_id}: {e}")
            
    print("\n🎉 All downloads attempted.")

if __name__ == "__main__":
    force_download()
