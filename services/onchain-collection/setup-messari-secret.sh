#!/bin/bash

# Setup Messari API secret for Enhanced Onchain Collector
# This is optional - the collector works without it but with reduced functionality

NAMESPACE="crypto-data-collection"

echo "🔐 Setting up Messari API secret for Enhanced Onchain Collector..."

# Check if secret already exists
if kubectl get secret messari-secret -n $NAMESPACE >/dev/null 2>&1; then
    echo "⚠️  Messari secret already exists. Skipping creation."
    echo "   To update, run: kubectl delete secret messari-secret -n $NAMESPACE"
    echo "   Then run this script again."
else
    echo "📝 Creating Messari API secret..."
    
    # Get Messari API key from user or environment
    if [ -z "$MESSARI_API_KEY" ]; then
        echo "📋 No MESSARI_API_KEY environment variable found."
        echo "   The collector will work without it but with reduced Messari data."
        echo "   You can add it later by setting the environment variable and re-running this script."
        
        # Create empty secret for now
        kubectl create secret generic messari-secret \
            --namespace=$NAMESPACE \
            --from-literal=api-key=""
        
        echo "✅ Created empty Messari secret. Collector will use CoinGecko only."
    else
        echo "🔑 Found MESSARI_API_KEY environment variable"
        
        # Create secret with the API key
        kubectl create secret generic messari-secret \
            --namespace=$NAMESPACE \
            --from-literal=api-key="$MESSARI_API_KEY"
        
        echo "✅ Messari API secret created successfully!"
    fi
fi

# Verify secret creation
echo ""
echo "🔍 Verifying Messari secret:"
kubectl get secret messari-secret -n $NAMESPACE -o yaml | grep -A 1 "data:" | tail -1 | awk '{print "   Secret length: " length($2) " characters"}'

echo ""
echo "📋 Messari Secret Setup Complete!"
echo "   The Enhanced Onchain Collector can now access Messari API (if key provided)"
echo "   Note: Messari API is optional - collector works with CoinGecko alone"