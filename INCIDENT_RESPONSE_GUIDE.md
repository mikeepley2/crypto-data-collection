# 🚨 Data Collection Incident Response Guide

## Overview

This guide provides step-by-step procedures for responding to data collection incidents, based on the October 7, 2025 incident where data collection stopped for 5 days.

## 🚨 **CRITICAL INCIDENT: Data Collection Stopped**

### **Symptoms**
- ML feature processing stops or falls behind
- Health score drops below 80/100
- No recent updates in monitoring logs
- Data age exceeds alert thresholds

### **Immediate Response (0-15 minutes)**

1. **Check System Status**
   ```bash
   # Run health check
   python monitor_ml_features.py
   
   # Check Kubernetes pods
   kubectl get pods -n crypto-data-collection
   
   # Check cronjobs
   kubectl get cronjobs -n crypto-data-collection
   ```

2. **Identify Root Cause**
   ```bash
   # Check materialized updater logs
   kubectl logs materialized-updater-* -n crypto-data-collection --tail=50
   
   # Check price collector logs
   kubectl logs enhanced-crypto-prices-* -n crypto-data-collection --tail=20
   
   # Check health monitor logs
   kubectl logs data-collection-health-monitor-* -n crypto-data-collection --tail=20
   ```

### **Common Root Causes & Fixes**

#### **1. Materialized Updater Date Range Stuck**
**Symptoms**: Processing same old date range repeatedly
**Fix**:
```bash
# Restart materialized updater
kubectl delete pod materialized-updater-* -n crypto-data-collection

# Verify restart
kubectl get pods -n crypto-data-collection | grep materialized-updater
```

#### **2. API Gateway Redis Connection Issues**
**Symptoms**: API Gateway in CrashLoopBackOff
**Fix**:
```bash
# Check Redis status
kubectl exec redis-data-collection-* -n crypto-data-collection -- redis-cli ping

# Check current monitoring services
kubectl get pods -n crypto-data-collection | grep -E "(prometheus|grafana|alertmanager)"
```

#### **3. CronJob Scheduling Issues**
**Symptoms**: CronJobs not executing
**Fix**:
```bash
# Check cronjob status
kubectl get cronjobs -n crypto-data-collection

# Manually trigger if needed
kubectl create job --from=cronjob/enhanced-crypto-prices-collector manual-trigger -n crypto-data-collection
```

#### **4. Database Connection Issues**
**Symptoms**: Connection errors in logs
**Fix**:
```bash
# Test database connection
kubectl exec materialized-updater-* -n crypto-data-collection -- python -c "import mysql.connector; mysql.connector.connect(host='host.docker.internal', user='root', password='password', database='crypto_prices').close(); print('DB OK')"
```

### **Recovery Procedures (15-60 minutes)**

1. **Verify Data Collection Restored**
   ```bash
   # Run monitoring script
   python monitor_ml_features.py
   
   # Check for recent updates
   kubectl logs materialized-updater-* -n crypto-data-collection --tail=20 | grep "Updated materialized table"
   ```

2. **Backfill Missing Data (if needed)**
   ```bash
   # Check data gaps
   python monitor_ml_features.py continuous 5 12
   
   # If gaps exist, the materialized updater will automatically backfill
   # Monitor progress with:
   kubectl logs materialized-updater-* -n crypto-data-collection -f
   ```

3. **Validate System Health**
   ```bash
   # Run comprehensive health check
   python monitor_data_collection_health.py --once
   
   # Verify all services are healthy
   kubectl get pods -n crypto-data-collection
   ```

### **Post-Incident Actions (1-24 hours)**

1. **Document Incident**
   - Record root cause
   - Document resolution steps
   - Update this guide if needed

2. **Implement Prevention Measures**
   - Deploy automated monitoring
   - Set up alerting
   - Review and update procedures

3. **Monitor Recovery**
   - Run continuous monitoring for 24 hours
   - Verify data quality and completeness
   - Check for any residual issues

## 🔧 **Prevention Measures**

### **Automated Monitoring**
```bash
# Deploy health monitoring CronJob
kubectl apply -f k8s/monitoring/data-collection-health-monitor.yaml

# Check monitoring status
kubectl get cronjobs -n crypto-data-collection | grep health-monitor
```

### **Alert Thresholds**
- **Critical**: Health score < 60, data age > 4 hours
- **Warning**: Health score < 80, data age > 2 hours
- **Info**: Health score < 95, data age > 1 hour

### **Regular Health Checks**
```bash
# Daily health check
python monitor_data_collection_health.py --once

# Weekly comprehensive check
python monitor_ml_features.py continuous 5 12
```

## 📊 **Monitoring Commands Reference**

### **Quick Status Checks**
```bash
# Overall system health
python monitor_ml_features.py

# Kubernetes services
kubectl get pods -n crypto-data-collection

# Recent activity
kubectl logs materialized-updater-* -n crypto-data-collection --tail=20

# Data freshness
kubectl exec materialized-updater-* -n crypto-data-collection -- python -c "from datetime import datetime; print(f'Current time: {datetime.now()}')"
```

### **Detailed Diagnostics**
```bash
# Full health check
python monitor_data_collection_health.py --once --alert-threshold 1

# Continuous monitoring
python monitor_data_collection_health.py --check-interval 5

# Service logs
kubectl logs -l app=materialized-updater -n crypto-data-collection --tail=100
kubectl logs -l app=enhanced-crypto-prices -n crypto-data-collection --tail=50
```

## 🚨 **Emergency Contacts & Escalation**

### **Severity Levels**
- **P1 (Critical)**: Data collection completely stopped, health score < 60
- **P2 (High)**: Data collection degraded, health score < 80
- **P3 (Medium)**: Minor issues, health score < 95

### **Response Times**
- **P1**: Immediate response, fix within 1 hour
- **P2**: Response within 4 hours, fix within 24 hours
- **P3**: Response within 24 hours, fix within 72 hours

## 📝 **Incident Log Template**

```
INCIDENT #: [NUMBER]
DATE: [YYYY-MM-DD HH:MM]
SEVERITY: [P1/P2/P3]
STATUS: [OPEN/INVESTIGATING/RESOLVED/CLOSED]

DESCRIPTION:
[Brief description of the incident]

ROOT CAUSE:
[What caused the incident]

RESOLUTION:
[Steps taken to resolve]

PREVENTION:
[Measures to prevent recurrence]

LESSONS LEARNED:
[Key takeaways]
```

---

**Last Updated**: January 15, 2025  
**Version**: 2.0  
**Status**: Active - Updated for current system
