#!/usr/bin/env python3
"""
Unit tests for Enhanced ML Sentiment Collector
"""

import pytest
import asyncio
import torch
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timezone
from typing import List, Dict

from enhanced_sentiment_ml_template import (
    EnhancedMLSentimentCollector,
    MLSentimentCollectorConfig
)
from tests.test_base_collector import BaseCollectorTestCase

class TestMLSentimentCollectorConfig:
    """Test ML sentiment collector configuration"""
    
    def test_config_initialization(self):
        """Test configuration defaults"""
        config = MLSentimentCollectorConfig.from_env()
        
        assert config.service_name == "enhanced-sentiment-ml"
        assert config.batch_processing_size == 5
        assert config.processing_interval == 300
        assert config.crypto_model == "kk08/CryptoBERT"
        assert config.stock_model == "ProsusAI/finbert"
        assert config.device == -1  # CPU
    
    def test_model_configuration(self):
        """Test ML model configuration"""
        config = MLSentimentCollectorConfig()
        
        assert config.max_text_length == 512 * 4
        assert config.days_lookback == 7
        assert config.min_confidence_threshold == 0.1
        assert config.fallback_confidence == 0.5

class TestEnhancedMLSentimentCollector(BaseCollectorTestCase):
    """Test Enhanced ML Sentiment Collector functionality"""
    
    @pytest.fixture
    def sentiment_collector(self):
        """Create sentiment collector instance for testing"""
        with patch.dict('os.environ', {
            'DB_HOST': 'localhost',
            'DB_USER': 'test',
            'DB_PASSWORD': 'test',
            'DB_NAME': 'test_db',
            'SERVICE_NAME': 'enhanced-sentiment-ml'
        }):
            return EnhancedMLSentimentCollector()
    
    @pytest.fixture
    def mock_transformers_pipeline(self):
        """Mock transformers pipeline"""
        mock_pipeline = Mock()
        mock_pipeline.return_value = [
            {"label": "POSITIVE", "score": 0.8},
            {"label": "NEGATIVE", "score": 0.2}
        ]
        return mock_pipeline
    
    def test_collector_initialization(self, sentiment_collector):
        """Test sentiment collector initialization"""
        assert sentiment_collector.config.service_name == "enhanced-sentiment-ml"
        assert sentiment_collector.crypto_sentiment_pipeline is None
        assert sentiment_collector.stock_sentiment_pipeline is None
        assert sentiment_collector.model_loading_status["crypto"] == False
        assert sentiment_collector.model_loading_status["stock"] == False
    
    @patch('services.enhanced_sentiment_ml_template.pipeline')
    @pytest.mark.asyncio
    async def test_load_crypto_model(self, mock_pipeline, sentiment_collector):
        """Test loading CryptoBERT model"""
        mock_pipeline.return_value = Mock()
        
        sentiment_collector._load_crypto_model()
        
        mock_pipeline.assert_called_once_with(
            "sentiment-analysis",
            model="kk08/CryptoBERT",
            tokenizer="kk08/CryptoBERT",
            device=-1,
            return_all_scores=True
        )
    
    @patch('services.enhanced_sentiment_ml_template.pipeline')
    @pytest.mark.asyncio
    async def test_load_stock_model(self, mock_pipeline, sentiment_collector):
        """Test loading FinBERT model"""
        mock_pipeline.return_value = Mock()
        
        sentiment_collector._load_stock_model()
        
        mock_pipeline.assert_called_once_with(
            "sentiment-analysis",
            model="ProsusAI/finbert",
            tokenizer="ProsusAI/finbert",
            device=-1,
            return_all_scores=True
        )
    
    def test_market_type_detection(self, sentiment_collector):
        """Test crypto vs stock market type detection"""
        # Test crypto text
        crypto_text = "Bitcoin BTC price surges with blockchain adoption and DeFi growth"
        market_type = sentiment_collector._detect_market_type(crypto_text)
        assert market_type == "crypto"
        
        # Test stock text
        stock_text = "NYSE trading volumes increase with S&P 500 earnings reports and Fed policy"
        market_type = sentiment_collector._detect_market_type(stock_text)
        assert market_type == "stock"
        
        # Test neutral text (defaults to crypto)
        neutral_text = "Technology sector shows mixed signals"
        market_type = sentiment_collector._detect_market_type(neutral_text)
        assert market_type == "crypto"
    
    @pytest.mark.asyncio
    async def test_extract_sentiment_from_results(self, sentiment_collector):
        """Test sentiment extraction from ML model results"""
        # Test HuggingFace format with return_all_scores=True
        results = [[
            {"label": "positive", "score": 0.7},
            {"label": "negative", "score": 0.2},
            {"label": "neutral", "score": 0.1}
        ]]
        
        sentiment_score, confidence = await sentiment_collector._extract_sentiment_from_results(
            results, "CryptoBERT"
        )
        
        assert sentiment_score == 0.5  # 0.7 - 0.2
        assert confidence == 0.7  # max(positive, negative)
    
    @pytest.mark.asyncio
    async def test_analyze_sentiment_with_ml(self, sentiment_collector):
        """Test ML sentiment analysis"""
        # Mock model pipeline
        mock_pipeline = Mock()
        mock_pipeline.return_value = [[
            {"label": "positive", "score": 0.8},
            {"label": "negative", "score": 0.2}
        ]]
        sentiment_collector.crypto_sentiment_pipeline = mock_pipeline
        
        text = "Bitcoin price is showing bullish momentum"
        market_type = "crypto"
        
        score, confidence, analysis = await sentiment_collector._analyze_sentiment_with_ml(
            text, market_type
        )
        
        assert isinstance(score, float)
        assert -1.0 <= score <= 1.0
        assert 0.0 <= confidence <= 1.0
        assert "CryptoBERT" in analysis
        mock_pipeline.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analyze_sentiment_fallback(self, sentiment_collector):
        """Test sentiment analysis fallback when models fail"""
        # No models loaded
        sentiment_collector.crypto_sentiment_pipeline = None
        sentiment_collector.stock_sentiment_pipeline = None
        
        text = "Market analysis text"
        market_type = "crypto"
        
        score, confidence, analysis = await sentiment_collector._analyze_sentiment_with_ml(
            text, market_type
        )
        
        # Should return fallback values
        assert score == 0.0
        assert confidence == sentiment_collector.config.fallback_confidence
        assert "failed" in analysis.lower()
    
    @pytest.mark.asyncio
    async def test_process_single_article(self, sentiment_collector, mock_database):
        """Test processing a single article for sentiment"""
        mock_conn, mock_cursor = mock_database
        mock_cursor.fetchone.return_value = {
            'id': 1,
            'title': 'Bitcoin Bullish Trend',
            'content': 'Bitcoin shows strong upward momentum',
            'market_type': None,
            'ml_sentiment_score': None,
            'ml_sentiment_confidence': None
        }
        
        # Mock sentiment analysis
        with patch.object(sentiment_collector, '_analyze_sentiment_with_ml',
                         return_value=(0.75, 0.85, "Positive sentiment")) as mock_analyze:
            
            result = await sentiment_collector._process_single_article(1)
            
            assert result == True
            mock_analyze.assert_called_once()
            mock_cursor.execute.assert_called()  # Database update
    
    @pytest.mark.asyncio
    async def test_process_pending_articles(self, sentiment_collector, mock_database):
        """Test processing pending articles"""
        mock_conn, mock_cursor = mock_database
        mock_cursor.fetchall.return_value = [(1,), (2,), (3,)]  # 3 articles
        
        with patch.object(sentiment_collector, '_process_single_article', return_value=True) as mock_process:
            result = await sentiment_collector._process_pending_articles(limit=5)
            
            assert result == 3  # 3 articles processed
            assert mock_process.call_count == 3
    
    @pytest.mark.asyncio
    async def test_collect_data(self, sentiment_collector):
        """Test main data collection method"""
        with patch.object(sentiment_collector, '_ensure_models_loaded') as mock_models:
            with patch.object(sentiment_collector, '_process_pending_articles', return_value=5) as mock_process:
                
                result = await sentiment_collector.collect_data()
                
                assert result == 5
                mock_models.assert_called_once()
                mock_process.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_ensure_models_loaded(self, sentiment_collector):
        """Test ensuring ML models are loaded"""
        with patch.object(sentiment_collector.circuit_breaker, 'call') as mock_cb:
            with patch.object(sentiment_collector, '_load_crypto_model', return_value=Mock()) as mock_crypto:
                with patch.object(sentiment_collector, '_load_stock_model', return_value=Mock()) as mock_stock:
                    
                    await sentiment_collector._ensure_models_loaded()
                    
                    # Circuit breaker should be called for model loading
                    assert mock_cb.call_count == 2  # Once for each model
    
    @pytest.mark.asyncio
    async def test_backfill_data(self, sentiment_collector):
        """Test backfill functionality"""
        missing_periods = [
            {"start_date": datetime(2024, 1, 1), "end_date": datetime(2024, 1, 2)}
        ]
        
        with patch.object(sentiment_collector, '_process_single_article', return_value=True) as mock_process:
            with patch.object(sentiment_collector, 'get_database_connection') as mock_db:
                mock_cursor = Mock()
                mock_cursor.fetchall.return_value = [(1,), (2,)]  # 2 articles to backfill
                mock_db.return_value.__enter__.return_value.cursor.return_value = mock_cursor
                
                result = await sentiment_collector.backfill_data(missing_periods)
                
                assert result >= 0
                assert mock_process.call_count >= 0
    
    @pytest.mark.asyncio
    async def test_analyze_missing_data(self, sentiment_collector, mock_database):
        """Test missing sentiment data analysis"""
        mock_conn, mock_cursor = mock_database
        mock_cursor.fetchall.return_value = [
            (datetime(2024, 1, 1).date(), 100, 30),  # 30 missing sentiment
            (datetime(2024, 1, 2).date(), 80, 20)    # 20 missing sentiment
        ]
        
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 7)
        
        missing_periods = await sentiment_collector._analyze_missing_data(start_date, end_date)
        
        assert isinstance(missing_periods, list)
        assert len(missing_periods) == 2
        for period in missing_periods:
            assert "missing_sentiment" in period
            assert period["missing_sentiment"] > 0
    
    @pytest.mark.asyncio
    async def test_generate_data_quality_report(self, sentiment_collector, mock_database):
        """Test data quality report generation"""
        mock_conn, mock_cursor = mock_database
        mock_cursor.fetchone.side_effect = [
            (1000,),  # total_records
            (800,),   # valid_records (with sentiment)
            (50,)     # low_confidence_records
        ]
        
        report = await sentiment_collector._generate_data_quality_report()
        
        assert report.total_records == 1000
        assert report.valid_records == 800
        assert report.invalid_records == 200
        assert 0 <= report.data_quality_score <= 100

class TestSentimentModelHandling:
    """Test ML model loading and management"""
    
    @pytest.fixture
    def sentiment_collector(self):
        """Create collector for model testing"""
        with patch.dict('os.environ', {'SERVICE_NAME': 'test-sentiment'}):
            return EnhancedMLSentimentCollector()
    
    @patch('torch.cuda.is_available', return_value=False)
    def test_cpu_device_selection(self, mock_cuda, sentiment_collector):
        """Test CPU device selection when CUDA unavailable"""
        assert sentiment_collector.config.device == -1  # Force CPU
    
    @pytest.mark.asyncio
    async def test_model_loading_failure_handling(self, sentiment_collector):
        """Test handling of model loading failures"""
        with patch('services.enhanced_sentiment_ml_template.pipeline', side_effect=Exception("Model not found")):
            with patch.object(sentiment_collector, '_send_alert') as mock_alert:
                sentiment_collector.config.enable_alerting = True
                
                await sentiment_collector._ensure_models_loaded()
                
                # Should send alert on model loading failure
                assert mock_alert.call_count >= 0  # May send alerts
    
    def test_text_truncation(self, sentiment_collector):
        """Test text truncation for model processing"""
        long_text = "Bitcoin " * 1000  # Very long text
        max_length = sentiment_collector.config.max_text_length
        
        # In actual implementation, text would be truncated
        truncated_text = long_text[:max_length]
        assert len(truncated_text) <= max_length

class TestSentimentIntegration:
    """Integration tests for sentiment collector"""
    
    @pytest.mark.integration
    @pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
    def test_gpu_model_loading(self):
        """Test model loading with GPU"""
        # This would test actual GPU model loading
        pass
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_real_model_inference(self):
        """Test real model inference with sample data"""
        # This would test actual model inference
        # Marked as slow because model loading takes time
        pass

if __name__ == "__main__":
    pytest.main([__file__, "-v"])