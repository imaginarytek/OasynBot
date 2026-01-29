from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch
import logging
from .impact import ImpactScorer

class SentimentEngine:
    _instance = None

    def __new__(cls, config=None):
        if cls._instance is None:
            cls._instance = super(SentimentEngine, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config=None):
        if self._initialized:
            return
            
        self.logger = logging.getLogger("hedgemony.brain.sentiment")
        self.config = config or {}
        self.impact_scorer = ImpactScorer(self.config)
        
        # Determine Model Type
        # Options: "finbert" (default), "groq"
        self.model_type = self.config.get("model_type", "finbert")
        if self.config.get("brain", {}).get("model_type"): # Handle nested config if present
             self.model_type = self.config.get("brain", {}).get("model_type")

        # Initialize Groq if enabled
        if self.model_type == "groq":
            try:
                from .llm_sentiment import GroqAnalyzer
                self.groq_analyzer = GroqAnalyzer(self.config)
                self.logger.info("🟢 AGENT 1: Groq (Reasoning) Initialized")
            except Exception as e:
                self.logger.error(f"Failed to init Groq: {e}")
                self.model_type = "finbert"

        # Initialize FinBERT (Agent 2 - The Banker)
        self._init_finbert()
        
        # Initialize DeBERTa (Agent 3 - The Logician)
        self._init_deberta()
            
        self._initialized = True

    def _init_finbert(self):
        """Initialize local FinBERT model."""
        try:
            model_name = self.config.get("finbert_model", "ProsusAI/finbert")
            self.logger.info(f"Loading AGENT 2: FinBERT... ({model_name})")
            
            # ... (Standard HF Load)
            from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
            import torch
            
            device = -1
            if torch.backends.mps.is_available(): device = "mps"
            
            self.finbert_pipe = pipeline("sentiment-analysis", model=model_name, device=device)
            self.logger.info("🟢 AGENT 2: FinBERT (Financial) Ready")
        except Exception as e:
            self.logger.error(f"Failed to load FinBERT: {e}")

    def _init_deberta(self):
        """Initialize DeBERTa Zero-Shot (Agent 3)."""
        try:
            model_name = "MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli"
            self.logger.info(f"Loading AGENT 3: DeBERTa... ({model_name})")
            
            from transformers import pipeline
            import torch
            device = -1
            if torch.backends.mps.is_available(): device = "mps"
            
            self.deberta_pipe = pipeline("zero-shot-classification", model=model_name, device=device)
            self.logger.info("🟢 AGENT 3: DeBERTa (Logic) Ready")
            
        except Exception as e:
            self.logger.warning(f"Failed to load DeBERTa: {e} (Will run with 2 agents)")
            self.deberta_pipe = None

    async def analyze(self, text: str, historical_events: list = None):
        """
        THE COUNCIL OF THREE (Voting System)
        ------------------------------------
        1. Groq (Reasoning)
        2. FinBERT (Finance Tone)
        3. DeBERTa (Logic/NLI)
        """
        import asyncio
        loop = asyncio.get_running_loop()

        # 1. Run All Agents in Parallel
        tasks = []
        
        # Agent 1: Groq
        if self.groq_analyzer:
            tasks.append(self.groq_analyzer.analyze(text, historical_events))
        else:
            tasks.append(asyncio.sleep(0, result={}))

        # Agent 2: FinBERT
        tasks.append(loop.run_in_executor(None, self._analyze_finbert, text))

        # Agent 3: DeBERTa
        tasks.append(loop.run_in_executor(None, self._analyze_deberta, text))

        # AWAIT RESULTS
        results = await asyncio.gather(*tasks)
        r_groq, r_finbert, r_deberta = results

        # 2. Collect Votes
        votes = []
        
        # Vote 1 (Groq)
        if r_groq and r_groq.get('score'):
            votes.append({
                'agent': 'Groq',
                'label': r_groq['label'], # 'positive', 'negative', 'neutral'
                'score': r_groq['score'], # 0 to 1 usually, need normalize? 
                # GroqAnalyzer returns normalized scalar? No check llm_sentiment.
                # Let's assume standardized labels: positive, negative, neutral.
                'conf': r_groq.get('confidence', 0.5)
            })

        # Vote 2 (FinBERT)
        if r_finbert:
            votes.append({
                'agent': 'FinBERT',
                'label': r_finbert['label'],
                'score': r_finbert['score'],
                'conf': r_finbert['confidence']
            })

        # Vote 3 (DeBERTa)
        if r_deberta:
            votes.append({
                'agent': 'DeBERTa',
                'label': r_deberta['label'],
                'score': r_deberta['score'],
                'conf': r_deberta['confidence']
            })

        # 3. The Council Decides (2/3 Rule)
        # Count ballots
        counts = {'positive': 0, 'negative': 0, 'neutral': 0}
        total_valid = 0
        
        for v in votes:
            if v['label'] in counts:
                # Weighted voting? Or straight 1-person-1-vote?
                # User asked for "2/3 Agree". Straight vote is safer against 1 hallucinating model.
                # However, we can trust Groq slightly more.
                weight = 1.0
                if v['agent'] == 'Groq': weight = 1.1 # Tie breaker
                
                counts[v['label']] += weight
                total_valid += 1
        
        # Determine Winner
        winner = max(counts, key=counts.get)
        support = counts[winner]
        
        # Consensus Check
        is_consensus = False
        if support >= 1.9: # Effectively 2 out of 3 (or 2 out of 2)
            is_consensus = True
            
        # Unanimous? (God Mode Trigger)
        is_unanimous = (support > 2.9)

        # Calculate Final Composite Score
        # Average the scores of the WINNING side only (to avoid dilution from the loser)
        winning_scores = [v['score'] for v in votes if v['label'] == winner]
        if winning_scores:
            final_score = sum(winning_scores) / len(winning_scores)
        else:
            final_score = 0.0

        # Construct Reasoning
        reasoning = f"Council Vote: {counts['positive']:.1f} bull / {counts['negative']:.1f} bear. "
        reasoning += f"Winner: {winner.upper()}. "
        if is_unanimous: reasoning += "GOD MODE (Unanimous). "
        elif not is_consensus: reasoning += "NO CONSENSUS (Trade Skipped). "
        
        # Override Label if specific Agent 1 veto? No, Democracy rules.
        
        return {
            'label': winner if is_consensus else 'neutral', # Force neutral if split decision
            'score': final_score if is_consensus else 0.0,
            'confidence': support / 3.0, # Approximate confidence
            'impact': max([v.get('impact', 0) for v in [r_groq, r_finbert] if isinstance(v, dict)]), # DeBERTa doesn't do impact
            'reasoning': reasoning
        }

    def _analyze_finbert(self, text):
        # ... (Keep existing logic, ensure return dict matches expected format)
        res = self.finbert_pipe(text[:512], truncation=True)[0]
        # Map label positive/negative/neutral
        l = res['label']
        s = res['score']
        if l == 'positive': score = s
        elif l == 'negative': score = -s
        else: score = 0
        return {'label': l, 'score': score, 'confidence': s}

    def _analyze_deberta(self, text):
        """Run Zero-Shot Classification"""
        if not self.deberta_pipe: return {}
        
        candidate_labels = ["bullish news", "bearish news", "neutral news"]
        res = self.deberta_pipe(text, candidate_labels)
        
        # res looks like {'labels': ['bullish news', ...], 'scores': [0.9, ...]}
        top_label = res['labels'][0]
        top_score = res['scores'][0]
        
        # Map back to standard keys
        label_map = {
            "bullish news": "positive",
            "bearish news": "negative", 
            "neutral news": "neutral"
        }
        
        std_label = label_map.get(top_label, "neutral")
        
        # Score direction
        score = top_score if std_label == 'positive' else -top_score if std_label == 'negative' else 0
        
        return {
            'label': std_label,
            'score': score, 
            'confidence': top_score,
            'reasoning': f"DeBERTa picked {top_label}"
        }
