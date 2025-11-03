# Fix Database Lock Blocking Updater

## Problem
The updater is stuck on symbol **AAVE** with repeated lock timeout errors, blocking all processing.

## Solution

Connect to MySQL and run:

```sql
-- Find long-running queries
SELECT 
    ID,
    USER,
    HOST,
    DB,
    COMMAND,
    TIME,
    STATE,
    LEFT(INFO, 100) as QUERY_SNIPPET
FROM information_schema.PROCESSLIST
WHERE COMMAND != 'Sleep'
AND TIME > 60
ORDER BY TIME DESC;
```

Look for queries that have been running for hours. Then kill them:

```sql
KILL <ID>;
```

After killing the blocking query, restart the updater:

```bash
kubectl rollout restart deployment/materialized-updater -n crypto-data-collection
```

## Why This Works

The updater code already handles updating existing records with NULLs:
- Lines 1064-1078: Updates technical indicators if NULL in existing records
- Lines 1086-1123: Updates macro indicators if NULL in existing records  
- Lines 1269-1293: Updates onchain data if NULL in existing records
- Line 1295: Processes updates when `need_update` is True

It just needs to process records, which it can't do while blocked by the lock on AAVE.


