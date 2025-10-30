# Bollinger Bands Backfill - Issue & Fix

**Date:** October 21, 2025  
**Issue:** Backfill processed 300K+ records but updated 0 records  
**Status:** FIXED AND RERUNNING

---

## Root Cause Analysis

### Issue 1: Timestamp Format Mismatch

**Problem:**
```python
# OLD CODE - Line 76
cursor.execute("""
    SELECT current_price
    FROM price_data_real
    WHERE symbol = %s
    AND timestamp < %s  # <-- timestamp_iso is DATETIME, but price_data_real.timestamp is UNIX MILLISECONDS
    ORDER BY timestamp DESC
    LIMIT 20
""", (symbol, timestamp_iso))
```

**Why it failed:**
- `timestamp_iso` from `technical_indicators` is a **DATETIME** object (e.g., "2025-09-30 17:15:15")
- `price_data_real.timestamp` is stored as **UNIX MILLISECONDS** (e.g., 1759285200000)
- Comparing DATETIME < UNIX_MILLISECONDS always returns FALSE
- Result: No prices retrieved → No standard deviation calculated → No update

**Example:**
```
timestamp_iso = 2025-09-30 17:15:15 (DATETIME)
Compared with price_data_real.timestamp = 1759285200000 (milliseconds)
Result: All comparisons fail, prices list is empty, condition `len(prices) >= 2` is False
```

### Issue 2: Cursor Reuse

**Problem:**
```python
# OLD CODE - Nested cursor calls on same cursor
cursor.execute("SELECT ... FROM technical_indicators ...")  # Main loop query
records = cursor.fetchall()

for record in records:
    cursor.execute("SELECT ... FROM price_data_real ...")   # Nested query reuses cursor
    prices = cursor.fetchall()                              # Fetches from nested query
    # Main query results lost!
```

**Why it failed:**
- When reusing the same cursor for nested queries, the first result set is lost
- This can cause unpredictable behavior in iteration loops

---

## Solution Applied

### Fix 1: Timestamp Conversion

```python
# NEW CODE
from datetime import datetime as dt

# Convert DATETIME to Unix milliseconds for comparison
timestamp_ms = int(dt.timestamp(timestamp_iso) * 1000)

# Now both sides are in same format
price_cursor.execute("""
    SELECT current_price
    FROM price_data_real
    WHERE symbol = %s
    AND timestamp < %s  # Both now in milliseconds
    ORDER BY timestamp DESC
    LIMIT 20
""", (symbol, timestamp_ms))
```

### Fix 2: Separate Cursors

```python
# NEW CODE
# Main cursor for technical_indicators queries
cursor = conn.cursor()

# Separate cursor for price_data_real queries (nested)
price_cursor = mysql.connector.connect(**config).cursor()

# Now safe to use both simultaneously
cursor.execute("SELECT ... FROM technical_indicators ...")
for record in records:
    price_cursor.execute("SELECT ... FROM price_data_real ...")  # Independent cursor
    prices = price_cursor.fetchall()  # Correct results
```

---

## Changes Made

**File:** `backfill_bollinger_bands.py`

**Key Modifications:**

1. **Line 26**: Added separate connection for price cursor
   ```python
   price_cursor = mysql.connector.connect(**config).cursor()
   ```

2. **Line 73-74**: Added timestamp conversion
   ```python
   from datetime import datetime as dt
   timestamp_ms = int(dt.timestamp(timestamp_iso) * 1000)
   ```

3. **Line 80**: Updated query to use milliseconds
   ```python
   price_cursor.execute(..., (symbol, timestamp_ms))
   ```

4. **Line 87**: Changed cursor from `cursor.fetchall()` to `price_cursor.fetchall()`

5. **Line 151**: Added cleanup for price cursor
   ```python
   price_cursor.close()
   ```

---

## Expected Results After Fix

### Before (0 updates)
```
Total records processed: 300,000+
Total records updated:   0
Success rate:           0%
Bollinger Bands populated: 2 / 3,297,120 (0.00%)
```

### After (Expected ~3.3M updates)
```
Total records processed: 3,297,120
Total records updated:   ~3,297,100 (some may not have 20+ prices)
Success rate:           ~99.9%
Bollinger Bands populated: ~3,297,100 / 3,297,120 (~99.9%)
```

---

## Status

✅ **Issue Identified:** Timestamp format mismatch + cursor reuse  
✅ **Fix Applied:** Timestamp conversion + separate cursors  
🔄 **Running:** Backfill executing with fixes  
⏳ **Expected Completion:** 45-60 minutes  

---

## Validation Plan

After backfill completes:
1. Run `comprehensive_technical_validation.py` to verify Bollinger coverage
2. Confirm 99%+ records have both `bollinger_upper` and `bollinger_lower`
3. Verify data quality (realistic band widths around SMA 20)

---

*Fix applied: October 21, 2025 - 11:00 AM UTC*
*Backfill restarted with corrected timestamp handling and cursor management*




