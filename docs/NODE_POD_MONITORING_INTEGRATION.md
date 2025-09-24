# Node/Pod Health Monitoring Integration Guide
# =============================================

## Overview
This document outlines how node and pod health monitoring integrates with our dedicated Analytics/Observability solution rather than using standalone monitoring scripts.

## Architecture Decision
✅ **CORRECT**: Use Analytics Node for infrastructure monitoring
❌ **AVOID**: Local scripts for node/pod health monitoring

## Integration Points

### 1. Analytics Node Setup
The Analytics Node contains:
- **Grafana**: Visual dashboards for infrastructure metrics
- **Prometheus**: Metrics collection and storage
- **Alertmanager**: Alert routing and notification
- **Elasticsearch/Kibana**: Log aggregation and analysis

### 2. Data Collection Node Role
The Data Collection Node should:
- **Export metrics** to Analytics Node Prometheus
- **Send logs** to Analytics Node Elasticsearch
- **Respond to health checks** from monitoring systems
- **Configure service-level monitoring** (application health)

### 3. Service Integration

#### Add Prometheus Metrics to All Services
```python
# Add to each service's main.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest

# Export metrics endpoint
@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

#### Configure Pod Annotations for Scraping
```yaml
# Add to deployment templates
metadata:
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/path: "/metrics"
    prometheus.io/port: "8000"
```

#### Enable Structured Logging
```python
# Use structured JSON logging for Elasticsearch ingestion
import logging
import json

class StructuredLogger:
    def info(self, message: str, **context):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": "INFO", 
            "service": self.service_name,
            "message": message,
            "context": context
        }
        logging.info(json.dumps(log_entry))
```

## Quick Access Guide

### For Node Health Monitoring:
```bash
# Instead of local kubectl commands, use:
# 1. Access Analytics Node Grafana: http://analytics-node:3000
# 2. Open "Kubernetes Infrastructure" dashboard
# 3. View real-time node CPU, memory, disk, network metrics
```

### For Pod Health Monitoring:
```bash
# Instead of local scripts, use:
# 1. Analytics Node → Grafana → "Pod Health Overview" 
# 2. View pod status, restarts, resource usage
# 3. Set up alerts for pod failures
```

### For Service Logs:
```bash
# Instead of kubectl logs, use:
# 1. Analytics Node → Kibana → "Crypto Data Collection" index
# 2. Search, filter, and analyze structured logs
# 3. Create log-based alerts and dashboards
```

## Migration Checklist

### Phase 1: Enable Metrics Export
- [ ] Add /metrics endpoint to all services
- [ ] Configure Prometheus scraping annotations
- [ ] Verify metrics collection in Analytics Node

### Phase 2: Structured Logging
- [ ] Convert all services to JSON logging
- [ ] Configure log forwarding to Analytics Node
- [ ] Create Kibana index patterns and dashboards

### Phase 3: Dashboard Integration
- [ ] Import infrastructure dashboards to Analytics Node
- [ ] Configure service-specific dashboards
- [ ] Set up alerting rules and notification channels

### Phase 4: Remove Local Scripts
- [ ] Deprecate standalone monitoring scripts
- [ ] Update documentation to reference Analytics Node
- [ ] Train team on new monitoring workflows

## Emergency Procedures

### When Analytics Node is Unavailable:
```bash
# Temporary local commands (emergency only):
kubectl get nodes                    # Node status
kubectl top nodes                   # Node resources  
kubectl get pods -A                 # All pod status
kubectl describe node <node-name>   # Node details
```

### Service-Level Health Checks (Always Local):
```bash
# These remain on Data Collection Node:
curl http://service:8000/health     # Service health
./scripts/health-check.sh           # Service status
./scripts/service-manager.sh        # Service operations
```

## Documentation Updates

### README.md Changes:
- [x] Redirect infrastructure monitoring to Analytics Node
- [x] Clarify service vs infrastructure monitoring separation
- [x] Add Analytics Node dashboard access instructions

### Service Documentation:
- [x] Update best practices to reference Analytics Node
- [x] Remove references to local monitoring scripts
- [x] Add integration requirements for new services

## Benefits of This Approach

1. **Centralized Monitoring**: Single source of truth for all metrics
2. **Scalability**: Analytics Node designed for monitoring workloads
3. **Advanced Features**: Grafana alerting, Kibana analysis, etc.
4. **Reduced Complexity**: No duplicate monitoring systems
5. **Better Visibility**: Cross-service correlation and analysis
6. **Proper Architecture**: Separation of concerns between nodes

## Implementation Timeline

- **Week 1**: Enable metrics export on all services
- **Week 2**: Configure Analytics Node dashboards
- **Week 3**: Set up alerting and log forwarding  
- **Week 4**: Deprecate local monitoring scripts
- **Ongoing**: Monitor and improve observability stack