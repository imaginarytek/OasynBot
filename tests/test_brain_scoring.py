import pytest
from src.brain.impact import ImpactScorer

def test_impact_scorer_defaults():
    scorer = ImpactScorer()
    # "hello world" -> 1 (Low)
    assert scorer.score("hello world") == 1

def test_high_impact():
    scorer = ImpactScorer()
    # "SEC lawsuit" -> 10
    assert scorer.score("The SEC lawsuit against Binance is huge") == 10
    assert scorer.score("ETF APPROVED by regulators") == 10

def test_medium_impact():
    scorer = ImpactScorer()
    # "partnership" -> 5
    assert scorer.score("New partnership announced with Google") == 5
    
def test_priority():
    scorer = ImpactScorer()
    # "partnership" (5) + "SEC lawsuit" (10) -> Should be 10
    assert scorer.score("Partnership announced despite SEC lawsuit") == 10
