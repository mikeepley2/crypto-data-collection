# Quick ML Sentiment Deployment Checklist

## Pre-Deployment Checklist

- [ ] Kubernetes cluster is running
- [ ] kubectl is configured and can access the cluster
- [ ] crypto-data-collection namespace exists
- [ ] Database is accessible from the cluster
- [ ] Sufficient resources available (minimum 2Gi memory, 1 CPU)

## Deployment Steps

### 1. Create ML Sentiment Code
```bash
# Copy the enhanced_ml_sentiment.py file to docker/sentiment-services/
# (File should already exist from previous deployment)
```

### 2. Create ConfigMap
```bash
kubectl create configmap enhanced-sentiment-ml-code \
  --from-file=enhanced_ml_sentiment.py=docker/sentiment-services/enhanced_ml_sentiment.py \
  -n crypto-data-collection
```

### 3. Deploy Service
```bash
kubectl patch deployment enhanced-sentiment-collector -n crypto-data-collection \
  --patch-file k8s/collectors/enhanced-sentiment-collector-ml-update.yaml
```

### 4. Monitor Progress
```bash
# Check pod status
kubectl get pods -n crypto-data-collection -l app=enhanced-sentiment-collector

# Monitor logs
kubectl logs -f deployment/enhanced-sentiment-collector -n crypto-data-collection
```

## Expected Timeline

- **System Dependencies**: 2-3 minutes
- **Python Packages**: 1-2 minutes  
- **PyTorch Installation**: 5-8 minutes (900MB download)
- **Transformers Library**: 1-2 minutes
- **Model Download**: 2-3 minutes
- **Service Startup**: 30 seconds

**Total Time**: 10-15 minutes

## Success Indicators

- [ ] Pod status shows "Running" and "Ready"
- [ ] Logs show "✅ CryptoBERT model loaded successfully"
- [ ] Logs show "✅ FinBERT model loaded successfully"
- [ ] Health endpoint returns status "healthy"
- [ ] Both crypto_model_loaded and stock_model_loaded are true

## Testing Commands

```bash
# Port forward to service
kubectl port-forward svc/enhanced-sentiment-collector 8000:8000 -n crypto-data-collection

# Test health
curl http://localhost:8000/health

# Test sentiment analysis
curl -X POST "http://localhost:8000/sentiment" \
  -H "Content-Type: application/json" \
  -d '{"text": "Bitcoin is going to the moon!", "market_type": "crypto"}'
```

## Troubleshooting

### Pod Stuck in CrashLoopBackOff
- Check logs for specific error messages
- Ensure sufficient memory limits (minimum 2Gi)
- Verify ConfigMap exists and is correct

### Package Installation Fails
- Remove any PyTorch-specific index URLs from pip install
- Ensure internet connectivity for package downloads

### Model Loading Fails
- Check Hugging Face model availability
- Verify sufficient memory for model loading
- Check logs for specific model loading errors

## Rollback Plan

If deployment fails, rollback to working collector:

```bash
# Delete the problematic deployment
kubectl delete deployment enhanced-sentiment-collector -n crypto-data-collection

# The old working pod should still be running
kubectl get pods -n crypto-data-collection -l app=enhanced-sentiment-collector
```

## Resource Requirements

- **Memory**: Minimum 2Gi, Recommended 4Gi
- **CPU**: Minimum 1 core, Recommended 2 cores
- **Storage**: Temporary space for model downloads (~2GB)
- **Network**: Internet access for model downloads

## Notes

- The deployment uses runtime installation to avoid Kind cluster image loading issues
- Models are downloaded from Hugging Face during startup
- Service automatically detects market type (crypto vs stock) based on keywords
- CPU-only inference to avoid GPU dependencies
- Background processing handles article sentiment analysis automatically


