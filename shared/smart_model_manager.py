#!/usr/bin/env python3
"""
Smart Model Manager - Multi-Environment ML Model Loading

This module provides intelligent model loading that adapts to any environment:
- K3s Production: Uses persistent volume storage
- Local Development: Downloads and caches models locally  
- Unit Tests: Uses mock models for fast testing
- CI/CD: Downloads models on demand
- Fallback: Direct HuggingFace Hub access

Usage:
    from shared.smart_model_manager import SmartModelManager
    
    manager = SmartModelManager()
    model = manager.load_model("ProsusAI/finbert", "sentiment")
"""

import os
import logging
from pathlib import Path
from enum import Enum
from typing import Optional, Union, Dict, Any, Callable
from unittest.mock import MagicMock
import time
import json

# Conditional imports - handle missing dependencies gracefully
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    pipeline = None

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

class ModelSource(Enum):
    """Available model sources based on environment detection"""
    PERSISTENT_VOLUME = "persistent_volume"     # K3s production with mounted models
    LOCAL_CACHE = "local_cache"                 # Development with local model cache
    MOCK_MODELS = "mock_models"                 # Unit tests with mocked responses
    DOWNLOAD_ON_DEMAND = "download_on_demand"   # CI/CD with temporary downloads
    HUGGINGFACE_HUB = "huggingface_hub"        # Direct HuggingFace Hub access

class ModelLoadingError(Exception):
    """Exception raised when model loading fails"""
    pass

class SmartModelManager:
    """Intelligent model manager that adapts to any environment"""
    
    def __init__(self):
        self.environment = self._detect_environment()
        self.models = {}
        self.logger = logging.getLogger(__name__)
        
        # Environment-specific configuration
        self.config = self._get_env_config()
        
        # Track model loading attempts for debugging
        self.loading_history = []
        
        self.logger.info(f"Initialized SmartModelManager for {self.environment.value}")
    
    def _detect_environment(self) -> ModelSource:
        """Automatically detect environment and return appropriate model source"""
        
        # 1. K3s Production - persistent volume exists
        if Path("/app/models/model-metadata.yaml").exists():
            return ModelSource.PERSISTENT_VOLUME
        
        # 2. Testing - explicit test environment
        if (os.getenv("PYTEST_CURRENT_TEST") or 
            os.getenv("TESTING") == "true" or
            "pytest" in str(os.getenv("_", "")).lower()):
            return ModelSource.MOCK_MODELS
        
        # 3. GitHub Actions - CI environment
        if os.getenv("GITHUB_ACTIONS") == "true":
            return ModelSource.DOWNLOAD_ON_DEMAND
        
        # 4. Local development - check for local cache
        local_cache = Path(os.getenv("MODEL_CACHE_DIR", "./model_cache"))
        if (local_cache.exists() and 
            any(model_dir.is_dir() for model_dir in local_cache.iterdir())):
            return ModelSource.LOCAL_CACHE
        
        # 5. Fallback - download from HuggingFace Hub
        return ModelSource.HUGGINGFACE_HUB
    
    def _get_env_config(self) -> Dict[str, Any]:
        """Get configuration for current environment"""
        configs = {
            ModelSource.PERSISTENT_VOLUME: {
                "cache_dir": "/app/models",
                "local": True,
                "timeout": 30,
                "device": -1,  # CPU only in production for stability
                "description": "K3s persistent volume"
            },
            ModelSource.LOCAL_CACHE: {
                "cache_dir": os.getenv("MODEL_CACHE_DIR", "./model_cache"),
                "local": True,
                "timeout": 60,
                "device": -1,  # CPU for development
                "description": "Local development cache"
            },
            ModelSource.MOCK_MODELS: {
                "cache_dir": None,
                "local": False,
                "timeout": 1,
                "device": None,
                "description": "Mock models for testing"
            },
            ModelSource.DOWNLOAD_ON_DEMAND: {
                "cache_dir": "/tmp/models",
                "local": False,
                "timeout": 300,  # 5 minutes for download
                "device": -1,  # CPU for CI/CD
                "description": "On-demand download"
            },
            ModelSource.HUGGINGFACE_HUB: {
                "cache_dir": None,
                "local": False,
                "timeout": 300,
                "device": -1,  # CPU fallback
                "description": "HuggingFace Hub direct"
            }
        }
        return configs[self.environment]
    
    def load_model(self, model_name: str, model_type: str = "sentiment") -> Union[Any, MagicMock]:
        """
        Load model appropriate for current environment
        
        Args:
            model_name: HuggingFace model name (e.g., "ProsusAI/finbert")
            model_type: Type of model for proper mocking (e.g., "sentiment")
            
        Returns:
            Loaded model pipeline or mock object
            
        Raises:
            ModelLoadingError: If model loading fails in production
        """
        cache_key = f"{model_type}_{model_name.replace('/', '_')}"
        
        # Return cached model if available
        if cache_key in self.models:
            self.logger.debug(f"Returning cached model: {cache_key}")
            return self.models[cache_key]
        
        start_time = time.time()
        self.logger.info(f"Loading {model_type} model '{model_name}' using {self.environment.value}")
        
        try:
            # Load model based on environment
            if self.environment == ModelSource.MOCK_MODELS:
                model = self._create_mock_model(model_type, model_name)
                
            elif self.environment == ModelSource.PERSISTENT_VOLUME:
                model = self._load_from_persistent_volume(model_name, model_type)
                
            elif self.environment == ModelSource.LOCAL_CACHE:
                model = self._load_from_local_cache(model_name, model_type)
                
            elif self.environment == ModelSource.DOWNLOAD_ON_DEMAND:
                model = self._load_with_download(model_name, model_type)
                
            else:  # HUGGINGFACE_HUB
                model = self._load_from_hub(model_name, model_type)
            
            # Cache the loaded model
            self.models[cache_key] = model
            
            load_time = time.time() - start_time
            self.loading_history.append({
                "model": model_name,
                "type": model_type,
                "environment": self.environment.value,
                "load_time": load_time,
                "success": True,
                "timestamp": time.time()
            })
            
            self.logger.info(f"Successfully loaded {model_name} in {load_time:.2f}s")
            return model
            
        except Exception as e:
            load_time = time.time() - start_time
            error_msg = f"Failed to load {model_name}: {str(e)}"
            
            self.loading_history.append({
                "model": model_name,
                "type": model_type,
                "environment": self.environment.value,
                "load_time": load_time,
                "success": False,
                "error": str(e),
                "timestamp": time.time()
            })
            
            self.logger.error(error_msg)
            
            # Handle errors based on environment
            if self.environment == ModelSource.PERSISTENT_VOLUME:
                # Production - raise immediately
                raise ModelLoadingError(error_msg) from e
            elif self.environment == ModelSource.MOCK_MODELS:
                # Testing - should never fail, but return basic mock
                self.logger.warning(f"Mock model creation failed, using basic mock: {e}")
                model = MagicMock()
                self.models[cache_key] = model
                return model
            else:
                # Development/CI - try fallback to mock
                self.logger.warning(f"Model loading failed, using mock fallback: {e}")
                model = self._create_mock_model(model_type, model_name)
                self.models[cache_key] = model
                return model
    
    def _create_mock_model(self, model_type: str, model_name: str) -> MagicMock:
        """Create mock model for testing"""
        mock_model = MagicMock()
        mock_model.model_name = model_name
        mock_model.model_type = model_type
        
        if model_type == "sentiment":
            # Mock sentiment analysis results
            def mock_sentiment(text, **kwargs):
                # Return realistic-looking sentiment scores
                if isinstance(text, list):
                    return [self._mock_single_sentiment(t) for t in text]
                else:
                    return self._mock_single_sentiment(text)
            
            mock_model.side_effect = mock_sentiment
            mock_model.__call__ = mock_sentiment
        
        self.logger.info(f"Created mock {model_type} model for {model_name}")
        return mock_model
    
    def _mock_single_sentiment(self, text: str) -> List[Dict[str, Any]]:
        """Generate mock sentiment result for single text"""
        # Simple heuristic for realistic mock results
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["good", "great", "positive", "bull", "rise", "up"]):
            positive_score = 0.8 + (hash(text) % 20) / 100  # 0.8-0.99
            negative_score = 1.0 - positive_score
            label = "POSITIVE"
        elif any(word in text_lower for word in ["bad", "terrible", "negative", "bear", "fall", "down"]):
            negative_score = 0.8 + (hash(text) % 20) / 100  # 0.8-0.99
            positive_score = 1.0 - negative_score
            label = "NEGATIVE"
        else:
            # Neutral with slight randomness
            positive_score = 0.4 + (hash(text) % 20) / 100  # 0.4-0.59
            negative_score = 1.0 - positive_score
            label = "POSITIVE" if positive_score > 0.5 else "NEGATIVE"
        
        return [
            {"label": "POSITIVE", "score": positive_score},
            {"label": "NEGATIVE", "score": negative_score}
        ]
    
    def _load_from_persistent_volume(self, model_name: str, model_type: str):
        """Load from K3s persistent volume"""
        if not TRANSFORMERS_AVAILABLE:
            raise ModelLoadingError("transformers library not available")
        
        # Map HuggingFace model names to local directory names
        model_mapping = {
            "ProsusAI/finbert": "finbert",
            "kk08/CryptoBERT": "cryptobert", 
            "cardiffnlp/twitter-roberta-base-sentiment-latest": "twitter-roberta"
        }
        
        local_name = model_mapping.get(model_name, model_name.split("/")[-1])
        local_path = Path(self.config["cache_dir"]) / local_name
        
        if not local_path.exists():
            available_models = list(Path(self.config["cache_dir"]).glob("*/"))
            raise ModelLoadingError(
                f"Model '{local_name}' not found in persistent volume: {local_path}. "
                f"Available models: {[m.name for m in available_models]}"
            )
        
        # Verify model files exist
        required_files = ["pytorch_model.bin", "config.json"]
        missing_files = [f for f in required_files if not (local_path / f).exists()]
        if missing_files:
            raise ModelLoadingError(f"Missing model files in {local_path}: {missing_files}")
        
        return pipeline(
            "sentiment-analysis",
            model=str(local_path),
            tokenizer=str(local_path),
            device=self.config["device"],
            return_all_scores=True,
        )
    
    def _load_from_local_cache(self, model_name: str, model_type: str):
        """Load from local development cache"""
        if not TRANSFORMERS_AVAILABLE:
            raise ModelLoadingError("transformers library not available")
        
        cache_dir = Path(self.config["cache_dir"])
        model_dir = cache_dir / model_name.split("/")[-1]
        
        if model_dir.exists() and (model_dir / "pytorch_model.bin").exists():
            # Load from local cache
            self.logger.info(f"Loading {model_name} from local cache: {model_dir}")
            return pipeline(
                "sentiment-analysis",
                model=str(model_dir),
                tokenizer=str(model_dir),
                device=self.config["device"],
                return_all_scores=True,
            )
        else:
            # Download and cache locally
            self.logger.info(f"Downloading {model_name} to local cache")
            cache_dir.mkdir(parents=True, exist_ok=True)
            
            # Download model
            model = pipeline(
                "sentiment-analysis",
                model=model_name,
                tokenizer=model_name,
                device=self.config["device"],
                return_all_scores=True,
            )
            
            # Save to local cache for future use
            try:
                model.model.save_pretrained(str(model_dir))
                model.tokenizer.save_pretrained(str(model_dir))
                
                # Save metadata
                metadata = {
                    "model_name": model_name,
                    "cached_at": time.time(),
                    "cache_version": "1.0"
                }
                with open(model_dir / "cache_metadata.json", "w") as f:
                    json.dump(metadata, f, indent=2)
                    
                self.logger.info(f"Cached model to {model_dir}")
            except Exception as e:
                self.logger.warning(f"Failed to cache model locally: {e}")
            
            return model
    
    def _load_with_download(self, model_name: str, model_type: str):
        """Download model on demand (CI/CD)"""
        if not TRANSFORMERS_AVAILABLE:
            raise ModelLoadingError("transformers library not available")
        
        temp_dir = Path(self.config["cache_dir"])
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Downloading {model_name} on demand to {temp_dir}")
        
        return pipeline(
            "sentiment-analysis",
            model=model_name,
            tokenizer=model_name,
            device=self.config["device"],
            return_all_scores=True,
            cache_dir=str(temp_dir)
        )
    
    def _load_from_hub(self, model_name: str, model_type: str):
        """Load directly from HuggingFace Hub"""
        if not TRANSFORMERS_AVAILABLE:
            raise ModelLoadingError("transformers library not available")
        
        self.logger.info(f"Loading {model_name} directly from HuggingFace Hub")
        
        return pipeline(
            "sentiment-analysis",
            model=model_name,
            tokenizer=model_name,
            device=self.config["device"],
            return_all_scores=True,
        )
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about loaded models and environment"""
        return {
            "environment": self.environment.value,
            "config": self.config,
            "loaded_models": list(self.models.keys()),
            "loading_history": self.loading_history,
            "transformers_available": TRANSFORMERS_AVAILABLE,
            "torch_available": TORCH_AVAILABLE
        }
    
    def clear_cache(self):
        """Clear loaded models from memory"""
        cleared_count = len(self.models)
        self.models.clear()
        self.logger.info(f"Cleared {cleared_count} models from cache")
    
    def warmup_models(self, model_list: List[Dict[str, str]]):
        """Pre-load common models for faster access"""
        self.logger.info(f"Warming up {len(model_list)} models")
        
        for model_info in model_list:
            try:
                model_name = model_info["name"]
                model_type = model_info.get("type", "sentiment")
                self.load_model(model_name, model_type)
            except Exception as e:
                self.logger.warning(f"Failed to warmup model {model_info}: {e}")

# Global model manager instance
_global_manager = None

def get_model_manager() -> SmartModelManager:
    """Get global model manager instance (singleton)"""
    global _global_manager
    if _global_manager is None:
        _global_manager = SmartModelManager()
    return _global_manager

def load_sentiment_model(model_name: str) -> Union[Any, MagicMock]:
    """Convenience function to load sentiment model"""
    manager = get_model_manager()
    return manager.load_model(model_name, "sentiment")

# Common model configurations
COMMON_MODELS = {
    "finbert": "ProsusAI/finbert",
    "cryptobert": "kk08/CryptoBERT", 
    "twitter_roberta": "cardiffnlp/twitter-roberta-base-sentiment-latest"
}

if __name__ == "__main__":
    # Example usage and testing
    manager = SmartModelManager()
    print(f"Environment: {manager.environment.value}")
    print(f"Config: {manager.config}")
    
    # Test model loading
    try:
        model = manager.load_model("ProsusAI/finbert", "sentiment")
        print(f"Successfully loaded model: {type(model)}")
        
        # Test with sample text
        if hasattr(model, '__call__'):
            result = model("This is a positive test message")
            print(f"Test result: {result}")
            
    except Exception as e:
        print(f"Model loading failed: {e}")
    
    print(f"Model info: {manager.get_model_info()}")