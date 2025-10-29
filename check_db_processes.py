#!/usr/bin/env python3
"""
Check database processes and identify lock issues
"""

import mysql.connector
import os
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("db_process_checker")


def get_db_connection():
    try:
        return mysql.connector.connect(
            host=os.getenv("DB_HOST", "127.0.0.1"),
            user=os.getenv("DB_USER", "news_collector"),
            password=os.getenv("DB_PASSWORD", "99Rules!"),
            database=os.getenv("DB_NAME", "crypto_prices"),
        )
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None


def check_database_processes():
    """Check active database processes and identify potential lock issues"""
    logger.info("🔍 Checking database processes...")

    conn = get_db_connection()
    if not conn:
        return

    try:
        cursor = conn.cursor()

        # Get active processes
        logger.info("=== ACTIVE DATABASE PROCESSES ===")
        cursor.execute("SHOW PROCESSLIST")
        processes = cursor.fetchall()

        active_processes = []
        for proc in processes:
            if proc[4] and proc[4] != "Sleep":
                active_processes.append(proc)
                info = proc[7][:100] if proc[7] else "None"
                logger.info(
                    f"ID: {proc[0]}, User: {proc[1]}, Host: {proc[2]}, DB: {proc[3]}, Command: {proc[4]}, Time: {proc[5]}s, State: {proc[6]}"
                )
                logger.info(f"  Query: {info}")

        logger.info(f"Total processes: {len(processes)}")
        logger.info(f"Active processes: {len(active_processes)}")

        # Check for long-running processes
        long_running = [p for p in active_processes if p[5] > 60]  # More than 1 minute
        if long_running:
            logger.warning(f"⚠️  Found {len(long_running)} long-running processes:")
            for proc in long_running:
                logger.warning(f"  ID {proc[0]}: {proc[5]}s - {proc[6]}")

        # Check for lock-related states
        lock_processes = [
            p
            for p in active_processes
            if any(keyword in p[6].lower() for keyword in ["lock", "wait", "deadlock"])
        ]
        if lock_processes:
            logger.error(f"🚨 Found {len(lock_processes)} processes with lock issues:")
            for proc in lock_processes:
                logger.error(f"  ID {proc[0]}: {proc[6]} - {proc[5]}s")

        # Check INNODB status for lock information
        logger.info("\n=== INNODB LOCK INFORMATION ===")
        try:
            cursor.execute("SHOW ENGINE INNODB STATUS")
            status = cursor.fetchone()
            if status and status[2]:
                lines = status[2].split("\n")
                lock_section = False
                for line in lines:
                    if "TRANSACTIONS" in line:
                        lock_section = True
                    elif "FILE I/O" in line:
                        lock_section = False

                    if lock_section and any(
                        keyword in line.lower()
                        for keyword in ["lock", "wait", "trx", "thread"]
                    ):
                        logger.info(line)
        except Exception as e:
            logger.warning(f"Could not get INNODB status: {e}")

        # Check current connections by user
        logger.info("\n=== CONNECTIONS BY USER ===")
        cursor.execute(
            """
            SELECT USER, HOST, COUNT(*) as connection_count
            FROM information_schema.PROCESSLIST 
            WHERE USER IS NOT NULL
            GROUP BY USER, HOST
            ORDER BY connection_count DESC
        """
        )
        connections = cursor.fetchall()
        for conn_info in connections:
            logger.info(
                f"User: {conn_info[0]}, Host: {conn_info[1]}, Connections: {conn_info[2]}"
            )

    except Exception as e:
        logger.error(f"Error checking processes: {e}")
    finally:
        conn.close()


def check_connection_pooling():
    """Check if services are using connection pooling"""
    logger.info("\n🔍 Checking connection pooling configuration...")

    # Check materialized updater logs for connection patterns
    logger.info("Checking materialized updater connection patterns...")

    # Check if we can see connection pool settings in environment
    env_vars = [
        "MYSQL_POOL_SIZE",
        "MYSQL_MAX_CONNECTIONS",
        "DB_POOL_SIZE",
        "CONNECTION_POOL_SIZE",
    ]

    for var in env_vars:
        value = os.getenv(var)
        if value:
            logger.info(f"Found connection pool setting: {var}={value}")
        else:
            logger.info(f"No {var} found")


def main():
    logger.info("🚀 Starting Database Process Analysis")
    logger.info("=" * 60)

    check_database_processes()
    check_connection_pooling()

    logger.info("🎉 Analysis complete!")


if __name__ == "__main__":
    main()
