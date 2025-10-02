#!/bin/bash

# Apply materialized updater fixes automatically

echo "🔧 Applying materialized updater fixes..."

# Find the materialized updater pod
POD_NAME=$(kubectl get pods -n crypto-collectors -l app=materialized-updater --field-selector=status.phase=Running -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)

if [ -z "$POD_NAME" ]; then
    echo "❌ No running materialized-updater pod found"
    exit 1
fi

echo "📦 Found materialized updater pod: $POD_NAME"

# Copy the fixed script
echo "📋 Copying fixed materialized_updater_enhanced.py..."
kubectl cp materialized_updater_enhanced.py crypto-collectors/$POD_NAME:/app/materialized_updater_enhanced.py

echo "🔄 Replacing main script..."
kubectl exec -n crypto-collectors $POD_NAME -- cp /app/materialized_updater_enhanced.py /app/materialized_updater_fixed.py

echo "🔄 Restarting the process..."
kubectl delete pod $POD_NAME -n crypto-collectors

echo "⏳ Waiting for new pod to start..."
sleep 10

# Wait for new pod
NEW_POD_NAME=$(kubectl get pods -n crypto-collectors -l app=materialized-updater --field-selector=status.phase=Running -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)

if [ -z "$NEW_POD_NAME" ]; then
    echo "⏳ Pod still starting, checking again..."
    sleep 10
    NEW_POD_NAME=$(kubectl get pods -n crypto-collectors -l app=materialized-updater --field-selector=status.phase=Running -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
fi

if [ ! -z "$NEW_POD_NAME" ]; then
    echo "✅ New pod started: $NEW_POD_NAME"
    echo "🔧 Applying fix to new pod..."
    kubectl cp materialized_updater_enhanced.py crypto-collectors/$NEW_POD_NAME:/app/materialized_updater_fixed.py
    
    echo "🔄 Restarting process one more time..."
    kubectl delete pod $NEW_POD_NAME -n crypto-collectors
    
    echo "✅ Materialized updater fix applied!"
    echo "💡 Check logs with: kubectl logs -f -n crypto-collectors -l app=materialized-updater"
else
    echo "❌ Could not find new running pod"
fi