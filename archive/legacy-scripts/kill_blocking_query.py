#!/usr/bin/env python3
"""Automatically find and kill blocking MySQL queries"""
import mysql.connector
import sys


def kill_blocking_queries():
    """Find and kill long-running queries that are blocking the updater"""
    try:
        conn = mysql.connector.connect(
            host="127.0.0.1",
            user="news_collector",
            password="99Rules!",
            database="crypto_prices",
            connect_timeout=5,
        )

        cursor = conn.cursor(dictionary=True)

        print("=" * 80)
        print("FINDING BLOCKING QUERIES")
        print("=" * 80)
        print()

        # Find long-running queries (running for more than 5 minutes)
        cursor.execute(
            """
            SELECT 
                ID,
                USER,
                HOST,
                DB,
                COMMAND,
                TIME,
                STATE,
                LEFT(INFO, 200) as QUERY_SNIPPET
            FROM information_schema.PROCESSLIST
            WHERE COMMAND != 'Sleep'
            AND TIME > 300
            AND ID != CONNECTION_ID()
            ORDER BY TIME DESC
        """
        )

        blocking_queries = cursor.fetchall()

        if not blocking_queries:
            print("✅ No blocking queries found (queries running > 5 minutes)")
            print()

            # Check for any queries running for more than 1 minute
            cursor.execute(
                """
                SELECT 
                    ID,
                    USER,
                    HOST,
                    DB,
                    COMMAND,
                    TIME,
                    STATE,
                    LEFT(INFO, 200) as QUERY_SNIPPET
                FROM information_schema.PROCESSLIST
                WHERE COMMAND != 'Sleep'
                AND TIME > 60
                AND ID != CONNECTION_ID()
                ORDER BY TIME DESC
            """
            )

            recent_queries = cursor.fetchall()
            if recent_queries:
                print("⚠️  Found queries running > 1 minute (may not be blocking):")
                for q in recent_queries:
                    print(
                        f"   ID: {q['ID']}, Time: {q['TIME']}s, Query: {q['QUERY_SNIPPET']}"
                    )
            else:
                print("✅ No queries running > 1 minute found")

            conn.close()
            return

        print(f"⚠️  Found {len(blocking_queries)} blocking query/ies:")
        print()

        for q in blocking_queries:
            print(f"Query ID: {q['ID']}")
            print(f"  User: {q['USER']}")
            print(f"  Database: {q['DB']}")
            print(f"  Running for: {q['TIME']} seconds ({q['TIME']/60:.1f} minutes)")
            print(f"  State: {q['STATE']}")
            print(f"  Query snippet: {q['QUERY_SNIPPET']}")
            print()

        # Ask for confirmation before killing
        print("=" * 80)
        print("⚠️  WARNING: Killing these queries may cause data inconsistency!")
        print("=" * 80)
        print()

        response = input("Kill these queries? (yes/no): ").strip().lower()

        if response != "yes":
            print("Cancelled. No queries were killed.")
            conn.close()
            return

        # Kill each blocking query
        killed_count = 0
        for q in blocking_queries:
            try:
                kill_cursor = conn.cursor()
                kill_cursor.execute(f"KILL {q['ID']}")
                kill_cursor.close()
                print(f"✅ Killed query ID {q['ID']}")
                killed_count += 1
            except Exception as e:
                print(f"❌ Failed to kill query ID {q['ID']}: {e}")

        conn.close()

        print()
        print("=" * 80)
        print(f"✅ Killed {killed_count} blocking query/ies")
        print("=" * 80)
        print()
        print("Next steps:")
        print("1. Restart the materialized updater:")
        print(
            "   kubectl rollout restart deployment/materialized-updater -n crypto-data-collection"
        )
        print()
        print("2. Monitor logs to verify it's processing:")
        print(
            "   kubectl logs -n crypto-data-collection -l app=materialized-updater -f"
        )
        print()

    except Exception as e:
        print(f"❌ Error: {e}")
        print()
        print("Make sure MySQL is running and accessible")
        sys.exit(1)


if __name__ == "__main__":
    kill_blocking_queries()

