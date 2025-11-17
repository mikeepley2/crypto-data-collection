# Data Collection Node Validation Script (PowerShell)
# Quick validation of the crypto data collection deployment

Write-Host "🔍 DATA COLLECTION NODE VALIDATION" -ForegroundColor Blue
Write-Host "==================================" -ForegroundColor Blue

$namespace = "crypto-data-collection"
$passed = 0
$failed = 0

function Test-Component {
    param(
        [string]$Name,
        [scriptblock]$Test
    )
    
    Write-Host "`nTesting: $Name" -ForegroundColor Yellow
    try {
        $result = & $Test
        if ($result) {
            Write-Host "✅ PASS: $Name" -ForegroundColor Green
            return $true
        } else {
            Write-Host "❌ FAIL: $Name" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Host "❌ ERROR in $Name`: $_" -ForegroundColor Red
        return $false
    }
}

# Test 1: Check if namespace exists
$test1 = Test-Component "Namespace Exists" {
    kubectl get namespace $namespace 2>$null
    return $LASTEXITCODE -eq 0
}
if ($test1) { $passed++ } else { $failed++ }

# Test 2: Check pods
$test2 = Test-Component "Pods Status" {
    $pods = kubectl get pods -n $namespace --no-headers 2>$null
    if ($pods) {
        Write-Host "Pods found:`n$pods" -ForegroundColor Cyan
        return $true
    }
    return $false
}
if ($test2) { $passed++ } else { $failed++ }

# Test 3: Check services
$test3 = Test-Component "Services Status" {
    $services = kubectl get services -n $namespace --no-headers 2>$null
    if ($services) {
        Write-Host "Services found:`n$services" -ForegroundColor Cyan
        return $true
    }
    return $false
}
if ($test3) { $passed++ } else { $failed++ }

# Test 4: Check deployments
$test4 = Test-Component "Deployments Status" {
    $deployments = kubectl get deployments -n $namespace --no-headers 2>$null
    if ($deployments) {
        Write-Host "Deployments found:`n$deployments" -ForegroundColor Cyan
        return $true
    }
    return $false
}
if ($test4) { $passed++ } else { $failed++ }

# Test 5: Check Docker image
$test5 = Test-Component "Docker Image Available" {
    $image = docker images crypto-data-collection/api-gateway:latest --format "table {{.Repository}}:{{.Tag}}" 2>$null
    if ($image -and $image -notlike "*REPOSITORY*") {
        Write-Host "Docker image found: $image" -ForegroundColor Cyan
        return $true
    }
    return $false
}
if ($test5) { $passed++ } else { $failed++ }

# Test 6: Check secrets
$test6 = Test-Component "Secrets Configuration" {
    $secrets = kubectl get secrets -n $namespace --no-headers 2>$null
    if ($secrets) {
        Write-Host "Secrets found:`n$secrets" -ForegroundColor Cyan
        return $true
    }
    return $false
}
if ($test6) { $passed++ } else { $failed++ }

# Summary
Write-Host "`n==================================" -ForegroundColor Blue
Write-Host "VALIDATION SUMMARY" -ForegroundColor Blue
Write-Host "==================================" -ForegroundColor Blue
Write-Host "Tests Passed: $passed" -ForegroundColor Green
Write-Host "Tests Failed: $failed" -ForegroundColor Red
Write-Host "Total Tests: $($passed + $failed)"

if ($failed -eq 0) {
    Write-Host "`n🎉 ALL TESTS PASSED!" -ForegroundColor Green
    Write-Host "✅ Infrastructure is deployed successfully" -ForegroundColor Green
} else {
    Write-Host "`n⚠️ Some tests failed" -ForegroundColor Yellow
    Write-Host "🔧 Check the details above for issues" -ForegroundColor Yellow
}

Write-Host "`n==================================" -ForegroundColor Blue
Write-Host "USEFUL COMMANDS" -ForegroundColor Blue
Write-Host "==================================" -ForegroundColor Blue
Write-Host "View pods:        kubectl get pods -n $namespace"
Write-Host "View logs:        kubectl logs -f deployment/data-api-gateway -n $namespace"
Write-Host "Port forward:     kubectl port-forward svc/data-api-gateway 8000:8000 -n $namespace"
Write-Host "Delete namespace: kubectl delete namespace $namespace"
Write-Host "==================================" -ForegroundColor Blue