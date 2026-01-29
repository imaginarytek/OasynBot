
import json
import sqlite3
import argparse
from datetime import datetime

def export_data(db_path="data/hedgemony.db", output_file="data/training_data.jsonl"):
    """
    Exports news and sentiment data to JSONL format for fine-tuning.
    Format: {"prompt": "News Title", "completion": "Sentiment: X, Impact: Y"}
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    try:
        c.execute("SELECT * FROM news WHERE sentiment_label IS NOT NULL")
        rows = c.fetchall()
        
        with open(output_file, 'w') as f:
            count = 0
            for row in rows:
                # Construct a training example
                # We want the model to learn to predict Sentiment AND Impact from Title
                
                example = {
                    "messages": [
                        {"role": "system", "content": "You are a financial sentiment analysis expert. Analyze the news title for sentiment (positive/negative/neutral) and market impact score (1-10)."},
                        {"role": "user", "content": row['title']},
                        {"role": "assistant", "content": json.dumps({
                            "sentiment": row['sentiment_label'],
                            "impact": row['impact_score']
                        })}
                    ]
                }
                
                f.write(json.dumps(example) + "\n")
                count += 1
                
        print(f"Successfully exported {count} items to {output_file}")
        
    except Exception as e:
        print(f"Error exporting data: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="data/hedgemony.db")
    parser.add_argument("--out", default="data/training_data.jsonl")
    args = parser.parse_args()
    
    export_data(args.db, args.out)
