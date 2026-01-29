import logging
from typing import Dict

class ImpactScorer:
    """
    Assigns an Impact Score (1-10) to news items based on keywords and rules.
    1 = Noise / Irrelevant
    5 = Standard Market News
    10 = Black Swan / Critical Event
    """
    def __init__(self, config: dict = None):
        self.logger = logging.getLogger("hedgemony.brain.impact")
        self.config = config or {}
        
        # v1.5: Simple Keyword Rules
        # In v2.0: This will be replaced/augmented by an LLM
        self.high_impact_keywords = [
            "ETF approved", "SEC lawsuit", "Binance insolvent", "rate hike", 
            "war declared", "hack", "exploit", "peg lost", "bankruptcy",
            "Trump", "election", "sanctions", "nuclear", "missile", "invasion",
            "Fed", "Powell", "Gensler", "doj"
        ]
        
        self.medium_impact_keywords = [
            "partnership", "launch", "upgrade", "listing", "mainnet", 
            "volume surge", "whale", "inflation"
        ]

    def score(self, text: str) -> int:
        text_lower = text.lower()
        score = 1 # Default to low impact
        
        # Check High Impact
        for kw in self.high_impact_keywords:
            if kw.lower() in text_lower:
                score = 10
                self.logger.info(f"High Impact Keyword Found: {kw}")
                return score # Return immediately on max impact
                
        # Check Medium Impact
        for kw in self.medium_impact_keywords:
            if kw.lower() in text_lower:
                score = max(score, 5)
        
        return score
