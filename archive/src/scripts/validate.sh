#!/bin/bash

# Data Collection Node Validation Script
# Comprehensive testing of the isolated data collection system

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="crypto-data-collection"
API_GATEWAY_SERVICE="data-api-gateway"
API_BASE_URL="http://data-api-gateway.crypto-data-collection.svc.cluster.local:8000"

# Test results
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

# Logging
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✅${NC} $1"
    ((TESTS_PASSED++))
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠️${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ❌${NC} $1"
    ((TESTS_FAILED++))
}

test_start() {
    ((TESTS_TOTAL++))
    log "TEST $TESTS_TOTAL: $1"
}

# Test infrastructure
test_namespace() {
    test_start "Checking if crypto-data-collection namespace exists"
    
    if kubectl get namespace "$NAMESPACE" &> /dev/null; then
        success "Namespace $NAMESPACE exists"
    else
        error "Namespace $NAMESPACE not found"
        return 1
    fi
}

test_database_pods() {
    test_start "Checking database pods status"
    
    local mysql_ready=$(kubectl get deployment mysql-data-collection -n "$NAMESPACE" -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
    local redis_ready=$(kubectl get deployment redis-data-collection -n "$NAMESPACE" -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
    
    if [ "$mysql_ready" -gt 0 ]; then
        success "MySQL deployment is ready ($mysql_ready replicas)"
    else
        error "MySQL deployment is not ready"
    fi
    
    if [ "$redis_ready" -gt 0 ]; then
        success "Redis deployment is ready ($redis_ready replicas)"
    else
        error "Redis deployment is not ready"
    fi
}

test_api_gateway_pods() {
    test_start "Checking API Gateway pods status"
    
    local gateway_ready=$(kubectl get deployment "$API_GATEWAY_SERVICE" -n "$NAMESPACE" -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
    
    if [ "$gateway_ready" -gt 0 ]; then
        success "API Gateway deployment is ready ($gateway_ready replicas)"
    else
        error "API Gateway deployment is not ready"
    fi
}

test_database_connectivity() {
    test_start "Testing database connectivity"
    
    local mysql_pod=$(kubectl get pods -n "$NAMESPACE" -l app=mysql-data-collection -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
    local redis_pod=$(kubectl get pods -n "$NAMESPACE" -l app=redis-data-collection -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
    
    if [ -n "$mysql_pod" ]; then
        if kubectl exec -n "$NAMESPACE" "$mysql_pod" -- mysql -u root -p"$(kubectl get secret database-credentials -n "$NAMESPACE" -o jsonpath='{.data.MYSQL_ROOT_PASSWORD}' | base64 -d)" -e "SELECT 1" &> /dev/null; then
            success "MySQL connectivity test passed"
        else
            error "MySQL connectivity test failed"
        fi
    else
        error "MySQL pod not found"
    fi
    
    if [ -n "$redis_pod" ]; then
        if kubectl exec -n "$NAMESPACE" "$redis_pod" -- redis-cli ping &> /dev/null; then
            success "Redis connectivity test passed"
        else
            error "Redis connectivity test failed"
        fi
    else
        error "Redis pod not found"
    fi
}

test_api_gateway_health() {
    test_start "Testing API Gateway health endpoint"
    
    local gateway_pod=$(kubectl get pods -n "$NAMESPACE" -l app="$API_GATEWAY_SERVICE" -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
    
    if [ -n "$gateway_pod" ]; then
        if kubectl exec -n "$NAMESPACE" "$gateway_pod" -- curl -sf http://localhost:8000/health &> /dev/null; then
            success "API Gateway health check passed"
        else
            error "API Gateway health check failed"
        fi
    else
        error "API Gateway pod not found"
    fi
}

test_api_endpoints() {
    test_start "Testing API endpoints availability"
    
    local gateway_pod=$(kubectl get pods -n "$NAMESPACE" -l app="$API_GATEWAY_SERVICE" -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
    
    if [ -n "$gateway_pod" ]; then
        local endpoints=(
            "/health"
            "/ready"
            "/api/v1/stats/collectors"
        )
        
        for endpoint in "${endpoints[@]}"; do
            if kubectl exec -n "$NAMESPACE" "$gateway_pod" -- curl -sf "http://localhost:8000$endpoint" &> /dev/null; then
                success "Endpoint $endpoint is accessible"
            else
                error "Endpoint $endpoint is not accessible"
            fi
        done
    else
        error "API Gateway pod not found for endpoint testing"
    fi
}

test_service_discovery() {
    test_start "Testing Kubernetes service discovery"
    
    local gateway_pod=$(kubectl get pods -n "$NAMESPACE" -l app="$API_GATEWAY_SERVICE" -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
    
    if [ -n "$gateway_pod" ]; then
        # Test internal service resolution
        if kubectl exec -n "$NAMESPACE" "$gateway_pod" -- nslookup mysql-data-collection.crypto-data-collection.svc.cluster.local &> /dev/null; then
            success "MySQL service discovery working"
        else
            error "MySQL service discovery failed"
        fi
        
        if kubectl exec -n "$NAMESPACE" "$gateway_pod" -- nslookup redis-data-collection.crypto-data-collection.svc.cluster.local &> /dev/null; then
            success "Redis service discovery working"
        else
            error "Redis service discovery failed"
        fi
    else
        error "API Gateway pod not found for service discovery testing"
    fi
}

test_network_isolation() {
    test_start "Testing network isolation from trading system"
    
    # Check if trading namespace exists and test isolation
    if kubectl get namespace crypto-trading &> /dev/null; then
        local trading_pod=$(kubectl get pods -n crypto-trading -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
        
        if [ -n "$trading_pod" ]; then
            # Test that trading pods can access data APIs (should work)
            if kubectl exec -n crypto-trading "$trading_pod" -- curl -sf "$API_BASE_URL/health" --connect-timeout 5 &> /dev/null; then
                success "Trading system can access data collection APIs"
            else
                warning "Trading system cannot access data collection APIs (may need configuration)"
            fi
            
            # Test that trading pods cannot directly access databases (should fail)
            if kubectl exec -n crypto-trading "$trading_pod" -- nc -z mysql-data-collection.crypto-data-collection.svc.cluster.local 3306 --timeout=2 &> /dev/null; then
                warning "Trading system can directly access MySQL (may indicate insufficient isolation)"
            else
                success "Trading system cannot directly access MySQL (good isolation)"
            fi
        else
            warning "No trading pods found for isolation testing"
        fi
    else
        warning "crypto-trading namespace not found - skipping isolation tests"
    fi
}

test_performance() {
    test_start "Testing API performance"
    
    local gateway_pod=$(kubectl get pods -n "$NAMESPACE" -l app="$API_GATEWAY_SERVICE" -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
    
    if [ -n "$gateway_pod" ]; then
        # Test response time (should be < 1 second for health check)
        local start_time=$(date +%s.%N)
        if kubectl exec -n "$NAMESPACE" "$gateway_pod" -- curl -sf http://localhost:8000/health &> /dev/null; then
            local end_time=$(date +%s.%N)
            local duration=$(echo "$end_time - $start_time" | bc -l)
            
            if (( $(echo "$duration < 1.0" | bc -l) )); then
                success "API response time is good (${duration}s)"
            else
                warning "API response time is slow (${duration}s)"
            fi
        else
            error "Performance test failed - API not responding"
        fi
    else
        error "API Gateway pod not found for performance testing"
    fi
}

test_data_collection_isolation() {
    test_start "Verifying data collection operates independently"
    
    # Check if any data collection services are still in crypto-collectors namespace
    if kubectl get namespace crypto-collectors &> /dev/null; then
        local old_collectors=$(kubectl get pods -n crypto-collectors 2>/dev/null | grep -c "Running" || echo "0")
        if [ "$old_collectors" -gt 0 ]; then
            warning "$old_collectors old collection services still running in crypto-collectors namespace"
        else
            success "No old collection services found - clean migration"
        fi
    else
        success "Old crypto-collectors namespace not found - complete isolation"
    fi
    
    # Check resource allocation
    local data_collection_pods=$(kubectl get pods -n "$NAMESPACE" --no-headers | wc -l)
    if [ "$data_collection_pods" -gt 0 ]; then
        success "Data collection running with $data_collection_pods pods in isolated namespace"
    else
        error "No data collection pods found"
    fi
}

# Generate validation report
generate_report() {
    log "Generating validation report..."
    
    local report_file="data-collection-validation-report-$(date +'%Y%m%d-%H%M%S').md"
    
    cat << EOF > "$report_file"
# Data Collection Node Validation Report

**Validation Date**: $(date)
**Namespace**: $NAMESPACE
**Tests Passed**: $TESTS_PASSED
**Tests Failed**: $TESTS_FAILED
**Total Tests**: $TESTS_TOTAL
**Success Rate**: $(echo "scale=2; $TESTS_PASSED * 100 / $TESTS_TOTAL" | bc -l)%

## Infrastructure Status

### Namespace Status
$(kubectl get namespace "$NAMESPACE" -o wide 2>/dev/null || echo "Namespace not found")

### Pod Status
\`\`\`
$(kubectl get pods -n "$NAMESPACE" -o wide 2>/dev/null || echo "No pods found")
\`\`\`

### Service Status
\`\`\`
$(kubectl get services -n "$NAMESPACE" -o wide 2>/dev/null || echo "No services found")
\`\`\`

### Deployment Status
\`\`\`
$(kubectl get deployments -n "$NAMESPACE" -o wide 2>/dev/null || echo "No deployments found")
\`\`\`

## API Gateway Status

### Health Check
\`\`\`
$(kubectl exec -n "$NAMESPACE" "$(kubectl get pods -n "$NAMESPACE" -l app="$API_GATEWAY_SERVICE" -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "gateway-pod")" -- curl -s http://localhost:8000/health 2>/dev/null || echo "Health check failed")
\`\`\`

### Statistics
\`\`\`
$(kubectl exec -n "$NAMESPACE" "$(kubectl get pods -n "$NAMESPACE" -l app="$API_GATEWAY_SERVICE" -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "gateway-pod")" -- curl -s http://localhost:8000/api/v1/stats/collectors 2>/dev/null || echo "Statistics not available")
\`\`\`

## Test Results Summary

$(if [ $TESTS_FAILED -eq 0 ]; then
    echo "🎉 **ALL TESTS PASSED** - Data collection node is fully operational"
else
    echo "⚠️ **$TESTS_FAILED TESTS FAILED** - Some issues need attention"
fi)

## Recommendations

$(if [ $TESTS_FAILED -eq 0 ]; then
    echo "✅ The data collection node is ready for production use"
    echo "✅ Trading system can be safely updated to use data APIs"
    echo "✅ Old collection services can be safely removed"
else
    echo "❌ Address failed tests before proceeding with migration"
    echo "❌ Check pod logs for detailed error information"
    echo "❌ Verify configuration and resource availability"
fi)

## Next Steps

1. Monitor the data collection system performance
2. Update trading services to use data APIs
3. Validate data quality and collection rates
4. Set up monitoring and alerting
5. Document operational procedures

---

Generated by data collection validation script on $(date)
EOF

    success "Validation report generated: $report_file"
}

# Main validation function
main() {
    log "Starting data collection node validation..."
    
    echo "================================================================="
    echo "🔍 DATA COLLECTION NODE VALIDATION"
    echo "================================================================="
    echo
    
    # Run all validation tests
    test_namespace
    test_database_pods
    test_api_gateway_pods
    test_database_connectivity
    test_api_gateway_health
    test_api_endpoints
    test_service_discovery
    test_network_isolation
    test_performance
    test_data_collection_isolation
    
    echo
    echo "================================================================="
    echo "📊 VALIDATION SUMMARY"
    echo "================================================================="
    echo
    echo "Tests Passed: $TESTS_PASSED"
    echo "Tests Failed: $TESTS_FAILED"
    echo "Total Tests: $TESTS_TOTAL"
    echo "Success Rate: $(echo "scale=2; $TESTS_PASSED * 100 / $TESTS_TOTAL" | bc -l)%"
    echo
    
    if [ $TESTS_FAILED -eq 0 ]; then
        success "🎉 ALL TESTS PASSED - Data collection node is operational!"
        echo "✅ The isolated data collection system is ready for use"
        echo "✅ Trading system can safely use the data APIs"
    else
        error "❌ $TESTS_FAILED tests failed - issues need attention"
        echo "🔧 Check the detailed logs and fix issues before proceeding"
    fi
    
    generate_report
    
    echo
    echo "================================================================="
    echo "📚 USEFUL COMMANDS"
    echo "================================================================="
    echo "Monitor pods:     kubectl get pods -n $NAMESPACE -w"
    echo "Check logs:       kubectl logs -f deployment/data-api-gateway -n $NAMESPACE"
    echo "Port forward:     kubectl port-forward svc/data-api-gateway 8000:8000 -n $NAMESPACE"
    echo "Test API:         curl http://localhost:8000/health"
    echo "Delete if needed: kubectl delete namespace $NAMESPACE"
    echo "================================================================="
}

# Run validation
main "$@"