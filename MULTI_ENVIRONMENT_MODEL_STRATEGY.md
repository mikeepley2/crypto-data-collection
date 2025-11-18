# 🧪 Multi-Environment Model Management Strategy

## 🎯 **The Challenge: K3s Production vs Development/Testing**

You're absolutely right! Our K3s persistent storage solution is perfect for production, but we need a seamless strategy for:

- **Local Development**: Developers working on their machines
- **Unit Tests**: Fast, isolated testing without external dependencies  
- **Integration Tests**: Full-stack testing in dev environment
- **CI/CD Pipeline**: GitHub Actions and automated testing
- **Production**: K3s with persistent shared storage

## 🏗️ **Multi-Tier Model Management Architecture**

### **Environment Detection Strategy**
```python
import os
from pathlib import Path
from enum import Enum

class ModelSource(Enum):
    PERSISTENT_VOLUME = "persistent_volume"     # K3s production
    LOCAL_CACHE = "local_cache"                 # Development
    MOCK_MODELS = "mock_models"                 # Unit tests
    DOWNLOAD_ON_DEMAND = "download_on_demand"   # CI/CD
    HUGGINGFACE_HUB = "huggingface_hub"        # Fallback

def detect_environment() -> ModelSource:
    """Automatically detect environment and return appropriate model source"""
    
    # 1. K3s Production - persistent volume exists
    if Path("/app/models/model-metadata.yaml").exists():
        return ModelSource.PERSISTENT_VOLUME
    
    # 2. Testing - explicit test environment
    if os.getenv("PYTEST_CURRENT_TEST") or os.getenv("TESTING") == "true":
        return ModelSource.MOCK_MODELS
    
    # 3. GitHub Actions - CI environment
    if os.getenv("GITHUB_ACTIONS") == "true":
        return ModelSource.DOWNLOAD_ON_DEMAND
    
    # 4. Local development - check for local cache
    local_cache = Path(os.getenv("MODEL_CACHE_DIR", "./model_cache"))
    if local_cache.exists() and (local_cache / "finbert").exists():
        return ModelSource.LOCAL_CACHE
    
    # 5. Fallback - download from HuggingFace Hub
    return ModelSource.HUGGINGFACE_HUB
```

## 🛠️ **Enhanced Model Loading System**

### **Smart Model Manager**
```python
from typing import Optional, Union, Dict, Any
from transformers import pipeline
from unittest.mock import MagicMock
import logging

class SmartModelManager:
    """Intelligent model manager that adapts to any environment"""
    
    def __init__(self):
        self.environment = detect_environment()
        self.models = {}
        self.logger = logging.getLogger(__name__)
        
        # Environment-specific configuration
        self.config = self._get_env_config()
    
    def _get_env_config(self) -> Dict[str, Any]:
        """Get configuration for current environment"""
        configs = {
            ModelSource.PERSISTENT_VOLUME: {
                "cache_dir": "/app/models",
                "local": True,
                "timeout": 30
            },
            ModelSource.LOCAL_CACHE: {
                "cache_dir": os.getenv("MODEL_CACHE_DIR", "./model_cache"),
                "local": True,
                "timeout": 60
            },
            ModelSource.MOCK_MODELS: {
                "cache_dir": None,
                "local": False,
                "timeout": 1
            },
            ModelSource.DOWNLOAD_ON_DEMAND: {
                "cache_dir": "/tmp/models",
                "local": False,
                "timeout": 300  # 5 minutes for download
            },
            ModelSource.HUGGINGFACE_HUB: {
                "cache_dir": None,
                "local": False,
                "timeout": 300
            }
        }
        return configs[self.environment]
    
    def load_model(self, model_name: str, model_type: str) -> Union[Any, MagicMock]:
        """Load model appropriate for current environment"""
        
        cache_key = f"{model_type}_{model_name.replace('/', '_')}"
        
        if cache_key in self.models:
            return self.models[cache_key]
        
        self.logger.info(f"Loading {model_type} model for {self.environment.value}")
        
        if self.environment == ModelSource.MOCK_MODELS:
            # Unit tests - return mock
            model = self._create_mock_model(model_type)
            
        elif self.environment == ModelSource.PERSISTENT_VOLUME:
            # K3s production - load from persistent volume
            model = self._load_from_persistent_volume(model_name, model_type)
            
        elif self.environment == ModelSource.LOCAL_CACHE:
            # Development - load from local cache or download
            model = self._load_from_local_cache(model_name, model_type)
            
        elif self.environment == ModelSource.DOWNLOAD_ON_DEMAND:
            # CI/CD - download to temp location
            model = self._load_with_download(model_name, model_type)
            
        else:
            # Fallback - HuggingFace Hub direct
            model = self._load_from_hub(model_name, model_type)
        
        self.models[cache_key] = model
        return model
    
    def _create_mock_model(self, model_type: str) -> MagicMock:
        """Create mock model for testing"""
        mock_model = MagicMock()
        
        if model_type == "sentiment":
            # Mock sentiment analysis results
            mock_model.return_value = [
                {
                    'label': 'POSITIVE',
                    'score': 0.85
                },
                {
                    'label': 'NEGATIVE', 
                    'score': 0.15
                }
            ]
        
        self.logger.info(f"Created mock {model_type} model")
        return mock_model
    
    def _load_from_persistent_volume(self, model_name: str, model_type: str):
        """Load from K3s persistent volume"""
        local_path = Path(self.config["cache_dir"]) / model_name.split("/")[-1]
        
        if not local_path.exists():
            raise FileNotFoundError(f"Model not found in persistent volume: {local_path}")
        
        return pipeline(
            "sentiment-analysis",
            model=str(local_path),
            tokenizer=str(local_path),
            device=-1,  # CPU
            return_all_scores=True,
        )
    
    def _load_from_local_cache(self, model_name: str, model_type: str):
        """Load from local development cache"""
        cache_dir = Path(self.config["cache_dir"])
        model_dir = cache_dir / model_name.split("/")[-1]
        
        if model_dir.exists():
            # Load from local cache
            self.logger.info(f"Loading {model_name} from local cache: {model_dir}")
            return pipeline(
                "sentiment-analysis",
                model=str(model_dir),
                tokenizer=str(model_dir),
                device=-1,
                return_all_scores=True,
            )
        else:
            # Download and cache locally
            self.logger.info(f"Downloading {model_name} to local cache")
            cache_dir.mkdir(parents=True, exist_ok=True)
            
            model = pipeline(
                "sentiment-analysis",
                model=model_name,
                tokenizer=model_name,
                device=-1,
                return_all_scores=True,
            )
            
            # Save to local cache for future use
            model.model.save_pretrained(str(model_dir))
            model.tokenizer.save_pretrained(str(model_dir))
            
            return model
    
    def _load_with_download(self, model_name: str, model_type: str):
        """Download model on demand (CI/CD)"""
        temp_dir = Path(self.config["cache_dir"])
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Downloading {model_name} on demand")
        
        return pipeline(
            "sentiment-analysis",
            model=model_name,
            tokenizer=model_name,
            device=-1,
            return_all_scores=True,
        )
    
    def _load_from_hub(self, model_name: str, model_type: str):
        """Load directly from HuggingFace Hub"""
        self.logger.info(f"Loading {model_name} from HuggingFace Hub")
        
        return pipeline(
            "sentiment-analysis",
            model=model_name,
            tokenizer=model_name,
            device=-1,
            return_all_scores=True,
        )

# Global model manager instance
model_manager = SmartModelManager()
```

## 🔧 **Updated Service Implementation**

### **Enhanced Sentiment Service with Multi-Environment Support**
```python
class EnhancedMLSentimentCollector(BaseCollector):
    """Enhanced ML Sentiment Collector with multi-environment support"""
    
    def __init__(self):
        config = MLSentimentCollectorConfig.from_env()
        super().__init__(config)
        
        # Initialize smart model manager
        self.model_manager = SmartModelManager()
        
        # Model pipelines - loaded on demand
        self.crypto_sentiment_pipeline = None
        self.stock_sentiment_pipeline = None
        self.model_loading_status = {
            "crypto": False,
            "stock": False
        }

    async def _ensure_models_loaded(self):
        """Ensure ML models are loaded and ready"""
        
        if not self.crypto_sentiment_pipeline:
            try:
                self.crypto_sentiment_pipeline = self.model_manager.load_model(
                    self.config.crypto_model, "sentiment"
                )
                self.model_loading_status["crypto"] = True
                self.logger.info("crypto_model_loaded_successfully", 
                               environment=self.model_manager.environment.value)
            except Exception as e:
                self.logger.error("crypto_model_loading_failed", error=str(e))
                
                # Only raise in production - use fallback in dev/test
                if self.model_manager.environment == ModelSource.PERSISTENT_VOLUME:
                    raise
                else:
                    # Use mock model as fallback
                    self.crypto_sentiment_pipeline = self.model_manager._create_mock_model("sentiment")
                    self.model_loading_status["crypto"] = True
                    self.logger.warning("using_mock_crypto_model")

        if not self.stock_sentiment_pipeline:
            try:
                self.stock_sentiment_pipeline = self.model_manager.load_model(
                    self.config.stock_model, "sentiment"  
                )
                self.model_loading_status["stock"] = True
                self.logger.info("stock_model_loaded_successfully",
                               environment=self.model_manager.environment.value)
            except Exception as e:
                self.logger.error("stock_model_loading_failed", error=str(e))
                
                # Only raise in production - use fallback in dev/test
                if self.model_manager.environment == ModelSource.PERSISTENT_VOLUME:
                    raise
                else:
                    # Use mock model as fallback
                    self.stock_sentiment_pipeline = self.model_manager._create_mock_model("sentiment")
                    self.model_loading_status["stock"] = True
                    self.logger.warning("using_mock_stock_model")
```

## 🧪 **Testing Strategy by Environment**

### **1. Unit Tests (MOCK_MODELS)**
```python
# tests/test_enhanced_sentiment_ml.py
import pytest
import os
from unittest.mock import patch

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Force test environment detection"""
    with patch.dict(os.environ, {"TESTING": "true"}):
        yield

@pytest.fixture
def sentiment_collector():
    """Create sentiment collector with mocked models"""
    collector = EnhancedMLSentimentCollector()
    return collector

async def test_sentiment_analysis_with_mocks(sentiment_collector):
    """Test sentiment analysis using mock models"""
    # Models are automatically mocked in test environment
    await sentiment_collector._ensure_models_loaded()
    
    # Verify mocks are used
    assert sentiment_collector.model_manager.environment == ModelSource.MOCK_MODELS
    assert sentiment_collector.model_loading_status["crypto"] == True
    assert sentiment_collector.model_loading_status["stock"] == True
    
    # Test analysis
    result = await sentiment_collector._analyze_sentiment("Test crypto news", "crypto")
    
    # Mock returns predictable results
    assert "score" in result
    assert "label" in result
```

### **2. Local Development (LOCAL_CACHE)**
```python
# Local development configuration
# .env.development
MODEL_CACHE_DIR=./model_cache
ENVIRONMENT=development

# Downloads models to ./model_cache/ on first run
# Reuses cached models on subsequent runs
```

### **3. Integration Tests (DOWNLOAD_ON_DEMAND)**
```python
# tests/test_integration_sentiment.py
import pytest
import os
from pathlib import Path

@pytest.fixture(scope="session")
def integration_test_environment():
    """Setup integration test with real models"""
    with patch.dict(os.environ, {
        "MODEL_CACHE_DIR": "/tmp/integration_models",
        "GITHUB_ACTIONS": "true"  # Force download mode
    }):
        yield

@pytest.mark.integration
async def test_real_sentiment_analysis(integration_test_environment):
    """Test with real models (slower, but comprehensive)"""
    collector = EnhancedMLSentimentCollector()
    await collector._ensure_models_loaded()
    
    # This will download real models to /tmp/
    assert collector.model_manager.environment == ModelSource.DOWNLOAD_ON_DEMAND
    
    # Test with real model
    result = await collector._analyze_sentiment(
        "Bitcoin price surge indicates bullish market sentiment", 
        "crypto"
    )
    
    # Real model returns actual predictions
    assert isinstance(result["score"], float)
    assert result["label"] in ["POSITIVE", "NEGATIVE", "NEUTRAL"]
```

### **4. CI/CD Configuration**
```yaml
# .github/workflows/complete-ci-cd.yml
- name: Run Unit Tests
  run: |
    # Unit tests use mocks - fast, no model downloads
    python -m pytest tests/test_*.py -v -m "not integration"

- name: Run Integration Tests  
  run: |
    # Integration tests download models on demand
    export MODEL_CACHE_DIR="/tmp/ci_models"
    export GITHUB_ACTIONS="true"
    python -m pytest tests/test_*.py -v -m "integration" --timeout=600
```

### **5. K3s Production (PERSISTENT_VOLUME)**
```yaml
# K3s deployment automatically uses persistent volume
# No code changes needed - environment detection handles it
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sentiment-analyzer
spec:
  template:
    spec:
      containers:
      - name: sentiment-analyzer
        image: megabob70/crypto-sentiment-analyzer:latest
        env:
        - name: MODEL_SOURCE
          value: "persistent_volume"  # Optional - auto-detected
        volumeMounts:
        - name: ml-models
          mountPath: /app/models
          readOnly: true
```

## 📊 **Environment Comparison Table**

| Environment | Model Source | Startup Time | Storage | Use Case |
|-------------|--------------|--------------|---------|----------|
| **Unit Tests** | Mock Models | <1s | None | Fast testing |
| **Local Dev** | Local Cache | 5-30s first run, 2s cached | ~/model_cache/ | Development |
| **Integration** | Download On-Demand | 60-180s | /tmp/ | CI testing |
| **Production** | Persistent Volume | 5-10s | K3s PV | Production |
| **Fallback** | HuggingFace Hub | 60-300s | None | Emergency |

## 🚀 **Implementation Benefits**

✅ **Zero Code Changes**: Same service code works in all environments  
✅ **Fast Unit Tests**: Mock models for instant testing  
✅ **Efficient Development**: Local caching prevents re-downloads  
✅ **Comprehensive CI/CD**: Real models for integration testing  
✅ **Optimized Production**: Persistent volume for maximum performance  
✅ **Automatic Fallbacks**: Graceful degradation in all environments  
✅ **Environment Detection**: Automatic configuration based on context  

## 🎯 **Next Steps**

This multi-environment strategy gives you the best of all worlds:

1. **Developers**: Fast local development with model caching
2. **Testing**: Lightning-fast unit tests + comprehensive integration tests  
3. **CI/CD**: Automated testing with real models when needed
4. **Production**: Ultimate performance with K3s persistent storage

Would you like me to implement this enhanced multi-environment model management system?