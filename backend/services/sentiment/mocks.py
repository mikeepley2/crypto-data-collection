import random
import re
import hashlib

# Enhanced positive crypto terms with weights
POSITIVE_TERMS = {
    # Strong positive terms (weight: 2.0)
    'bullish': 2.0, 'surge': 2.0, 'rally': 2.0, 'moon': 2.0, 'soar': 2.0,
    'breakthrough': 2.0, 'excellent': 2.0, 'skyrocket': 2.0, 'boom': 2.0,
    # Medium positive terms (weight: 1.5)
    'gain': 1.5, 'rise': 1.5, 'adoption': 1.5, 'mainstream': 1.5,
    'innovation': 1.5, 'institutional': 1.5, 'profit': 1.5, 'consensus': 1.5,
    'higher': 1.5, 'boost': 1.5, 'opportunity': 1.5, 'success': 1.5,
    # Light positive terms (weight: 1.0)
    'invest': 1.0, 'support': 1.0, 'growth': 1.0, 'strong': 1.0,
    'partnership': 1.0, 'improve': 1.0, 'improved': 1.0, 'increasing': 1.0,
    'increase': 1.0, 'upgrade': 1.0, 'reduced': 1.0, 'reduce': 1.0,
    'efficiency': 1.0, 'efficient': 1.0, 'successful': 1.0,
    'promising': 1.0, 'potential': 1.0, 'confident': 1.0,
    'advantageous': 1.0, 'valuable': 1.0, 'positive': 1.0, 'optimistic': 1.0,
    'recover': 1.0, 'recovery': 1.0, 'progress': 1.0, 'advancing': 1.0,
    'advance': 1.0, 'solid': 1.0, 'strength': 1.0, 'strengthen': 1.0,
    'encouraging': 1.0, 'good': 1.0, 'great': 1.0,
}

# Enhanced negative crypto terms with weights
NEGATIVE_TERMS = {
    # Strong negative terms (weight: 2.0)
    'bearish': 2.0, 'crash': 2.0, 'plunge': 2.0, 'hack': 2.0, 'scam': 2.0,
    'fraud': 2.0, 'ponzi': 2.0, 'collapse': 2.0, 'worst': 2.0, 'dump': 2.0,
    # Medium negative terms (weight: 1.5)
    'drop': 1.5, 'fall': 1.5, 'ban': 1.5, 'bubble': 1.5,
    'fear': 1.5, 'uncertainty': 1.5, 'doubt': 1.5, 'fud': 1.5,
    'decline': 1.5, 'problem': 1.5, 'issue': 1.5, 'failure': 1.5,
    'fail': 1.5, 'loss': 1.5, 'loses': 1.5, 'lost': 1.5,
    # Light negative terms (weight: 1.0)
    'regulation': 1.0, 'volatility': 1.0, 'risk': 1.0, 'warning': 1.0,
    'concern': 1.0, 'decreased': 1.0, 'decrease': 1.0, 'struggle': 1.0,
    'struggling': 1.0, 'disappointing': 1.0, 'poor': 1.0,
    'bad': 1.0, 'worse': 1.0, 'trouble': 1.0, 'problematic': 1.0,
    'danger': 1.0, 'dangerous': 1.0, 'worried': 1.0, 'worry': 1.0,
    'anxious': 1.0, 'anxiety': 1.0, 'fearful': 1.0, 'negative': 1.0,
    'pessimistic': 1.0, 'downturn': 1.0, 'downtrend': 1.0,
}

# Crypto-specific entities that can modify sentiment
CRYPTO_ENTITIES = {
    'bitcoin': 1.0, 'btc': 1.0, 'ethereum': 1.0, 'eth': 1.0, 
    'binance': 0.8, 'coinbase': 0.8, 'ftx': -0.5,  # FTX has negative connotation after collapse
    'sec': -0.3, 'regulation': -0.3, 'regulated': -0.2,
    'mining': 0.2, 'miner': 0.2, 'staking': 0.4, 'yield': 0.6,
    'defi': 0.5, 'nft': 0.3, 'web3': 0.4, 'metaverse': 0.2,
    'wallet': 0.2, 'blockchain': 0.4, 'token': 0.1
}

def mock_cryptobert_sentiment(text):
    """
    Enhanced mock implementation of CryptoBERT sentiment analysis.
    Returns realistic sentiment scores based on text content.
    """
    # Count positive and negative words
    text_lower = text.lower()
    
    # More comprehensive list of positive/negative crypto terms
    positive_terms = [
        'bullish', 'surge', 'rally', 'gain', 'rise', 'adoption', 'mainstream',
        'breakthrough', 'innovation', 'institutional', 'invest', 'support',
        'growth', 'strong', 'profit', 'consensus', 'partnership', 'improve',
        'improved', 'increasing', 'increase', 'upgrade', 'reduced', 'reduce',
        'efficiency', 'efficient', 'success', 'successful', 'opportunity',
        'higher', 'boost', 'boost', 'promising', 'potential', 'confident',
        'advantageous', 'valuable', 'positive', 'optimistic', 'recover',
        'recovery', 'progress', 'advancing', 'advance', 'solid', 'strength',
        'strengthen', 'encouraging', 'good', 'great', 'excellent'
    ]
    
    negative_terms = [
        'bearish', 'crash', 'plunge', 'drop', 'fall', 'regulation', 'ban',
        'risk', 'volatile', 'uncertainty', 'bubble', 'correction', 'loss',
        'sell-off', 'weak', 'decline', 'decreased', 'decreasing', 'decrease',
        'downgrade', 'problem', 'issue', 'concern', 'fraud', 'scam', 'hack',
        'vulnerability', 'threat', 'attack', 'lower', 'failure', 'fail',
        'failed', 'disappointing', 'poor', 'bad', 'worse', 'worst',
        'trouble', 'problematic', 'risk', 'risky', 'danger', 'dangerous',
        'warning', 'worried', 'worry', 'anxious', 'anxiety', 'fear',
        'fearful', 'negative', 'pessimistic', 'bearish', 'downturn',
        'downtrend', 'struggle', 'struggling', 'collapse'
    ]
    
    # Calculate positive and negative scores
    pos_count = sum(1 for term in positive_terms if term in text_lower)
    neg_count = sum(1 for term in negative_terms if term in text_lower)
    
    # Calculate sentiment based on word counts with some randomization
    import random
    import hashlib
    
    # Use deterministic randomness based on the text
    text_hash = int(hashlib.md5(text.encode()).hexdigest(), 16)
    random.seed(text_hash)
    
    # Base sentiment calculation
    word_count = len(text.split())
    
    # Normalize by text length
    pos_score = min(0.9, pos_count / max(5, word_count/2) + random.uniform(-0.05, 0.05))
    neg_score = min(0.9, neg_count / max(5, word_count/2) + random.uniform(-0.05, 0.05))
    
    # Ensure we have reasonable minimums
    pos_score = max(0.05, pos_score)
    neg_score = max(0.05, neg_score)
    
    # Calculate neutral as the remainder, ensuring all scores sum to 1
    neut_score = 1.0 - (pos_score + neg_score)
    
    # If neutral is negative, redistribute
    if neut_score < 0:
        total = pos_score + neg_score
        pos_score = pos_score / total
        neg_score = neg_score / total
        neut_score = 0.0
    
    # Convert to list format expected by the real model [neg, neut, pos]
    scores = [neg_score, neut_score, pos_score]
    
    # Calculate sentiment score as pos - neg (matches real model)
    sentiment = pos_score - neg_score
    
    return sentiment, scores

def mock_openai_sentiment(text):
    """
    Enhanced mock implementation of OpenAI sentiment analysis.
    Returns more realistic sentiment scores and summaries based on the input text.
    """
    # Use same base algorithm as CryptoBERT for consistency
    text_lower = text.lower()
    
    # Count positive and negative term occurrences
    positive_count = sum(1 for term in POSITIVE_TERMS if term in text_lower)
    negative_count = sum(1 for term in NEGATIVE_TERMS if term in text_lower)
    
    # Calculate base sentiment
    if positive_count > 0 or negative_count > 0:
        base_sentiment = (positive_count - negative_count) / max(positive_count + negative_count, 1)
    else:
        # Slight random bias for texts without clear sentiment terms
        base_sentiment = random.uniform(-0.2, 0.2)
    
    # Add some randomness but keep within reasonable bounds
    score = min(max(base_sentiment + random.uniform(-0.3, 0.3), -1), 1)
    
    # Generate a more realistic summary based on the sentiment
    if score > 0.5:
        summary_start = random.choice(["Highly positive sentiment.", "Very bullish outlook.", "Strong positive indicators."])
    elif score > 0.2:
        summary_start = random.choice(["Moderately positive sentiment.", "Somewhat bullish.", "Positive signals present."])
    elif score > -0.2:
        summary_start = random.choice(["Neutral sentiment.", "Balanced perspective.", "No strong sentiment indicators."])
    elif score > -0.5:
        summary_start = random.choice(["Moderately negative sentiment.", "Somewhat bearish.", "Concerning elements present."])
    else:
        summary_start = random.choice(["Highly negative sentiment.", "Very bearish outlook.", "Strong negative indicators."])
    
    summary = f"{summary_start} Analysis of: {text[:50]}{'...' if len(text) > 50 else ''} (score: {score:.2f})"
    
    return score, summary
