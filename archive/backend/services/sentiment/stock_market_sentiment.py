#!/usr/bin/env python3
"""
Enhanced Stock Market Sentiment Analysis Module for Crypto ML Training
=====================================================================

This module provides advanced sentiment analysis specifically designed for stock market news
to generate valuable insights for cryptocurrency ML training models. It combines multiple 
state-of-the-art techniques to extract actionable trading signals.

Key Features:
- Financial sentiment analysis with FinBERT and other specialized models
- Market psychology indicators (fear, greed, volatility sentiment)
- Cross-asset correlation sentiment (stock market impact on crypto)
- Economic indicator sentiment (macro economic impact)
- Technical analysis sentiment (chart patterns in news)
- Sector rotation signals
- Risk appetite indicators
- News momentum and acceleration metrics

This data will be used to train ML models for crypto trading decisions by understanding
how traditional financial market sentiment affects cryptocurrency prices.
"""

import os
import sys
import logging
import traceback
import json
import re
import math
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
import numpy as np

# Add backend path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'collectors', 'stockmarketnews'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('stock_market_sentiment')

# Import dependencies with fallbacks
try:
    import torch
    from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    logger.warning("transformers not available - using fallback methods")
    TRANSFORMERS_AVAILABLE = False
    torch = None

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
except ImportError:
    logger.warning("VADER not available")
    VADER_AVAILABLE = False

try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    logger.warning("TextBlob not available")
    TEXTBLOB_AVAILABLE = False

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except (ImportError, Exception) as e:
    logger.warning(f"yfinance not available for market data: {e}")
    YFINANCE_AVAILABLE = False
    yf = None

try:
    from stock_definitions import TOP_100_STOCKS, MAJOR_INDICES, STOCK_SECTORS
    STOCK_DEFINITIONS_AVAILABLE = True
except (ImportError, Exception) as e:
    logger.warning(f"stock_definitions not available - using fallback: {e}")
    STOCK_DEFINITIONS_AVAILABLE = False
    TOP_100_STOCKS = {}
    MAJOR_INDICES = {}
    STOCK_SECTORS = {}

class StockMarketSentimentAnalyzer:
    """Advanced sentiment analyzer for stock market news with crypto ML focus"""
    
    def __init__(self):
        """Initialize the sentiment analyzer"""
        self.finbert_model = None
        self.finbert_tokenizer = None
        self.crypto_impact_model = None
        self.models_loaded = False
        
        # Market psychology indicators
        self.fear_greed_indicators = self._load_fear_greed_indicators()
        self.volatility_indicators = self._load_volatility_indicators()
        self.risk_indicators = self._load_risk_indicators()
        
        # Economic correlation patterns
        self.macro_economic_patterns = self._load_macro_patterns()
        self.sector_rotation_patterns = self._load_sector_patterns()
        
        # Load models
        self._load_models()
        
        logger.info("🧠 Stock Market Sentiment Analyzer initialized")
    
    def _load_models(self):
        """Load specialized financial sentiment models"""
        if not TRANSFORMERS_AVAILABLE:
            logger.warning("⚠️ Transformers not available - using rule-based methods only")
            return
        
        try:
            # Load FinBERT for financial sentiment
            logger.info("📥 Loading FinBERT model for financial sentiment...")
            self.finbert_tokenizer = AutoTokenizer.from_pretrained(
                "ProsusAI/finbert",
                cache_dir=os.path.join(os.path.dirname(__file__), "model_cache", "finbert")
            )
            self.finbert_model = AutoModelForSequenceClassification.from_pretrained(
                "ProsusAI/finbert", 
                cache_dir=os.path.join(os.path.dirname(__file__), "model_cache", "finbert")
            )
            
            logger.info("✅ FinBERT model loaded successfully")
            self.models_loaded = True
            
        except Exception as e:
            logger.error(f"❌ Error loading FinBERT model: {e}")
            logger.info("🔄 Falling back to rule-based analysis")
    
    def _load_fear_greed_indicators(self) -> Dict[str, float]:
        """Load fear and greed sentiment indicators"""
        return {
            # Fear indicators (negative sentiment amplifiers)
            'panic': -0.9, 'crash': -0.9, 'collapse': -0.9, 'meltdown': -0.8,
            'fear': -0.7, 'anxiety': -0.6, 'uncertainty': -0.6, 'concern': -0.5,
            'worry': -0.5, 'risk-off': -0.6, 'flight to safety': -0.7,
            'sell-off': -0.7, 'liquidation': -0.8, 'capitulation': -0.9,
            'bearish': -0.6, 'pessimistic': -0.5, 'negative outlook': -0.6,
            
            # Greed indicators (positive sentiment amplifiers)
            'euphoria': 0.9, 'exuberance': 0.8, 'optimism': 0.7, 'bullish': 0.7,
            'rally': 0.7, 'surge': 0.8, 'boom': 0.8, 'momentum': 0.6,
            'risk-on': 0.6, 'appetite for risk': 0.7, 'buying spree': 0.8,
            'accumulation': 0.6, 'institutional buying': 0.7, 'inflows': 0.6,
            'positive outlook': 0.6, 'confident': 0.6, 'strong demand': 0.7
        }
    
    def _load_volatility_indicators(self) -> Dict[str, float]:
        """Load volatility sentiment indicators"""
        return {
            # High volatility (often negative for traditional assets)
            'volatile': -0.4, 'volatility spike': -0.6, 'wild swings': -0.5,
            'choppy': -0.4, 'erratic': -0.5, 'unstable': -0.6,
            'turbulent': -0.5, 'whipsaw': -0.6,
            
            # Low volatility (stability indicators)
            'stable': 0.4, 'steady': 0.4, 'calm': 0.5, 'orderly': 0.4,
            'range-bound': 0.2, 'consolidation': 0.3, 'low volatility': 0.4,
            
            # Directional volatility
            'breakout': 0.6, 'breakdown': -0.6, 'momentum surge': 0.7,
            'trend acceleration': 0.5, 'explosive move': 0.4
        }
    
    def _load_risk_indicators(self) -> Dict[str, float]:
        """Load risk appetite indicators"""
        return {
            # Risk-off sentiment
            'safe haven': -0.5, 'defensive': -0.4, 'quality': 0.3,
            'treasury rally': -0.3, 'dollar strength': -0.3, 'gold rally': -0.4,
            'credit spreads widening': -0.6, 'risk aversion': -0.7,
            
            # Risk-on sentiment  
            'risk appetite': 0.6, 'yield chase': 0.5, 'carry trade': 0.4,
            'leveraged buying': 0.5, 'margin expansion': 0.4,
            'credit spreads tightening': 0.5, 'junk bonds rally': 0.6,
            
            # Leverage indicators
            'deleveraging': -0.7, 'margin calls': -0.8, 'forced selling': -0.8,
            'leverage increase': 0.4, 'margin buying': 0.3
        }
    
    def _load_macro_patterns(self) -> Dict[str, Dict[str, float]]:
        """Load macroeconomic sentiment patterns that affect crypto"""
        return {
            'fed_policy': {
                'rate hike': -0.6, 'rate cut': 0.7, 'dovish': 0.6, 'hawkish': -0.6,
                'quantitative easing': 0.8, 'tapering': -0.5, 'tightening': -0.6,
                'loose monetary policy': 0.7, 'accommodative': 0.6,
                'inflation concerns': -0.4, 'deflation risk': -0.5
            },
            'economic_data': {
                'gdp growth': 0.5, 'recession': -0.8, 'expansion': 0.6,
                'unemployment rising': -0.6, 'job growth': 0.5,
                'consumer confidence': 0.4, 'business sentiment': 0.4,
                'manufacturing pmi': 0.3, 'services pmi': 0.3
            },
            'global_events': {
                'geopolitical tension': -0.7, 'trade war': -0.6, 'sanctions': -0.5,
                'peace talks': 0.4, 'trade deal': 0.6, 'cooperation': 0.3,
                'oil shock': -0.6, 'energy crisis': -0.7, 'supply chain': -0.4
            }
        }
    
    def _load_sector_patterns(self) -> Dict[str, float]:
        """Load sector rotation patterns indicating risk sentiment"""
        return {
            # Growth sectors (risk-on, crypto positive)
            'technology outperform': 0.6, 'growth stocks rally': 0.7,
            'momentum stocks': 0.5, 'high beta': 0.4, 'speculative': 0.3,
            
            # Value/Defensive sectors (risk-off, crypto negative)
            'utilities outperform': -0.4, 'consumer staples': -0.3,
            'defensive rotation': -0.5, 'value stocks': -0.2,
            'dividend stocks': -0.2, 'low beta': -0.3,
            
            # Cyclical indicators
            'financials rally': 0.4, 'energy surge': 0.3, 'materials rally': 0.3,
            'industrials strength': 0.4, 'real estate': 0.2
        }
    
    def finbert_sentiment(self, text: str) -> Tuple[float, Dict[str, float], float]:
        """
        Analyze financial sentiment using FinBERT model
        
        Returns:
            Tuple of (sentiment_score, class_probabilities, confidence)
        """
        if not self.models_loaded or not TRANSFORMERS_AVAILABLE:
            return self._fallback_financial_sentiment(text)
        
        try:
            # Tokenize and predict
            inputs = self.finbert_tokenizer(text, return_tensors="pt", truncation=True, 
                                          padding=True, max_length=512)
            
            with torch.no_grad():
                outputs = self.finbert_model(**inputs)
                probabilities = torch.nn.functional.softmax(outputs.logits, dim=-1)
                probs = probabilities[0].tolist()
            
            # FinBERT classes: ['positive', 'negative', 'neutral']
            positive_prob = probs[0]
            negative_prob = probs[1] 
            neutral_prob = probs[2]
            
            # Calculate sentiment score (-1 to 1)
            sentiment_score = positive_prob - negative_prob
            
            # Confidence is the max probability
            confidence = max(probs)
            
            class_probs = {
                'positive': positive_prob,
                'negative': negative_prob,
                'neutral': neutral_prob
            }
            
            return sentiment_score, class_probs, confidence
            
        except Exception as e:
            logger.warning(f"FinBERT analysis failed: {e}")
            return self._fallback_financial_sentiment(text)
    
    def _fallback_financial_sentiment(self, text: str) -> Tuple[float, Dict[str, float], float]:
        """Fallback financial sentiment analysis using rules"""
        text_lower = text.lower()
        
        # Financial keywords with weights
        positive_financial = {
            'earnings beat': 0.8, 'revenue growth': 0.7, 'profit surge': 0.8,
            'buyback': 0.6, 'dividend increase': 0.6, 'guidance raised': 0.7,
            'strong results': 0.7, 'exceeds expectations': 0.8, 'record high': 0.8,
            'all-time high': 0.9, 'breakthrough': 0.7, 'innovation': 0.6
        }
        
        negative_financial = {
            'earnings miss': 0.8, 'revenue decline': 0.7, 'loss widens': 0.8,
            'guidance cut': 0.7, 'layoffs': 0.6, 'restructuring': 0.5,
            'bankruptcy': 0.9, 'default': 0.9, 'downgrade': 0.7, 'warning': 0.6,
            'investigation': 0.7, 'fraud': 0.9, 'lawsuit': 0.6
        }
        
        pos_score = sum(weight for keyword, weight in positive_financial.items() 
                       if keyword in text_lower)
        neg_score = sum(weight for keyword, weight in negative_financial.items() 
                       if keyword in text_lower)
        
        total_score = pos_score + neg_score
        if total_score == 0:
            return 0.0, {'positive': 0.33, 'negative': 0.33, 'neutral': 0.34}, 0.2
        
        sentiment = (pos_score - neg_score) / (total_score + 1)
        confidence = min(0.8, total_score * 0.2 + 0.2)
        
        if sentiment > 0:
            pos_prob = 0.5 + sentiment * 0.4
            neg_prob = max(0.1, 0.5 - sentiment * 0.4)
        else:
            neg_prob = 0.5 + abs(sentiment) * 0.4
            pos_prob = max(0.1, 0.5 - abs(sentiment) * 0.4)
        
        neu_prob = 1.0 - pos_prob - neg_prob
        
        return sentiment, {'positive': pos_prob, 'negative': neg_prob, 'neutral': neu_prob}, confidence
    
    def market_psychology_sentiment(self, text: str) -> Dict[str, float]:
        """
        Analyze market psychology indicators from text
        
        Returns:
            Dictionary with fear/greed, volatility, and risk scores
        """
        text_lower = text.lower()
        
        # Fear/Greed analysis
        fear_greed_score = 0.0
        for indicator, weight in self.fear_greed_indicators.items():
            if indicator in text_lower:
                fear_greed_score += weight
        
        # Volatility analysis
        volatility_score = 0.0
        for indicator, weight in self.volatility_indicators.items():
            if indicator in text_lower:
                volatility_score += weight
        
        # Risk appetite analysis
        risk_score = 0.0
        for indicator, weight in self.risk_indicators.items():
            if indicator in text_lower:
                risk_score += weight
        
        # Normalize scores
        fear_greed_score = max(-1.0, min(1.0, fear_greed_score))
        volatility_score = max(-1.0, min(1.0, volatility_score))
        risk_score = max(-1.0, min(1.0, risk_score))
        
        return {
            'fear_greed_score': fear_greed_score,
            'volatility_sentiment': volatility_score,
            'risk_appetite': risk_score
        }
    
    def macro_economic_sentiment(self, text: str) -> Dict[str, float]:
        """
        Analyze macroeconomic sentiment that affects crypto markets
        
        Returns:
            Dictionary with macro economic sentiment scores
        """
        text_lower = text.lower()
        macro_scores = {}
        
        for category, patterns in self.macro_economic_patterns.items():
            category_score = 0.0
            matches = 0
            
            for pattern, weight in patterns.items():
                if pattern in text_lower:
                    category_score += weight
                    matches += 1
            
            if matches > 0:
                category_score = category_score / matches  # Average
                
            macro_scores[f'{category}_sentiment'] = max(-1.0, min(1.0, category_score))
        
        return macro_scores
    
    def sector_rotation_sentiment(self, text: str) -> float:
        """
        Analyze sector rotation patterns for crypto correlation
        
        Returns:
            Sector rotation sentiment score (-1 to 1)
        """
        text_lower = text.lower()
        rotation_score = 0.0
        matches = 0
        
        for pattern, weight in self.sector_rotation_patterns.items():
            if pattern in text_lower:
                rotation_score += weight
                matches += 1
        
        if matches > 0:
            rotation_score = rotation_score / matches
            
        return max(-1.0, min(1.0, rotation_score))
    
    def extract_market_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract market entities (stocks, indices, sectors) mentioned in text
        
        Returns:
            Dictionary with entity types and their mentions
        """
        text_lower = text.lower()
        entities = {
            'stocks': [],
            'indices': [],
            'sectors': [],
            'currencies': [],
            'commodities': []
        }
        
        # Extract stock mentions
        if STOCK_DEFINITIONS_AVAILABLE:
            for symbol, data in TOP_100_STOCKS.items():
                if symbol.lower() in text_lower:
                    entities['stocks'].append(symbol)
                for alias in data.get('aliases', []):
                    if alias.lower() in text_lower:
                        entities['stocks'].append(symbol)
                        break
            
            # Extract index mentions
            for symbol, data in MAJOR_INDICES.items():
                if symbol.lower() in text_lower:
                    entities['indices'].append(symbol)
                for alias in data.get('aliases', []):
                    if alias.lower() in text_lower:
                        entities['indices'].append(symbol)
                        break
        
        # Extract common financial entities
        currency_patterns = [r'\busd\b', r'\beur\b', r'\bgbp\b', r'\bjpy\b', r'\bcny\b']
        for pattern in currency_patterns:
            matches = re.findall(pattern, text_lower)
            entities['currencies'].extend(matches)
        
        commodity_patterns = [r'\bgold\b', r'\bsilver\b', r'\boil\b', r'\bcopper\b', r'\bnatural gas\b']
        for pattern in commodity_patterns:
            matches = re.findall(pattern, text_lower)
            entities['commodities'].extend(matches)
        
        # Remove duplicates
        for key in entities:
            entities[key] = list(set(entities[key]))
        
        return entities
    
    def calculate_news_momentum(self, text: str, timestamp: datetime) -> Dict[str, float]:
        """
        Calculate news momentum and acceleration indicators
        
        Returns:
            Dictionary with momentum metrics
        """
        # Urgency indicators
        urgency_keywords = {
            'breaking': 0.9, 'urgent': 0.8, 'alert': 0.7, 'flash': 0.8,
            'developing': 0.6, 'latest': 0.5, 'update': 0.4, 'now': 0.3
        }
        
        # Impact indicators
        impact_keywords = {
            'major': 0.8, 'significant': 0.7, 'massive': 0.9, 'huge': 0.8,
            'dramatic': 0.8, 'unprecedented': 0.9, 'historic': 0.8,
            'landmark': 0.7, 'milestone': 0.6
        }
        
        text_lower = text.lower()
        
        urgency_score = sum(weight for keyword, weight in urgency_keywords.items() 
                          if keyword in text_lower)
        impact_score = sum(weight for keyword, weight in impact_keywords.items() 
                         if keyword in text_lower)
        
        # Time-based momentum (news recency boost)
        now = datetime.now(timezone.utc)
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        
        time_diff = (now - timestamp).total_seconds() / 3600  # hours
        time_decay = math.exp(-time_diff / 24)  # Exponential decay over 24 hours
        
        momentum_score = (urgency_score + impact_score) * time_decay
        
        return {
            'news_urgency': min(1.0, urgency_score),
            'news_impact': min(1.0, impact_score), 
            'time_decay_factor': time_decay,
            'overall_momentum': min(1.0, momentum_score)
        }
    
    def crypto_correlation_sentiment(self, text: str, market_entities: Dict[str, List[str]]) -> float:
        """
        Calculate sentiment specifically for crypto correlation
        
        Returns:
            Crypto correlation sentiment score (-1 to 1)
        """
        # Patterns that indicate strong crypto correlation
        crypto_positive_patterns = [
            'risk-on sentiment', 'tech rally', 'growth stocks surge', 
            'speculative appetite', 'momentum trade', 'retail investor',
            'young investor', 'fintech', 'digital assets', 'blockchain',
            'institutional adoption', 'innovation', 'disruption'
        ]
        
        crypto_negative_patterns = [
            'risk-off sentiment', 'flight to quality', 'defensive rotation',
            'traditional assets', 'safe haven demand', 'stability',
            'regulation', 'ban', 'crackdown', 'investigation'
        ]
        
        text_lower = text.lower()
        
        positive_count = sum(1 for pattern in crypto_positive_patterns if pattern in text_lower)
        negative_count = sum(1 for pattern in crypto_negative_patterns if pattern in text_lower)
        
        # Weight by entity types that correlate with crypto
        entity_weight = 0.0
        if market_entities['stocks']:
            # Tech stocks have higher crypto correlation
            entity_weight += 0.3
        if 'NASDAQ' in market_entities['indices']:
            entity_weight += 0.4  # NASDAQ correlates strongly with crypto
        
        total_patterns = positive_count + negative_count
        if total_patterns == 0:
            return 0.0
        
        base_sentiment = (positive_count - negative_count) / total_patterns
        weighted_sentiment = base_sentiment * (1 + entity_weight)
        
        return max(-1.0, min(1.0, weighted_sentiment))

def generate_enhanced_sentiment_features(text: str, timestamp: datetime = None) -> Dict[str, Any]:
    """
    Generate comprehensive sentiment features for ML training
    
    Args:
        text: News article text
        timestamp: Article timestamp (defaults to now)
        
    Returns:
        Dictionary with all sentiment features for ML training
    """
    if timestamp is None:
        timestamp = datetime.now(timezone.utc)
    
    analyzer = StockMarketSentimentAnalyzer()
    
    # Core sentiment analysis
    finbert_score, finbert_probs, finbert_confidence = analyzer.finbert_sentiment(text)
    
    # Market psychology
    psychology = analyzer.market_psychology_sentiment(text)
    
    # Macro economic sentiment
    macro_sentiment = analyzer.macro_economic_sentiment(text)
    
    # Sector rotation
    sector_sentiment = analyzer.sector_rotation_sentiment(text)
    
    # Extract entities
    entities = analyzer.extract_market_entities(text)
    
    # News momentum
    momentum = analyzer.calculate_news_momentum(text, timestamp)
    
    # Crypto correlation
    crypto_correlation = analyzer.crypto_correlation_sentiment(text, entities)
    
    # Additional ML features
    ml_features = {
        # Core FinBERT sentiment
        'finbert_sentiment_score': finbert_score,
        'finbert_positive_prob': finbert_probs['positive'],
        'finbert_negative_prob': finbert_probs['negative'],
        'finbert_neutral_prob': finbert_probs['neutral'],
        'finbert_confidence': finbert_confidence,
        
        # Market psychology features
        'fear_greed_score': psychology['fear_greed_score'],
        'volatility_sentiment': psychology['volatility_sentiment'],
        'risk_appetite_score': psychology['risk_appetite'],
        
        # Macro economic features
        **macro_sentiment,
        
        # Sector and correlation features
        'sector_rotation_sentiment': sector_sentiment,
        'crypto_correlation_score': crypto_correlation,
        
        # Momentum features
        'news_urgency_score': momentum['news_urgency'],
        'news_impact_score': momentum['news_impact'],
        'time_decay_factor': momentum['time_decay_factor'],
        'overall_momentum_score': momentum['overall_momentum'],
        
        # Entity counts (additional features)
        'mentioned_stocks_count': len(entities['stocks']),
        'mentioned_indices_count': len(entities['indices']),
        'mentioned_currencies_count': len(entities['currencies']),
        'mentioned_commodities_count': len(entities['commodities']),
        
        # Text characteristics
        'text_length': len(text),
        'word_count': len(text.split()),
        'sentence_count': len(text.split('.')),
        
        # Composite scores for ML
        'composite_bullish_score': max(0, finbert_score + psychology['fear_greed_score'] * 0.5 + sector_sentiment * 0.3),
        'composite_bearish_score': max(0, -finbert_score - psychology['fear_greed_score'] * 0.5 - sector_sentiment * 0.3),
        'risk_adjusted_sentiment': finbert_score * (1 - abs(psychology['volatility_sentiment']) * 0.3),
        'macro_adjusted_sentiment': finbert_score * (1 + sum(macro_sentiment.values()) * 0.2),
        
        # Meta information
        'analysis_timestamp': datetime.utcnow().isoformat(),
        'entities_detected': entities,
        'feature_version': '1.0.0'
    }
    
    return ml_features

# Legacy compatibility function for existing code
def ensemble_sentiment_analysis(text: str) -> Dict[str, Any]:
    """
    Legacy compatibility wrapper for existing sentiment regeneration scripts
    """
    features = generate_enhanced_sentiment_features(text)
    
    # Map to legacy format
    legacy_result = {
        'text_length': features['text_length'],
        'word_count': features['word_count'],
        'methods_used': ['finbert', 'market_psychology', 'macro_economic', 'sector_rotation'],
        'individual_scores': {
            'finbert': {
                'score': features['finbert_sentiment_score'],
                'confidence': features['finbert_confidence']
            },
            'market_psychology': {
                'score': features['fear_greed_score'],
                'confidence': 0.8
            },
            'macro_economic': {
                'score': features.get('fed_policy_sentiment', 0.0),
                'confidence': 0.7
            },
            'sector_rotation': {
                'score': features['sector_rotation_sentiment'],
                'confidence': 0.6
            },
            'crypto_correlation': {
                'score': features['crypto_correlation_score'],
                'confidence': 0.7
            }
        },
        'ensemble_score': features['finbert_sentiment_score'],  # Use FinBERT as primary
        'ensemble_confidence': features['finbert_confidence'],
        'sentiment_label': 'positive' if features['finbert_sentiment_score'] > 0.1 else ('negative' if features['finbert_sentiment_score'] < -0.1 else 'neutral'),
        'method_weights': {
            'finbert': 0.5,
            'market_psychology': 0.2,
            'macro_economic': 0.15,
            'sector_rotation': 0.1,
            'crypto_correlation': 0.05
        },
        'enhanced_features': features  # Include all enhanced features
    }
    
    return legacy_result

# For testing
if __name__ == "__main__":
    # Test the sentiment analyzer
    test_text = """
    Apple Inc. reported strong earnings that beat expectations, with revenue growth of 15% 
    year-over-year. The tech giant announced a massive $100 billion share buyback program 
    amid growing optimism about AI integration in their products. Investors showed strong 
    risk appetite as technology stocks rallied across the board.
    """
    
    print("🧪 Testing Enhanced Stock Market Sentiment Analysis")
    print(f"Text: {test_text[:100]}...")
    
    features = generate_enhanced_sentiment_features(test_text)
    
    print(f"\n📊 Sentiment Analysis Results:")
    print(f"   FinBERT Score: {features['finbert_sentiment_score']:.3f}")
    print(f"   Fear/Greed: {features['fear_greed_score']:.3f}")
    print(f"   Risk Appetite: {features['risk_appetite_score']:.3f}")
    print(f"   Crypto Correlation: {features['crypto_correlation_score']:.3f}")
    print(f"   Composite Bullish: {features['composite_bullish_score']:.3f}")
    
    print(f"\n🎯 ML Features Generated: {len(features)} total features")
    print(f"   Entities Detected: {features['entities_detected']}")
