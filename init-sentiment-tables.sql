-- Create sentiment data tables for the crypto news collection system

-- Social sentiment data table
CREATE TABLE IF NOT EXISTS social_sentiment_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    platform VARCHAR(50) NOT NULL,
    username VARCHAR(100),
    post_content TEXT,
    sentiment_score DECIMAL(5,3),
    sentiment_confidence DECIMAL(5,3),
    sentiment_label VARCHAR(20),
    metadata JSON,
    timestamp DATETIME,
    collected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_platform (platform),
    INDEX idx_timestamp (timestamp),
    INDEX idx_collected_at (collected_at)
);

-- Stock sentiment data table  
CREATE TABLE IF NOT EXISTS stock_sentiment_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    stock_symbol VARCHAR(10) NOT NULL,
    headline VARCHAR(500),
    content TEXT,
    sentiment_score DECIMAL(5,3),
    sentiment_confidence DECIMAL(5,3),
    sentiment_label VARCHAR(20),
    source VARCHAR(100),
    timestamp DATETIME,
    collected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_symbol (stock_symbol),
    INDEX idx_timestamp (timestamp),
    INDEX idx_collected_at (collected_at)
);

-- Crypto sentiment data table
CREATE TABLE IF NOT EXISTS crypto_sentiment_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    crypto_symbol VARCHAR(10) NOT NULL,
    source VARCHAR(100),
    headline VARCHAR(500),
    content TEXT,
    sentiment_score DECIMAL(5,3),
    sentiment_confidence DECIMAL(5,3),
    sentiment_label VARCHAR(20),
    metadata JSON,
    timestamp DATETIME,
    collected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_symbol (crypto_symbol),
    INDEX idx_source (source),
    INDEX idx_timestamp (timestamp),
    INDEX idx_collected_at (collected_at)
);

-- General sentiment analysis results table
CREATE TABLE IF NOT EXISTS sentiment_analysis_results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    text_input TEXT NOT NULL,
    sentiment_score DECIMAL(5,3),
    sentiment_confidence DECIMAL(5,3),
    sentiment_label VARCHAR(20),
    analysis_method VARCHAR(50),
    processed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_label (sentiment_label),
    INDEX idx_processed_at (processed_at)
);