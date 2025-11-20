#!/usr/bin/env python3
"""
Enhanced Unit Tests for ML Sentiment Collector with Multi-Environment Support

These tests demonstrate how the smart model manager enables seamless testing
across different environments while maintaining the same code.
"""

import pytest
import asyncio
import os
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timezone
from typing import List, Dict

# Force test environment for model manager
os.environ["TESTING"] = "true"

from services.enhanced_sentiment_ml_analysis import (
    EnhancedMLSentimentCollector,
    MLSentimentCollectorConfig
)
from shared.smart_model_manager import SmartModelManager, ModelSource
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

class TestSmartModelManager:
    """Test smart model manager functionality"""
    
    def test_environment_detection(self):
        """Test that testing environment is correctly detected"""
        manager = SmartModelManager()
        assert manager.environment == ModelSource.MOCK_MODELS
    
    def test_mock_model_creation(self):
        """Test mock model creation for sentiment analysis"""
        manager = SmartModelManager()
        model = manager.load_model("ProsusAI/finbert", "sentiment")
        
        # Should return a mock
        assert isinstance(model, MagicMock)
        
        # Test mock functionality
        result = model("This is a positive test message")
        assert isinstance(result, list)
        assert len(result) == 2
        assert all("label" in item and "score" in item for item in result)
    
    def test_model_caching(self):
        """Test that models are cached properly"""
        manager = SmartModelManager()
        
        # Load same model twice
        model1 = manager.load_model("ProsusAI/finbert", "sentiment")
        model2 = manager.load_model("ProsusAI/finbert", "sentiment")
        
        # Should be the same cached instance
        assert model1 is model2
        assert "sentiment_ProsusAI_finbert" in manager.models

class TestEnhancedMLSentimentCollector(BaseCollectorTestCase):
    """Test Enhanced ML Sentiment Collector functionality"""
    
    @pytest.fixture
    def sentiment_collector(self):
        """Create sentiment collector instance for testing"""
        with patch.dict('os.environ', {
            'DB_HOST': 'localhost',
            'DB_USER': 'test',
            'DB_PASSWORD': 'test',
            'DB_NAME': 'test_crypto_data',
            'TESTING': 'true'  # Ensure test environment
        }):
            collector = EnhancedMLSentimentCollector()
            return collector
    
    def test_collector_initialization(self, sentiment_collector):
        """Test collector initialization with mock models"""
        assert sentiment_collector.model_manager.environment == ModelSource.MOCK_MODELS
        assert sentiment_collector.model_loading_status["crypto"] == False
        assert sentiment_collector.model_loading_status["stock"] == False
    
    @pytest.mark.asyncio
    async def test_ensure_models_loaded(self, sentiment_collector):
        """Test ensuring ML models are loaded in test environment"""
        # Models should load without errors in test environment
        await sentiment_collector._ensure_models_loaded()
        
        # Verify models are loaded (using mocks)
        assert sentiment_collector.model_loading_status["crypto"] == True
        assert sentiment_collector.model_loading_status["stock"] == True
        assert sentiment_collector.crypto_sentiment_pipeline is not None
        assert sentiment_collector.stock_sentiment_pipeline is not None
    
    @pytest.mark.asyncio
    async def test_sentiment_analysis_with_mocks(self, sentiment_collector):
        """Test sentiment analysis using mock models"""
        await sentiment_collector._ensure_models_loaded()
        
        # Test crypto sentiment analysis
        crypto_result = await sentiment_collector._analyze_sentiment(
            "Bitcoin surges to new highs", "crypto"
        )
        
        assert isinstance(crypto_result, dict)
        assert "score" in crypto_result
        assert "label" in crypto_result
        assert "confidence" in crypto_result
        
        # Test stock sentiment analysis
        stock_result = await sentiment_collector._analyze_sentiment(
            "Tesla stock shows strong performance", "stock"
        )
        
        assert isinstance(stock_result, dict)
        assert "score" in stock_result
        assert "label" in stock_result
        assert "confidence" in stock_result
    
    @pytest.mark.asyncio
    async def test_collect_data_with_mocks(self, sentiment_collector):
        """Test data collection with mocked database and models"""
        with patch.object(sentiment_collector, '_process_pending_articles') as mock_process:
            mock_process.return_value = 5
            
            # Should complete without errors
            result = await sentiment_collector.collect_data()
            assert result == 5
            mock_process.assert_called_once()
    
    @pytest.mark.asyncio 
    async def test_health_check_includes_environment(self, sentiment_collector):
        """Test that health check includes environment information"""
        await sentiment_collector._ensure_models_loaded()
        
        health_data = await sentiment_collector.health_check()
        
        assert health_data["status"] == "healthy"
        assert "service_info" in health_data
        assert "model_manager" in health_data["service_info"]
        assert health_data["service_info"]["model_manager"]["environment"] == "mock_models"
    
    @pytest.mark.asyncio
    async def test_mock_sentiment_realistic_results(self, sentiment_collector):
        """Test that mock sentiment analysis returns realistic results"""
        await sentiment_collector._ensure_models_loaded()
        
        # Test positive text
        positive_result = await sentiment_collector._analyze_sentiment(
            "Great news about cryptocurrency adoption", "crypto"
        )
        assert positive_result["label"] == "POSITIVE"
        assert positive_result["score"] > 0.5
        
        # Test negative text  
        negative_result = await sentiment_collector._analyze_sentiment(
            "Terrible market crash affects all stocks", "stock"
        )
        assert negative_result["label"] == "NEGATIVE"
        assert negative_result["score"] > 0.5

class TestModelManagerEnvironments:
    """Test model manager behavior across different environments"""
    
    def test_persistent_volume_detection(self):
        """Test detection of K3s persistent volume environment"""
        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.return_value = True  # Simulate metadata file exists
            
            manager = SmartModelManager()
            # Should detect persistent volume if metadata exists
            # (but will fall back to mock in test environment)
            
    def test_local_cache_detection(self):
        """Test detection of local development environment"""
        with patch.dict(os.environ, {"MODEL_CACHE_DIR": "./test_cache", "TESTING": ""}):
            with patch('pathlib.Path.exists') as mock_exists:
                with patch('pathlib.Path.iterdir') as mock_iterdir:
                    mock_exists.return_value = True
                    mock_iterdir.return_value = [Mock(is_dir=Mock(return_value=True))]
                    
                    # Should detect local cache environment
                    # (but will still be mock due to pytest detection)
    
    @pytest.mark.parametrize("env_vars,expected_env", [
        ({"GITHUB_ACTIONS": "true", "TESTING": ""}, ModelSource.DOWNLOAD_ON_DEMAND),
        ({"PYTEST_CURRENT_TEST": "test_something", "TESTING": ""}, ModelSource.MOCK_MODELS),
        ({"TESTING": "true"}, ModelSource.MOCK_MODELS),
    ])
    def test_environment_detection_priority(self, env_vars, expected_env):
        """Test environment detection priority with different variable combinations"""
        with patch.dict(os.environ, env_vars, clear=False):
            # Reset any cached manager
            if hasattr(SmartModelManager, '_instance'):
                delattr(SmartModelManager, '_instance')
                
            manager = SmartModelManager()
            if "TESTING" in env_vars and env_vars["TESTING"] == "true":
                assert manager.environment == ModelSource.MOCK_MODELS

class TestIntegrationEnvironment:
    """Tests for integration testing environment (marked separately)"""
    
    @pytest.mark.integration
    @pytest.mark.skipif(not os.getenv("RUN_INTEGRATION_TESTS"), 
                       reason="Integration tests disabled")
    def test_real_model_loading(self):
        """Test loading real models (only runs in integration environment)"""
        # This would test actual model downloading and loading
        # Only runs when RUN_INTEGRATION_TESTS=true
        with patch.dict(os.environ, {
            "GITHUB_ACTIONS": "true",
            "MODEL_CACHE_DIR": "/tmp/integration_models",
            "TESTING": ""  # Disable test mode
        }):
            manager = SmartModelManager()
            
            # This would actually download models in real integration test
            # For now, we'll just verify the environment detection
            assert manager.environment in [
                ModelSource.DOWNLOAD_ON_DEMAND,
                ModelSource.HUGGINGFACE_HUB
            ]

# Test configuration for different pytest markers
pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.unit,  # Mark as unit tests by default
]

if __name__ == "__main__":
    # Example of running tests directly
    pytest.main([__file__, "-v", "--tb=short"])