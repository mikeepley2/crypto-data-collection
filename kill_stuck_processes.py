#!/usr/bin/env python3
"""
Kill stuck database processes
"""

import os
import mysql.connector


def kill_stuck_processes():
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            user=os.getenv("DB_USER", "news_collector"),
            password=os.getenv("DB_PASSWORD", "99Rules!"),
            database=os.getenv("DB_NAME", "crypto_prices"),
        )

        cursor = conn.cursor()

        print("🔍 KILLING STUCK PROCESSES")
        print("=" * 50)

        # Get stuck processes (running > 1 hour)
        cursor.execute(
            """
            SELECT ID, USER, HOST, DB, COMMAND, TIME, STATE, INFO
            FROM information_schema.PROCESSLIST 
            WHERE TIME > 3600 AND USER = 'news_collector'
            ORDER BY TIME DESC
        """
        )

        stuck_processes = cursor.fetchall()
        print(f"📊 Found {len(stuck_processes)} stuck processes:")

        for proc in stuck_processes:
            proc_id, user, host, db, command, time, state, info = proc
            print(f"  • ID: {proc_id}, Time: {time}s, State: {state}")
            if info:
                print(f"    Query: {info[:100]}...")

        # Kill the stuck processes
        for proc in stuck_processes:
            proc_id = proc[0]
            try:
                cursor.execute(f"KILL {proc_id}")
                print(f"  ✅ Killed process {proc_id}")
            except Exception as e:
                print(f"  ❌ Failed to kill process {proc_id}: {e}")

        # Check remaining processes
        cursor.execute(
            """
            SELECT COUNT(*) 
            FROM information_schema.PROCESSLIST 
            WHERE USER = 'news_collector' AND TIME > 3600
        """
        )

        remaining = cursor.fetchone()[0]
        print(f"\n📊 Remaining stuck processes: {remaining}")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    kill_stuck_processes()
