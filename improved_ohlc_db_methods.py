
# Improved Database Methods for OHLC Collector
# Add these methods to replace existing database operations

import mysql.connector
from mysql.connector import pooling
import time
import logging
from typing import List, Dict, Any

class ImprovedOHLCCollector:
    """Enhanced OHLC Collector with connection pooling and deadlock prevention"""
    
    def __init__(self):
        # Connection pool configuration
        self.pool_config = {
            'pool_name': 'ohlc_pool',
            'pool_size': 10,
            'pool_reset_session': True,
            'host': 'host.docker.internal',
            'user': 'news_collector', 
            'password': '99Rules!',
            'database': 'crypto_prices',
            'autocommit': False,  # Explicit transaction control
            'charset': 'utf8mb4',
            'use_unicode': True,
            'sql_mode': 'STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO',
            'isolation_level': 'READ COMMITTED'
        }
        
        try:
            # Create connection pool
            self.pool = pooling.MySQLConnectionPool(**self.pool_config)
            logging.info("✅ Database connection pool created successfully")
        except mysql.connector.Error as e:
            logging.error(f"❌ Failed to create connection pool: {e}")
            raise
    
    def get_connection_with_retry(self, max_retries=3):
        """Get connection from pool with retry logic"""
        for attempt in range(max_retries):
            try:
                return self.pool.get_connection()
            except mysql.connector.PoolError as e:
                if attempt == max_retries - 1:
                    raise
                time.sleep(0.1 * (2 ** attempt))
        return None
    
    def _store_ohlc_batch_with_retry(self, batch_data: List[Dict]) -> int:
        """Store OHLC data with deadlock retry and optimized batching"""
        
        if not batch_data:
            return 0
            
        max_retries = 3
        retry_delay = 0.1
        
        for attempt in range(max_retries):
            conn = None
            cursor = None
            
            try:
                # Get connection from pool
                conn = self.get_connection_with_retry()
                cursor = conn.cursor()
                
                # Start transaction with proper isolation
                conn.start_transaction(isolation_level='READ COMMITTED')
                
                # Sort by symbol to prevent deadlocks (consistent lock ordering)
                batch_data.sort(key=lambda x: (x['symbol'], x['timestamp_unix']))
                
                insert_sql = """
                    INSERT INTO ohlc_data
                    (symbol, coin_id, timestamp_unix, timestamp_iso,
                     open_price, high_price, low_price, close_price, 
                     volume, data_source, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        open_price = VALUES(open_price),
                        high_price = VALUES(high_price),
                        low_price = VALUES(low_price),
                        close_price = VALUES(close_price),
                        volume = VALUES(volume),
                        data_source = VALUES(data_source)
                """
                
                # Prepare batch data
                values = []
                for record in batch_data:
                    values.append((
                        record['symbol'],
                        record['coin_id'],
                        record['timestamp_unix'],
                        record['timestamp_iso'],
                        record['open_price'],
                        record['high_price'],
                        record['low_price'],
                        record['close_price'],
                        record.get('volume'),  # May be None
                        record['data_source'],
                        record['created_at']
                    ))
                
                # Execute batch insert
                cursor.executemany(insert_sql, values)
                
                # Commit transaction
                conn.commit()
                
                records_inserted = cursor.rowcount
                logging.info(f"✅ Batch stored: {records_inserted} records for {len(set(r['symbol'] for r in batch_data))} symbols")
                
                return records_inserted
                
            except mysql.connector.Error as e:
                # Rollback on any error
                if conn:
                    try:
                        conn.rollback()
                    except:
                        pass
                
                if e.errno == 1213:  # Deadlock detected
                    logging.warning(f"⚠️  Deadlock detected (attempt {attempt + 1}/{max_retries})")
                    if attempt < max_retries - 1:
                        # Exponential backoff with jitter
                        delay = retry_delay * (2 ** attempt) + (0.05 * attempt)
                        time.sleep(delay)
                        continue
                    else:
                        logging.error(f"❌ Max retries exceeded for deadlock")
                        raise
                elif e.errno == 1205:  # Lock wait timeout
                    logging.warning(f"⚠️  Lock timeout detected (attempt {attempt + 1}/{max_retries})")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay * (2 ** attempt))
                        continue
                    else:
                        raise
                else:
                    logging.error(f"❌ Database error: {e}")
                    raise
                    
            except Exception as e:
                if conn:
                    try:
                        conn.rollback()
                    except:
                        pass
                logging.error(f"❌ Unexpected error: {e}")
                raise
                
            finally:
                # Clean up resources
                if cursor:
                    try:
                        cursor.close()
                    except:
                        pass
                if conn:
                    try:
                        conn.close()  # Return connection to pool
                    except:
                        pass
        
        return 0
    
    def _load_database_mappings_pooled(self):
        """Load symbol mappings using connection pool"""
        conn = None
        try:
            conn = self.get_connection_with_retry()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT symbol, coingecko_id, name
                FROM crypto_assets 
                WHERE coingecko_id IS NOT NULL
                ORDER BY symbol
            """)
            
            db_mappings = {}
            for symbol, coingecko_id, name in cursor.fetchall():
                if symbol and coingecko_id:
                    db_mappings[symbol] = coingecko_id
            
            cursor.close()
            logging.info(f"✅ Loaded {len(db_mappings)} symbol mappings from database")
            return db_mappings
            
        except mysql.connector.Error as e:
            logging.error(f"❌ Error loading database mappings: {e}")
            return {}
        finally:
            if conn:
                conn.close()
    
    def get_existing_ohlc_symbols_pooled(self, days_back: int = 7) -> set:
        """Get symbols with recent OHLC data using connection pool"""
        conn = None
        try:
            conn = self.get_connection_with_retry()
            cursor = conn.cursor()
            
            # Improved query without the problematic premium filter
            cursor.execute("""
                SELECT DISTINCT symbol
                FROM ohlc_data
                WHERE timestamp_iso >= DATE_SUB(NOW(), INTERVAL %s DAY)
                ORDER BY symbol
            """, (days_back,))
            
            existing_symbols = set(row[0] for row in cursor.fetchall())
            cursor.close()
            
            logging.info(f"📈 Found {len(existing_symbols)} symbols with recent OHLC data")
            return existing_symbols
            
        except mysql.connector.Error as e:
            logging.error(f"❌ Error getting existing OHLC symbols: {e}")
            return set()
        finally:
            if conn:
                conn.close()
    
    def __del__(self):
        """Clean up connection pool on destruction"""
        if hasattr(self, 'pool'):
            try:
                # Note: MySQLConnectionPool doesn't have a close method
                # Connections will be cleaned up automatically
                pass
            except:
                pass
