import unittest
import asyncio
from unittest.mock import MagicMock, patch
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.brain.sentiment import SentimentEngine

class TestBrainCouncil(unittest.TestCase):
    
    def setUp(self):
        # We patch the init methods to avoid downloading models during logic test
        self.patcher1 = patch('src.brain.sentiment.SentimentEngine._init_finbert')
        self.patcher2 = patch('src.brain.sentiment.SentimentEngine._init_deberta')
        self.mock_init_finbert = self.patcher1.start()
        self.mock_init_deberta = self.patcher2.start()
    
    def tearDown(self):
        self.patcher1.stop()
        self.patcher2.stop()

    async def run_voting_test(self, vote_groq, vote_finbert, vote_deberta):
        # Initialize Engine (Mocked models)
        engine = SentimentEngine()
        
        # MOCK THE AGENTS OUTPUTS
        # 1. Groq
        if vote_groq:
            engine.groq_analyzer = MagicMock()
            engine.groq_analyzer.analyze = asyncio.coroutine(lambda *args: vote_groq)
        else:
            engine.groq_analyzer = None

        # 2. FinBERT (Mock _analyze_finbert)
        engine._analyze_finbert = MagicMock(return_value=vote_finbert)

        # 3. DeBERTa (Mock _analyze_deberta)
        engine._analyze_deberta = MagicMock(return_value=vote_deberta)

        # RUN ANALYSIS
        # We need to mock asyncio.gather since we are running in a sync test wrapper usually, 
        # but here we can just run the async method directly in the loop.
        # Actually, let's just call analyze() since it uses loop.run_in_executor for the sync parts.
        # We might need to patch loop.run_in_executor to just run the function.
        
        with patch('asyncio.get_running_loop') as mock_loop:
             mock_loop.return_value.run_in_executor = asyncio.coroutine(lambda _, func, *args: func(*args))
             # Re-wire gather to just return the 3 results
             # Ideally we just run the real method.
             pass

        # To simplify, we will just TEST THE VOTING LOGIC block by simulation?
        # No, let's try to run `analyze` as is, but we need an event loop.
        
        return await engine.analyze("Test Text")


    def test_bullish_consensus_2_vs_1(self):
        """Test that 2 Bulls vs 1 Bear results in Bullish Consensus"""
        print("\n🧪 TEST: Bullish Consensus (2 vs 1)")
        
        # Groq: Bull
        v_groq = {'label': 'positive', 'score': 0.8, 'confidence': 0.9}
        # FinBERT: Bull
        v_fin = {'label': 'positive', 'score': 0.7, 'confidence': 0.8}
        # DeBERTa: Bear (Dissenter)
        v_deb = {'label': 'negative', 'score': -0.6, 'confidence': 0.7}
        
        # Run
        result = asyncio.run(self.run_voting_test(v_groq, v_fin, v_deb))
        
        print(f"   Inputs: Groq(Bull), Fin(Bull), Deb(Bear)")
        print(f"   Result: {result['label'].upper()} (Conf: {result['confidence']:.2f})")
        print(f"   Reason: {result['reasoning']}")
        
        self.assertEqual(result['label'], 'positive')
        self.assertTrue(result['score'] > 0)
        print("   ✅ PASSED")

    def test_bearish_consensus_3_vs_0(self):
        """Test God Mode (Unanimous Bear)"""
        print("\n🧪 TEST: God Mode (Unanimous Bear)")
        
        v_groq = {'label': 'negative', 'score': -0.9, 'confidence': 0.9}
        v_fin = {'label': 'negative', 'score': -0.8, 'confidence': 0.9}
        v_deb = {'label': 'negative', 'score': -0.7, 'confidence': 0.9}
        
        result = asyncio.run(self.run_voting_test(v_groq, v_fin, v_deb))
        
        print(f"   Inputs: All Bear")
        print(f"   Result: {result['label'].upper()}")
        print(f"   Reason: {result['reasoning']}")
        
        self.assertIn("GOD MODE", result['reasoning'])
        self.assertEqual(result['label'], 'negative')
        print("   ✅ PASSED")

    def test_no_consensus_1_1_1(self):
        """Test Split Vote (Bull/Bear/Neutral) -> Skip"""
        print("\n🧪 TEST: Chaos (No Consensus)")
        
        v_groq = {'label': 'positive', 'score': 0.5, 'confidence': 0.6}
        v_fin = {'label': 'negative', 'score': -0.5, 'confidence': 0.6}
        v_deb = {'label': 'neutral', 'score': 0.0, 'confidence': 0.6}
        
        result = asyncio.run(self.run_voting_test(v_groq, v_fin, v_deb))
        
        print(f"   Inputs: Bull, Bear, Neutral")
        print(f"   Result: {result['label'].upper()}")
        
        self.assertEqual(result['label'], 'neutral') # Should default to neutral/skip
        self.assertIn("NO CONSENSUS", result['reasoning'])
        print("   ✅ PASSED")

if __name__ == '__main__':
    unittest.main()
