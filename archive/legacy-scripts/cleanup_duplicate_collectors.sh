#!/bin/bash

# Cleanup Duplicate Collectors Script
# This script removes all unauthorized collector duplicates

echo "🧹 Starting Duplicate Collectors Cleanup..."
echo "⚠️  This will remove all standalone collector services and keep only K8s deployments"

# Check if we're in the right directory
if [ ! -f ".copilot-instructions.md" ]; then
    echo "❌ Error: Please run this script from the crypto-data-collection root directory"
    exit 1
fi

echo ""
echo "📋 Official K8s Collectors (will be preserved):"
echo "  1. k8s/enhanced-technical-calculator.yaml"
echo "  2. k8s/enhanced-macro-collector-deployment.yaml"
echo "  3. k8s/collectors/enhanced-crypto-prices-automatic.yaml"
echo "  4. k8s/news-collector-deployment.yaml"
echo "  5. k8s/ohlc-collector-deployment.yaml"
echo "  6. k8s/onchain-collector-deployment.yaml"
echo "  7. k8s/fix-sentiment-collector.yaml"
echo ""

# Ask for confirmation
read -p "🔴 Do you want to proceed with cleanup? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Cleanup cancelled"
    exit 1
fi

echo ""
echo "🔄 Starting cleanup process..."

# Kill any running collector processes
echo "🛑 Terminating running collector processes..."
pkill -f "collector\.py" 2>/dev/null || echo "  No collector processes found"
pkill -f "calculator\.py" 2>/dev/null || echo "  No calculator processes found"
pkill -f "service\.py" 2>/dev/null || echo "  No service processes found"

# Remove services directory entirely
echo "🗑️  Removing services/ directory..."
if [ -d "services" ]; then
    echo "  Found services directory with:"
    find services/ -name "*.py" | sed 's/^/    /'
    rm -rf services/
    echo "  ✅ services/ directory removed"
else
    echo "  ℹ️  services/ directory not found"
fi

# Remove standalone collector scripts
echo "🗑️  Removing standalone collector scripts..."

# List of standalone collectors to remove
COLLECTORS_TO_REMOVE=(
    "daily_macro_collector.py"
    "enhanced_macro_collector.py"
    "onchain_collector.py"
    "premium_ohlc_collector.py"
    "premium_onchain_collector.py"
    "current_collector.py"
    "fixed_collector.py"
)

for collector in "${COLLECTORS_TO_REMOVE[@]}"; do
    if [ -f "$collector" ]; then
        echo "  Removing: $collector"
        rm -f "$collector"
    else
        echo "  Not found: $collector (already clean)"
    fi
done

# Keep utility scripts (list what we're keeping)
echo "✅ Keeping utility scripts (not collectors):"
UTILITIES=(
    "check_all_collectors.py"
    "check_collectors_fast.py"
    "check_collectors_simple.py"
    "debug_macro_collector.py"
    "monitor_enhanced_macro_collector.py"
    "test_collectors.py"
)

for utility in "${UTILITIES[@]}"; do
    if [ -f "$utility" ]; then
        echo "  ✅ Keeping: $utility (monitoring/testing utility)"
    fi
done

# Create a .gitignore entry to prevent recreation
echo ""
echo "🛡️  Adding protection against recreation..."

# Add services/ to gitignore if not already there
if ! grep -q "^services/$" .gitignore 2>/dev/null; then
    echo "" >> .gitignore
    echo "# Prevent recreation of duplicate collector services" >> .gitignore
    echo "services/" >> .gitignore
    echo "  ✅ Added services/ to .gitignore"
else
    echo "  ℹ️  services/ already in .gitignore"
fi

# Final verification
echo ""
echo "🔍 Cleanup verification:"

# Check for any remaining collector files
remaining_collectors=$(find . -name "*collector*.py" -not -path "./venv/*" -not -path "./.git/*" | grep -v -E "(check_|debug_|monitor_|test_)")
if [ -n "$remaining_collectors" ]; then
    echo "⚠️  Remaining collector files found:"
    echo "$remaining_collectors" | sed 's/^/    /'
    echo "  Please review these manually"
else
    echo "✅ No unauthorized collector files found"
fi

# Check for running processes
running_processes=$(ps aux | grep -E "collector|calculator" | grep -v grep | wc -l)
if [ $running_processes -gt 0 ]; then
    echo "⚠️  Still have running collector processes:"
    ps aux | grep -E "collector|calculator" | grep -v grep | sed 's/^/    /'
else
    echo "✅ No collector processes running"
fi

echo ""
echo "🎉 Cleanup Complete!"
echo ""
echo "📊 Summary:"
echo "  🗑️  Removed: Entire services/ directory"
echo "  🗑️  Removed: Standalone collector scripts"
echo "  🛑  Killed: Running collector processes"
echo "  ✅ Kept: Official K8s deployments"
echo "  ✅ Kept: Utility/monitoring scripts"
echo "  🛡️  Protected: Added .gitignore rules"
echo ""
echo "🎯 Result: Single source of truth - 7 K8s collectors only!"
echo ""
echo "📝 Next steps:"
echo "  1. Verify K8s collectors are deployed: kubectl get deployments -n crypto-data-collection"
echo "  2. Monitor K8s logs: kubectl logs -f deployment/[collector-name] -n crypto-data-collection"
echo "  3. Use only the 7 official K8s deployments for any collector changes"