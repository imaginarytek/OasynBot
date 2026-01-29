"""
Groq LLM Sentiment Analyzer

Uses Llama-3 models via Groq API for ultra-fast, reasoning-based sentiment analysis.
Outputs structured JSON with impact scores and reasoning.
"""

import os
import json
import logging
from typing import Dict, Any, Optional

try:
    from groq import AsyncGroq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

class GroqAnalyzer:
    """
    Sentiment analyzer using Groq API (Llama-3).
    """
    
    def __init__(self, config: dict = None):
        self.logger = logging.getLogger("hedgemony.brain.groq")
        self.config = config or {}
        
        if not GROQ_AVAILABLE:
            self.logger.error("Groq library not installed. Run: pip install groq")
            raise ImportError("groq library required")
            
        self.api_key = self.config.get("groq", {}).get("api_key") or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            self.logger.warning("GROQ_API_KEY not found. LLM sentiment will fail.")
            
        self.client = AsyncGroq(api_key=self.api_key)
        self.model = self.config.get("groq", {}).get("model", "llama-3.3-70b-versatile")
        
        self.system_prompt = """
        You are an expert financial sentiment analyzer for a high-frequency trading bot.
        Analyze the given news headline/text for its immediate impact on crypto (BTC, ETH).
        
        CRITICAL RULES:
        1. 'Sanction' usually means PENALTY (Negative), unless 'Officially Sanctioned' in a regulatory approval context.
        2. 'Approves', 'Greenlight', 'Win', 'Launch' -> POSITIVE (Score 0.8-1.0)
        3. 'Ban', 'Sue', 'Hack', 'Reject', 'Delay' -> NEGATIVE (Score 0.0-0.2)
        4. 'Launch Investigation', 'Subpoena' -> NEGATIVE.
        
        Output valid JSON only. No markdown, no preamble.
        
        Schema:
        {
            "sentiment": "positive" | "negative" | "neutral",
            "score": float (0.0 to 1.0, 1.0 = positive/bullish, 0.0 = negative/bearish, 0.5 = neutral),
            "confidence": float (0.0 to 1.0),
            "impact": int (1 to 10, where 10 is market-crashing news),
            "reasoning": "brief explanation (max 15 words)"
        }
        """

    async def analyze(self, text: str, historical_events: list = None) -> Dict[str, Any]:
        """
        Analyze text and return structured sentiment.
        Optionally uses historical_events to ground the reasoning.
        """
        if not self.api_key:
            return {"label": "neutral", "score": 0.5, "confidence": 0.0, "impact": 0, "reasoning": "No API Key"}

        # Construct Context String if available
        context_str = ""
        if historical_events:
            context_str = "\nSimilar Past Events & Outcomes:\n"
            for event in historical_events:
                # event format from memory.search_similar
                # {'text': '...', 'metadata': {'impact': 8}, 'similarity': 0.85}
                meta = event.get('metadata', {})
                context_str += f"- '{event.get('text', '')[:100]}...' (Impact: {meta.get('impact', '?')})\n"
            
            context_str += "\nUse these precedents to inform your impact score and reasoning."

        try:
            chat_completion = await self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": self.system_prompt
                    },
                    {
                        "role": "user",
                        "content": f"News: {text}\n{context_str}"
                    }
                ],
                model=self.model,
                temperature=0.1, # Low temp for deterministic JSON
                response_format={"type": "json_object"},
            )
            
            response_content = chat_completion.choices[0].message.content
            result = json.loads(response_content)
            
            # Normalize keys if needed
            sentiment_score = result.get("score", 0.5)
            # Map score 0-1 to label if not provided clearly
            
            label = result.get("sentiment", "neutral").lower()
            if label not in ['positive', 'negative', 'neutral']:
                # Fallback mapping
                if sentiment_score > 0.6: label = 'positive'
                elif sentiment_score < 0.4: label = 'negative'
                else: label = 'neutral'

            return {
                "label": label,
                "score": sentiment_score, 
                "confidence": result.get("confidence", 0.5),
                "impact": result.get("impact", 1),
                "reasoning": result.get("reasoning", "")
            }
            
        except Exception as e:
            self.logger.error(f"Groq Analysis Failed: {e}")
            self.logger.debug(f"Failed Text: {text}")
            # return error structure
            return {
                "label": "neutral", 
                "score": 0.5, 
                "confidence": 0.0,
                "error": str(e)
            }
