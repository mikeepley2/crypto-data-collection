#!/bin/bash

# Centralized Placeholder Manager Test Script
echo "🧪 Testing Centralized Placeholder Manager..."

# Configuration
API_BASE="http://localhost:8080"
TEST_RESULTS=""

# Function to test API endpoint
test_endpoint() {
    local endpoint="$1"
    local description="$2"
    local expected_status="${3:-200}"
    
    echo "Testing: $description ($endpoint)"
    
    response=$(curl -s -w "%{http_code}" -o /dev/null "$API_BASE$endpoint")
    
    if [ "$response" -eq "$expected_status" ]; then
        echo "✅ PASS: $description"
        TEST_RESULTS="$TEST_RESULTS\n✅ $description"
    else
        echo "❌ FAIL: $description (got $response, expected $expected_status)"
        TEST_RESULTS="$TEST_RESULTS\n❌ $description (HTTP $response)"
    fi
    echo ""
}

# Function to test placeholder creation via API
test_placeholder_creation() {
    echo "🔧 Testing placeholder creation..."
    
    response=$(curl -s -X POST "$API_BASE/create-placeholders")
    
    if echo "$response" | grep -q "started"; then
        echo "✅ PASS: Placeholder creation triggered successfully"
        TEST_RESULTS="$TEST_RESULTS\n✅ Placeholder creation API"
        
        # Wait a moment and check status
        echo "⏳ Waiting for placeholder creation to process..."
        sleep 5
        
        status=$(curl -s "$API_BASE/status" | grep -o '"total_placeholders_created":[0-9]*' | cut -d':' -f2)
        if [ ! -z "$status" ] && [ "$status" -gt 0 ]; then
            echo "✅ PASS: Placeholders created (count: $status)"
            TEST_RESULTS="$TEST_RESULTS\n✅ Placeholder creation execution"
        else
            echo "⚠️  WARNING: Placeholder creation may still be running"
            TEST_RESULTS="$TEST_RESULTS\n⚠️  Placeholder creation pending"
        fi
    else
        echo "❌ FAIL: Placeholder creation failed"
        TEST_RESULTS="$TEST_RESULTS\n❌ Placeholder creation API"
    fi
    echo ""
}

# Function to test database placeholder records
test_database_placeholders() {
    echo "🗄️  Testing database placeholder records..."
    
    # Test macro placeholders
    echo "Checking macro placeholders..."
    macro_count=$(mysql -h127.0.0.1 -unews_collector -p'99Rules!' -Dcrypto_prices -e "
        SELECT COUNT(*) FROM macro_indicators 
        WHERE data_source LIKE '%placeholder%' 
        AND indicator_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
    " -s -N 2>/dev/null || echo "0")
    
    echo "   Macro placeholders in last 7 days: $macro_count"
    
    # Test technical placeholders
    echo "Checking technical placeholders..."
    technical_count=$(mysql -h127.0.0.1 -unews_collector -p'99Rules!' -Dcrypto_prices -e "
        SELECT COUNT(*) FROM technical_indicators 
        WHERE data_source LIKE '%placeholder%' 
        AND timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
    " -s -N 2>/dev/null || echo "0")
    
    echo "   Technical placeholders in last 24 hours: $technical_count"
    
    # Test onchain placeholders
    echo "Checking onchain placeholders..."
    onchain_count=$(mysql -h127.0.0.1 -unews_collector -p'99Rules!' -Dcrypto_prices -e "
        SELECT COUNT(*) FROM crypto_onchain_data 
        WHERE data_source LIKE '%placeholder%' 
        AND data_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
    " -s -N 2>/dev/null || echo "0")
    
    echo "   Onchain placeholders in last 30 days: $onchain_count"
    
    if [ "$macro_count" -gt 0 ] || [ "$technical_count" -gt 0 ] || [ "$onchain_count" -gt 0 ]; then
        echo "✅ PASS: Database contains placeholder records"
        TEST_RESULTS="$TEST_RESULTS\n✅ Database placeholder records"
    else
        echo "⚠️  WARNING: No placeholder records found in database"
        TEST_RESULTS="$TEST_RESULTS\n⚠️  Database placeholder records"
    fi
    echo ""
}

# Function to test completeness calculation
test_completeness_calculation() {
    echo "📊 Testing completeness calculations..."
    
    # Get completeness summary from API
    completeness=$(curl -s "$API_BASE/completeness")
    
    if echo "$completeness" | grep -q "avg_completeness"; then
        echo "✅ PASS: Completeness summary available"
        TEST_RESULTS="$TEST_RESULTS\n✅ Completeness calculation API"
        
        # Extract some sample values
        macro_completeness=$(echo "$completeness" | grep -o '"macro":.*"avg_completeness":[0-9.]*' | grep -o '[0-9.]*$')
        if [ ! -z "$macro_completeness" ]; then
            echo "   Macro average completeness: ${macro_completeness}%"
        fi
        
    else
        echo "❌ FAIL: Completeness summary unavailable"
        TEST_RESULTS="$TEST_RESULTS\n❌ Completeness calculation API"
    fi
    echo ""
}

# Main test execution
main() {
    echo "🚀 Starting Placeholder Manager Tests"
    echo "=================================="
    echo ""
    
    # Wait for service to be ready
    echo "⏳ Waiting for placeholder manager to be ready..."
    for i in {1..10}; do
        if curl -s "$API_BASE/health" > /dev/null; then
            echo "✅ Service is ready!"
            break
        fi
        echo "   Attempt $i/10 - waiting..."
        sleep 2
    done
    echo ""
    
    # Basic API endpoint tests
    test_endpoint "/health" "Health check endpoint"
    test_endpoint "/status" "Status endpoint" 
    test_endpoint "/completeness" "Completeness endpoint"
    test_endpoint "/metrics" "Metrics endpoint"
    
    # Functionality tests
    test_placeholder_creation
    test_database_placeholders
    test_completeness_calculation
    
    # Summary
    echo "🎯 Test Summary"
    echo "=============="
    echo -e "$TEST_RESULTS"
    echo ""
    
    # Check if service is healthy
    status_response=$(curl -s "$API_BASE/status")
    if echo "$status_response" | grep -q '"health":"healthy"'; then
        echo "✅ Overall service health: HEALTHY"
    elif echo "$status_response" | grep -q '"health":"degraded"'; then
        echo "⚠️  Overall service health: DEGRADED"
    else
        echo "❌ Overall service health: UNKNOWN"
    fi
    
    echo ""
    echo "🔍 For detailed status, run: curl $API_BASE/status | jq"
    echo "📊 For metrics, run: curl $API_BASE/metrics"
    echo ""
}

# Check if curl is available
if ! command -v curl &> /dev/null; then
    echo "❌ ERROR: curl is required for testing"
    exit 1
fi

# Run tests
main