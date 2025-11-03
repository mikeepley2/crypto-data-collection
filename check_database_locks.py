#!/usr/bin/env python3
"""Check for database locks that might be blocking the updater"""
import mysql.connector

conn = mysql.connector.connect(
    host="127.0.0.1",
    user="news_collector",
    password="99Rules!",
    database="crypto_prices",
)

cursor = conn.cursor(dictionary=True)

print("=" * 80)
print("DATABASE LOCKS CHECK")
print("=" * 80)
print()

# Check for locks (try different MySQL versions)
try:
    # Try MySQL 8.0+ approach with performance_schema
    cursor.execute(
        """
        SELECT 
            r.trx_id waiting_trx_id,
            r.trx_mysql_thread_id waiting_thread,
            TIMESTAMPDIFF(SECOND, r.trx_wait_started, NOW()) wait_time_sec,
            r.trx_query waiting_query,
            b.trx_id blocking_trx_id,
            b.trx_mysql_thread_id blocking_thread,
            b.trx_query blocking_query
        FROM performance_schema.data_lock_waits w
        INNER JOIN information_schema.innodb_trx b ON b.trx_id = w.blocking_engine_transaction_id
        INNER JOIN information_schema.innodb_trx r ON r.trx_id = w.requesting_engine_transaction_id
        ORDER BY wait_time_sec DESC
        LIMIT 10
    """
    )
except:
    # Fallback: just check long-running transactions
    cursor.execute("SELECT 1")
    locks = []

locks = cursor.fetchall()

if locks:
    print(f"⚠️  Found {len(locks)} active lock(s):")
    print()
    for lock in locks:
        print(f"Waiting Transaction: {lock['waiting_trx_id']}")
        print(f"  Thread: {lock['waiting_thread']}")
        print(f"  Wait time: {lock['wait_time_sec']} seconds")
        print(
            f"  Waiting query: {lock['waiting_query'][:100] if lock['waiting_query'] else 'N/A'}..."
        )
        print(f"Blocking Transaction: {lock['blocking_trx_id']}")
        print(f"  Thread: {lock['blocking_thread']}")
        print(
            f"  Blocking query: {lock['blocking_query'][:100] if lock['blocking_query'] else 'N/A'}..."
        )
        print(f"  Locked table: {lock['lock_table']}")
        print("-" * 80)
else:
    print("✅ No active locks found")
    print()

# Check for long-running transactions
cursor.execute(
    """
    SELECT 
        trx_id,
        trx_mysql_thread_id,
        trx_started,
        TIMESTAMPDIFF(SECOND, trx_started, NOW()) as duration_sec,
        trx_query,
        trx_state
    FROM information_schema.innodb_trx
    ORDER BY duration_sec DESC
    LIMIT 10
"""
)

trx = cursor.fetchall()

if trx:
    print(f"\n📊 Long-running transactions:")
    print("-" * 80)
    for t in trx:
        print(f"Transaction: {t['trx_id']}")
        print(f"  Thread: {t['trx_mysql_thread_id']}")
        print(f"  Started: {t['trx_started']}")
        print(
            f"  Duration: {t['duration_sec']} seconds ({t['duration_sec']/60:.1f} minutes)"
        )
        print(f"  State: {t['trx_state']}")
        print(f"  Query: {t['trx_query'][:100] if t['trx_query'] else 'N/A'}...")
        print("-" * 80)

conn.close()

print()
print("=" * 80)
print("To kill blocking transactions:")
print("KILL <thread_id>;")
print("=" * 80)
