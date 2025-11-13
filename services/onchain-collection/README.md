# Onchain Data Collection Service

## Overview
Comprehensive onchain data collector for blockchain metrics and indicators. Collects real-time blockchain data from multiple sources including Messari API.

## Features
- **Blockchain Metrics**: Transaction volumes, network activity, hash rates
- **Market Indicators**: On-chain market signals, whale movements, exchange flows  
- **Network Statistics**: Active addresses, transaction fees, mining data
- **Real-time Collection**: Continuous data collection with gap detection
- **FastAPI Endpoints**: Health monitoring and data access APIs
- **Production Ready**: Full error handling, logging, and Kubernetes compatibility

## Deployment
This service runs as a CronJob in Kubernetes for scheduled onchain data collection.

**Active Deployment**: `onchain-collector` CronJob in `crypto-data-collection` namespace

## Data Collection
Collects comprehensive onchain metrics contributing to the 258+ ML features for crypto market analysis.
