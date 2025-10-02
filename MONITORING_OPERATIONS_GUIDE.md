# 🚀 **CONTINUOUS COLLECTION MONITORING SYSTEM - OPERATIONS GUIDE**

## 📋 **System Overview**
Your crypto data collection system now has **continuous automated monitoring** with intelligent auto-resolution capabilities.

## 🎯 **What the Monitor Does**

### **Real-Time Monitoring**
- ✅ Checks all 7 collection services every 30 seconds
- ✅ Monitors pod health, service health, and data collection rates
- ✅ Tracks database connectivity and recent data collection

### **Automatic Issue Resolution**
- 🔧 **Pod failures**: Automatically restarts failed deployments
- 🔧 **Health check failures**: Triggers manual collections and restarts if needed
- 🔧 **No recent data**: Triggers collections to resume data flow
- 🔧 **Service issues**: Intelligent escalation (trigger → restart → alert)

### **Monitored Services**
1. **enhanced-crypto-prices** - Crypto price data (every 5 min)
2. **crypto-news-collector** - Crypto news (every 20 min) 
3. **stock-news-collector** - Stock news (every 15 min)
4. **technical-indicators** - Technical analysis (every 10 min)
5. **macro-economic** - Economic data (every 4 hours)
6. **social-other** - Social media data (every 30 min)
7. **onchain-data-collector** - Blockchain metrics (every 30 min)

## 🛠️ **Operations Commands**

### **Check Current Status** (Quick Snapshot)
```bash
E:/git/crypto-data-collection/venv/Scripts/python.exe quick_status_check.py
```

### **Start Continuous Monitoring** (Runs Forever)
```bash
E:/git/crypto-data-collection/venv/Scripts/python.exe simple_collection_monitor.py
```

### **Stop Monitoring**
Press `Ctrl+C` in the monitoring terminal

## 📊 **Reading the Dashboard**

### **Status Indicators**
- **OK**: Service is healthy and working properly
- **FAIL**: Service has critical issues (pod down, health failing)
- **LOW**: Service is running but not collecting data recently

### **Dashboard Layout**
```
SERVICE                  | STATUS | HEALTH | RECORDS/1H | ISSUES
enhanced-crypto-prices   | OK     | OK     | OK 245     | None
crypto-news-collector    | OK     | OK     | LOW 0      | No recent data (Auto-resolved)
```

## 🚨 **Issue Types and Auto-Resolution**

### **Automatic Fixes Applied**
1. **"Pod not running"** → Restarts the deployment
2. **"Health check failing"** → Triggers collection, then restarts if needed
3. **"No recent data"** → Triggers manual collection
4. **"Data is stale"** → Triggers fresh collection

### **Protection Mechanisms**
- ⏱️ **Rate limiting**: Won't restart services more than once per 5 minutes
- 🔢 **Retry limits**: Maximum 3 auto-resolution attempts per service
- 📝 **Logging**: All actions logged to `collection_monitor.log`

## 💡 **What to Watch For**

### **Good Signs** ✅
- Most services showing "OK" status
- Records/1H showing positive numbers
- "Auto-resolved" appearing in issues column
- Steady cycle count increasing

### **Concerning Signs** ⚠️
- Multiple services with "FAIL" status
- Persistent "No recent data" without auto-resolution
- Services repeatedly restarting
- Database connection errors

## 🔧 **Manual Interventions**

### **If Auto-Resolution Fails**
1. Check the service logs:
   ```bash
   kubectl logs [pod-name] -n crypto-collectors --tail=50
   ```

2. Check collector manager logs:
   ```bash
   kubectl logs collector-manager-[pod-id] -n crypto-collectors --tail=50
   ```

3. Manual service restart:
   ```bash
   kubectl rollout restart deployment/[service-name] -n crypto-collectors
   ```

### **Database Issues**
If database connectivity fails:
```bash
# Check database connectivity from a pod
kubectl exec -it [any-pod] -n crypto-collectors -- curl -s host.docker.internal:3306
```

## 📈 **Expected Behavior**

### **Normal Operations**
- Monitor cycles every 30 seconds
- Occasional auto-resolutions are NORMAL
- Data collection rates vary by service interval
- Some services (macro-economic) collect infrequently (4 hours)

### **Success Metrics**
- 6/7 or 7/7 services healthy most of the time
- Auto-resolution count increasing (shows it's working)
- Recent data showing for most services
- Stable pod status across cycles

## 🏃‍♂️ **Quick Start for Daily Operations**

1. **Morning Check**:
   ```bash
   python quick_status_check.py
   ```

2. **Start Monitoring** (leave running):
   ```bash
   python simple_collection_monitor.py
   ```

3. **End of Day**: Check `collection_monitor.log` for any recurring issues

## 📞 **Emergency Procedures**

### **System Down**
If everything is failing:
1. Check Kubernetes cluster health
2. Restart collector manager: `kubectl rollout restart deployment/collector-manager -n crypto-collectors`
3. Wait 2 minutes and run status check

### **Data Collection Stopped**
If no services are collecting:
1. Check database connectivity
2. Verify collector manager is running
3. Check ConfigMap is properly mounted
4. Restart collector manager if needed

---

**🎉 Your collection system is now self-monitoring and self-healing!**

The monitor will automatically detect and resolve most common issues, keeping your data collection running smoothly 24/7. Just check the status periodically and let the automation handle the rest!