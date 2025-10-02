-- News Narratives Table Schema
-- Stores advanced narrative analysis results from LLM processing

CREATE TABLE IF NOT EXISTS news_narratives (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    news_id VARCHAR(50) NOT NULL UNIQUE,
    title TEXT NOT NULL,
    
    -- Theme classification
    primary_theme ENUM(
        'regulation', 'adoption', 'technology', 'macro_economic', 
        'institutional', 'defi', 'security', 'market_structure', 
        'geopolitical', 'other'
    ) NOT NULL DEFAULT 'other',
    secondary_themes JSON,
    
    -- Narrative analysis
    narrative_summary TEXT,
    key_drivers JSON,
    market_implications TEXT,
    
    -- Impact analysis
    affected_assets JSON,
    impact_timeline ENUM('immediate', 'short-term', 'medium-term', 'long-term', 'uncertain') DEFAULT 'uncertain',
    confidence_score DECIMAL(3,2) DEFAULT 0.5,
    coherence ENUM('strong', 'moderate', 'weak', 'conflicting') DEFAULT 'moderate',
    
    -- Sentiment integration
    narrative_sentiment DECIMAL(3,2) DEFAULT 0.0,
    emotional_context VARCHAR(100),
    
    -- Historical context
    similar_events JSON,
    historical_patterns TEXT,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_news_id (news_id),
    INDEX idx_primary_theme (primary_theme),
    INDEX idx_created_at (created_at),
    INDEX idx_confidence (confidence_score),
    INDEX idx_sentiment (narrative_sentiment)
);

-- Market Theme Trends Table
-- Tracks theme popularity over time
CREATE TABLE IF NOT EXISTS theme_trends (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    theme VARCHAR(50) NOT NULL,
    date_analyzed DATE NOT NULL,
    article_count INT DEFAULT 0,
    average_sentiment DECIMAL(3,2) DEFAULT 0.0,
    average_confidence DECIMAL(3,2) DEFAULT 0.0,
    market_impact_score DECIMAL(3,2) DEFAULT 0.0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_theme_date (theme, date_analyzed),
    INDEX idx_theme (theme),
    INDEX idx_date (date_analyzed)
);

-- Narrative Cross-References Table
-- Links related narratives and events
CREATE TABLE IF NOT EXISTS narrative_cross_references (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    source_news_id VARCHAR(50) NOT NULL,
    related_news_id VARCHAR(50) NOT NULL,
    relationship_type ENUM('similar_theme', 'contradictory', 'follow_up', 'background') NOT NULL,
    similarity_score DECIMAL(3,2) DEFAULT 0.0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (source_news_id) REFERENCES news_narratives(news_id),
    FOREIGN KEY (related_news_id) REFERENCES news_narratives(news_id),
    INDEX idx_source (source_news_id),
    INDEX idx_related (related_news_id),
    INDEX idx_relationship (relationship_type)
);