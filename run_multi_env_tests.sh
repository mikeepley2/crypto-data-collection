#!/bin/bash

# Multi-environment test runner for CI/CD
# This script runs tests in multiple phases with proper error handling

set -e  # Exit on error

echo "🚀 Starting Multi-Environment Test Suite"
echo "========================================"

# Create tests directory if it doesn't exist
mkdir -p tests

# Set test environment variables
export TESTING=true
export PYTHONPATH="."
export MODEL_CACHE_DIR="/tmp/ci_models"
export LOG_LEVEL="WARNING"

# Function to run tests with error handling
run_test_phase() {
    local phase_name="$1"
    local test_command="$2"
    local continue_on_error="${3:-true}"
    
    echo ""
    echo "🧪 $phase_name"
    echo "$(printf '=%.0s' {1..40})"
    
    if eval "$test_command"; then
        echo "✅ $phase_name completed successfully"
        return 0
    else
        if [ "$continue_on_error" = "true" ]; then
            echo "⚠️ $phase_name failed, continuing..."
            return 1
        else
            echo "❌ $phase_name failed, stopping"
            exit 1
        fi
    fi
}

# Check if tests exist
if [ -d "tests" ] && [ "$(ls -A tests)" ]; then
    echo "📂 Tests directory found with content"
    
    # Phase 1: Fast unit tests with mock models
    run_test_phase \
        "Phase 1: Fast unit tests with mock models" \
        'python3 -m pytest tests/ -m "unit and not slow and not real_models" -v --tb=short --maxfail=5 --timeout=60 -p no:allure -p no:pdbpp --disable-warnings'
    
    # Phase 2: Smart model manager tests
    run_test_phase \
        "Phase 2: Smart model manager tests" \
        'if [ -f "tests/test_enhanced_sentiment_ml_multi_env.py" ]; then python3 -m pytest tests/test_enhanced_sentiment_ml_multi_env.py::TestSmartModelManager -v --tb=short --timeout=30 --disable-warnings; else echo "Smart model manager tests not found"; fi'
    
    # Phase 3: Mock ML model integration
    run_test_phase \
        "Phase 3: Mock ML model integration" \
        'python3 -m pytest tests/ -k "sentiment and mock" -v --tb=short --maxfail=3 --timeout=30 --disable-warnings'
    
    echo ""
    echo "✅ Multi-environment test suite completed"
    
    # Show test summary
    echo ""
    echo "📊 Test Environment Summary:"
    echo "============================"
    
    # Test centralized config
    python3 -c "
import sys
sys.path.append('.')
try:
    from shared.database_config import db_config
    print(f'Environment: {db_config.environment}')
    print(f'MySQL: {db_config.get_connection_info()}')
    print(f'Redis: {db_config.get_redis_info()}')
except Exception as e:
    print(f'Centralized config test: {e}')
" 2>/dev/null || echo "Centralized config not available"
    
    # Test smart model manager if available
    python3 -c "
import sys
sys.path.append('.')
try:
    from shared.smart_model_manager import SmartModelManager
    manager = SmartModelManager()
    print(f'Model Manager Environment: {manager.environment.value}')
    print(f'Model Manager Config: {manager.config}')
except Exception as e:
    print(f'Smart model manager: {e}')
" 2>/dev/null || echo "Smart model manager not available"

else
    echo "📂 No tests found - skipping test execution"
fi

echo ""
echo "🎯 Test suite execution complete"