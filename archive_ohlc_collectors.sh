#!/bin/bash
# OHLC Collectors Archive Script
# Keeping: unified-ohlc-collector
# Archiving: comprehensive-ohlc-collection, premium-ohlc-collection-job, working-ohlc-collection-job

echo "🗂️  Archiving OHLC collectors..."

echo "Backing up comprehensive-ohlc-collection..."
kubectl get cronjob comprehensive-ohlc-collection -n crypto-collectors -o yaml > comprehensive-ohlc-collection-backup.yaml

echo "Suspending comprehensive-ohlc-collection..."
kubectl patch cronjob comprehensive-ohlc-collection -n crypto-collectors -p '{"spec":{"suspend":true}}'

echo "Backing up premium-ohlc-collection-job..."
kubectl get cronjob premium-ohlc-collection-job -n crypto-collectors -o yaml > premium-ohlc-collection-job-backup.yaml

echo "Suspending premium-ohlc-collection-job..."
kubectl patch cronjob premium-ohlc-collection-job -n crypto-collectors -p '{"spec":{"suspend":true}}'

echo "Backing up working-ohlc-collection-job..."
kubectl get cronjob working-ohlc-collection-job -n crypto-collectors -o yaml > working-ohlc-collection-job-backup.yaml

echo "Suspending working-ohlc-collection-job..."
kubectl patch cronjob working-ohlc-collection-job -n crypto-collectors -p '{"spec":{"suspend":true}}'

echo "✅ Archive complete!"
echo "🎯 Keeping active: unified-ohlc-collector"
echo "🗂️  Archived: 3 collectors"
