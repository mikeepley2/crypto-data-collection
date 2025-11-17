# Archive Directory - Duplicate Collectors

## Purpose
This directory contains duplicate collector implementations that were consolidated into K8s deployments.

## Structure

### services-duplicate/
Contains the entire `services/` directory that duplicated K8s functionality:
- `macro-collection/` - Duplicated k8s/enhanced-macro-collector-deployment.yaml
- `news-collection/` - Duplicated k8s/news-collector-deployment.yaml  
- `ohlc-collection/` - Duplicated k8s/ohlc-collector-deployment.yaml
- `onchain-collection/` - Duplicated k8s/onchain-collector-deployment.yaml
- `price-collection/` - Duplicated k8s/collectors/enhanced-crypto-prices-automatic.yaml
- `technical-collection/` - Duplicated k8s/enhanced-technical-calculator.yaml

### standalone-scripts/
Contains standalone collector scripts that duplicated K8s functionality:
- `enhanced_macro_collector.py` - Source for K8s macro collector (used in consolidation)
- `daily_macro_collector.py` - Alternative macro implementation
- `onchain_collector.py` - Old onchain implementation
- `premium_ohlc_collector.py` - Premium OHLC features (may need review)
- `premium_onchain_collector.py` - Premium onchain features (may need review)

## Status

**✅ CONSOLIDATED**: All functionality has been reviewed and critical features moved to official K8s collectors

**⚠️ FOR REVIEW**: Premium collectors may have unique features that could be integrated

**🗑️ TO DELETE**: This entire directory can be deleted after final review

## Official K8s Collectors (Single Source of Truth)

1. `k8s/enhanced-technical-calculator.yaml` - Technical indicators
2. `k8s/enhanced-macro-collector-deployment.yaml` - Macro economics (✅ Updated with full implementation)
3. `k8s/collectors/enhanced-crypto-prices-automatic.yaml` - Price data
4. `k8s/news-collector-deployment.yaml` - News collection
5. `k8s/ohlc-collector-deployment.yaml` - OHLC data
6. `k8s/onchain-collector-deployment.yaml` - On-chain metrics
7. `k8s/fix-sentiment-collector.yaml` - Sentiment analysis