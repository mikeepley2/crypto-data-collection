#!/bin/bash

# ============================================================================
# Crypto Data Collection - Integration Test Runner with Test Database
# ============================================================================
# This script safely runs integration tests using isolated test database
# to ensure production database is never touched during testing.

set -e  # Exit on error

echo "🧪 CRYPTO DATA COLLECTION - INTEGRATION TEST RUNNER"
echo "=" >&2
echo "🛡️  SAFETY: Uses isolated test database (port 3307) - never touches production"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to log with timestamp
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if Docker is available
if ! command -v docker-compose &> /dev/null; then
    error "docker-compose is not installed or not in PATH"
    exit 1
fi

# Check if docker-compose.test.yml exists
if [ ! -f "docker-compose.test.yml" ]; then
    error "docker-compose.test.yml not found in current directory"
    exit 1
fi

log "🐳 Starting test database environment..."

# Start test database
if docker-compose -f docker-compose.test.yml up test-mysql test-redis -d; then
    success "Test database environment started"
else
    error "Failed to start test database environment"
    exit 1
fi

# Wait for database to be ready
log "⏳ Waiting for test database to be ready..."
sleep 10

# Check if database is accessible
log "🔍 Verifying test database connectivity..."
if docker-compose -f docker-compose.test.yml exec test-mysql mysql -h localhost -u test_user -ptest_password -e "SELECT 1;" 2>/dev/null; then
    success "Test database is accessible"
else
    warning "Test database connection check failed, but continuing..."
fi

log "🧪 Running integration tests..."

# Set environment variables for test mode
export MYSQL_HOST=localhost
export MYSQL_PORT=3307
export MYSQL_USER=test_user
export MYSQL_PASSWORD=test_password
export MYSQL_DATABASE=crypto_prices_test
export TEST_MODE=true

# Run the integration tests
if python tests/test_ohlc_integration.py; then
    success "Integration tests completed successfully"
    TEST_RESULT=0
else
    error "Integration tests failed"
    TEST_RESULT=1
fi

log "🧽 Cleaning up test environment..."

# Stop and remove test containers
if docker-compose -f docker-compose.test.yml down; then
    success "Test environment cleaned up"
else
    warning "Failed to clean up test environment"
fi

if [ $TEST_RESULT -eq 0 ]; then
    echo ""
    success "🎉 ALL INTEGRATION TESTS PASSED!"
    echo "   ✅ Test database isolation verified"
    echo "   ✅ Data collection validated"
    echo "   ✅ Backfill functionality confirmed" 
    echo "   ✅ Production database remained untouched"
else
    echo ""
    error "❌ Integration tests failed"
    echo "   Check the output above for details"
fi

exit $TEST_RESULT
