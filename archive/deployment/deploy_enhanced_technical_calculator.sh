#!/bin/bash

# Deploy Enhanced Technical Calculator
# This script replaces the old technical calculator with the enhanced version

echo "🚀 Deploying Enhanced Technical Calculator..."

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found. Please install kubectl first."
    exit 1
fi

# Check if namespace exists
kubectl get namespace crypto-data-collection &> /dev/null
if [ $? -ne 0 ]; then
    echo "📦 Creating namespace crypto-data-collection..."
    kubectl create namespace crypto-data-collection
fi

# Remove old technical calculator if it exists
echo "🧹 Removing old technical calculator deployment..."
kubectl delete deployment technical-calculator -n crypto-data-collection --ignore-not-found=true
kubectl delete configmap technical-calculator-code -n crypto-data-collection --ignore-not-found=true

# Apply the enhanced technical calculator
echo "📊 Applying enhanced technical calculator..."
kubectl apply -f k8s/enhanced-technical-calculator.yaml

# Wait for deployment to be ready
echo "⏳ Waiting for deployment to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/enhanced-technical-calculator -n crypto-data-collection

# Check deployment status
echo "📋 Deployment Status:"
kubectl get deployment enhanced-technical-calculator -n crypto-data-collection
kubectl get pods -l app=enhanced-technical-calculator -n crypto-data-collection

# Show logs
echo "📄 Recent logs:"
kubectl logs -l app=enhanced-technical-calculator -n crypto-data-collection --tail=20

echo ""
echo "✅ Enhanced Technical Calculator deployment complete!"
echo ""
echo "📊 Key Features:"
echo "  • Comprehensive technical indicators (RSI, MACD, Bollinger Bands, SMA/EMA, ATR)"
echo "  • Uses OHLC data for accurate calculations"
echo "  • Runs every 2 hours"
echo "  • Enhanced connection pooling"
echo "  • Better error handling and logging"
echo ""
echo "🔍 Monitor deployment:"
echo "  kubectl logs -f deployment/enhanced-technical-calculator -n crypto-data-collection"
echo ""
echo "🚀 Check health:"
echo "  kubectl exec -it deployment/enhanced-technical-calculator -n crypto-data-collection -- cat /tmp/enhanced_technical_calculator_health.txt"