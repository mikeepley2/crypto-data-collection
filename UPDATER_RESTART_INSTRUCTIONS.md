# Materialized Updater Restart Instructions

## ✅ Fixes Already Applied

The following fixes have been applied to `src/docker/materialized_updater/realtime_materialized_updater.py`:

1. **OHLC Data** - Fixed timestamp column (`timestamp_iso`)
2. **Technical Indicators** - Fixed to use `(symbol, date)` lookup  
3. **Macro Indicators** - Fixed to query `macro_indicators` table correctly
4. **Onchain Data** - Added batch lookup integration

## 🔄 Manual Restart Steps

### Step 1: Check if there's a stuck process

Open a **new** PowerShell window and run:

```powershell
# Kill any stuck Python processes related to the update script
Get-Process python | Where-Object {$_.MainWindowTitle -like "*update*"} | Stop-Process -Force

# Or check what's running
Get-Process python | Select-Object Id, ProcessName, StartTime
```

### Step 2: Restart the Materialized Updater Service

If using Kubernetes:

```powershell
# Check if deployment exists
kubectl get deployment materialized-updater -n crypto-data-collection

# Restart it
kubectl rollout restart deployment/materialized-updater -n crypto-data-collection

# Wait for it to be ready
kubectl rollout status deployment/materialized-updater -n crypto-data-collection --timeout=120s

# Check the pod status
kubectl get pods -n crypto-data-collection -l app=materialized-updater

# View logs
kubectl logs -n crypto-data-collection -l app=materialized-updater --tail=50 -f
```

If running as a local service or Docker container:

```powershell
# Find and restart the container/service
docker ps | findstr materialized
docker restart <container_id>

# Or if it's a Windows service
Get-Service | Where-Object {$_.Name -like "*materialized*"}
Restart-Service <service_name>
```

### Step 3: Verify It's Working

Wait 5-10 minutes after restart, then run:

```powershell
python verify_service_running.py
```

Or check more detailed status:

```powershell
python check_updater_working.py
```

## 📊 What to Look For

After restart, check the logs for:
- ✅ "Starting materialized table update cycle..."
- ✅ "Finished processing for symbol: ..."
- ✅ "Processed X records"
- ❌ Any error messages

The updater will:
- Process new price data automatically
- Backfill missing fields (technical, macro, OHLC, onchain) as new records arrive
- Use the corrected lookup logic we implemented

## ⚠️ Note About Existing Records

The `update_existing_materialized_records.py` script tries to update millions of existing records, which can take hours and may hang. 

**Better approach:** Let the updater service naturally backfill missing fields as new price data arrives. It will use the fixed lookup logic for all new records going forward.

## ✅ Verification

After 10-15 minutes, the updater should be:
- Processing new price records
- Populating technical indicators correctly
- Populating macro indicators correctly  
- Populating OHLC data correctly
- Populating onchain data for supported symbols

Run the verification scripts to confirm.


