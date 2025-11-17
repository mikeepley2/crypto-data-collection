#!/usr/bin/env python3
"""
Enhanced Database Manager for Trading System

This module automatically detects the environment (LOCAL or AWS) and provides
unified database access for all services. It replaces direct boto3/pymysql calls
with environment-aware database connections.
"""

import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Unified database manager that works in both local and AWS environments."""
    
    def __init__(self):
        self.local_mode = self._detect_local_mode()
        self._dynamodb = None
        self._mysql = None
        self._redis = None
        self._s3 = None
        self._setup_connections()
    
    def _detect_local_mode(self) -> bool:
        """Detect if we're running in local development mode."""
        return (
            os.environ.get('LOCAL_MODE', '').lower() in ['true', '1', 'yes'] or
            os.environ.get('ENVIRONMENT', '').lower() == 'local' or
            os.path.exists('docker-compose.local.yml')
        )
    
    def _setup_connections(self):
        """Setup database connections based on environment."""
        if self.local_mode:
            logger.info("🔧 Setting up LOCAL database connections")
            self._setup_local_connections()
        else:
            logger.info("☁️ Setting up AWS database connections")
            self._setup_aws_connections()
    
    def _setup_local_connections(self):
        """Setup local database connections."""
        try:
            # DynamoDB Local
            try:
                import boto3
                self._dynamodb = boto3.resource(
                    'dynamodb',
                    endpoint_url='http://localhost:8000',
                    region_name='us-west-2',
                    aws_access_key_id='local',
                    aws_secret_access_key='local'
                )
                logger.info("✅ Connected to local DynamoDB")
            except ImportError:
                logger.warning("boto3 not available, using mock DynamoDB")
                self._dynamodb = self._get_mock_dynamodb()
            
            # MySQL Local
            try:
                import pymysql
                from sqlalchemy import create_engine
                mysql_url = "mysql+pymysql://admin:99Rules!@localhost:3306/trading_db"
                self._mysql = create_engine(mysql_url, pool_pre_ping=True)
                logger.info("✅ Connected to local MySQL")
            except ImportError:
                logger.warning("MySQL dependencies not available")
                self._mysql = None
            
            # Redis Local
            try:
                import redis
                self._redis = redis.Redis(host='localhost', port=6379, db=0)
                logger.info("✅ Connected to local Redis")
            except ImportError:
                logger.warning("Redis not available")
                self._redis = None
            
            # MinIO (S3 Local)
            try:
                import boto3
                self._s3 = boto3.client(
                    's3',
                    endpoint_url='http://localhost:9000',
                    aws_access_key_id='minioadmin',
                    aws_secret_access_key='minioadmin'
                )
                logger.info("✅ Connected to local MinIO")
            except ImportError:
                logger.warning("boto3 not available for MinIO")
                self._s3 = None
                
        except Exception as e:
            logger.error(f"❌ Failed to setup local connections: {e}")
    
    def _setup_aws_connections(self):
        """Setup AWS database connections."""
        try:
            import boto3
            
            # DynamoDB AWS
            self._dynamodb = boto3.resource(
                'dynamodb',
                region_name=os.environ.get('AWS_REGION', 'us-west-2')
            )
            
            # S3 AWS
            self._s3 = boto3.client(
                's3',
                region_name=os.environ.get('AWS_REGION', 'us-west-2')
            )
            
            # MySQL Aurora
            if os.environ.get('AURORA_ENDPOINT'):
                from sqlalchemy import create_engine
                aurora_url = (
                    f"mysql+pymysql://{os.environ.get('AURORA_USERNAME', 'admin')}:"
                    f"{os.environ.get('AURORA_PASSWORD')}@"
                    f"{os.environ.get('AURORA_ENDPOINT')}:3306/"
                    f"{os.environ.get('AURORA_DATABASE', 'trading_db')}"
                )
                self._mysql = create_engine(aurora_url, pool_pre_ping=True)
            
            # Redis AWS
            if os.environ.get('REDIS_ENDPOINT'):
                import redis
                self._redis = redis.Redis(
                    host=os.environ.get('REDIS_ENDPOINT'),
                    port=6379,
                    password=os.environ.get('REDIS_PASSWORD')
                )
            
            logger.info("✅ Connected to AWS services")
            
        except Exception as e:
            logger.error(f"❌ Failed to setup AWS connections: {e}")
    
    def _get_mock_dynamodb(self):
        """Get mock DynamoDB when boto3 is not available."""
        try:
            import sys
            import os
            
            # Add the sentiment plugin path to access MockDynamoTable
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'plugins', 'sentiment'))
            from mock_dynamo import MockDynamoResource
            
            return MockDynamoResource()
        except ImportError:
            logger.error("Mock DynamoDB not available")
            return None
    
    def get_dynamodb_table(self, table_name: str):
        """Get DynamoDB table with environment-appropriate configuration."""
        if self._dynamodb is None:
            logger.error("DynamoDB not available")
            return None
        
        # Add prefix for local mode
        if self.local_mode:
            prefixed_name = f"local_{table_name}"
        else:
            prefixed_name = table_name
        
        return self._dynamodb.Table(prefixed_name)
    
    def get_mysql_session(self):
        """Get MySQL session."""
        if self._mysql is None:
            logger.warning("MySQL not available")
            return None
        
        from sqlalchemy.orm import sessionmaker
        Session = sessionmaker(bind=self._mysql)
        return Session()
    
    def get_redis_client(self):
        """Get Redis client."""
        return self._redis
    
    def get_s3_client(self):
        """Get S3/MinIO client."""
        return self._s3
    
    def execute_sql(self, query: str, params: Optional[Dict] = None) -> List[Dict]:
        """Execute SQL query and return results."""
        if self._mysql is None:
            logger.warning("MySQL not available for query execution")
            return []
        
        try:
            with self._mysql.connect() as conn:
                result = conn.execute(query, params or {})
                return [dict(row) for row in result.fetchall()]
        except Exception as e:
            logger.error(f"SQL execution failed: {e}")
            return []
    
    def store_trade_data(self, trade_data: Dict[str, Any]) -> bool:
        """Store trade data in appropriate database."""
        try:
            # Store in DynamoDB
            table = self.get_dynamodb_table('trading_trades')
            if table:
                table.put_item(Item=trade_data)
            
            # Also store in MySQL if available
            if self._mysql:
                sql = """
                INSERT INTO trades (trade_id, coin, action, amount, price, total_value, 
                                  status, ml_confidence, llm_reasoning, created_at)
                VALUES (%(trade_id)s, %(coin)s, %(action)s, %(amount)s, %(price)s, 
                        %(total_value)s, %(status)s, %(ml_confidence)s, %(llm_reasoning)s, NOW())
                ON DUPLICATE KEY UPDATE
                status = VALUES(status), completed_at = NOW()
                """
                with self._mysql.connect() as conn:
                    conn.execute(sql, trade_data)
            
            logger.info(f"✅ Trade data stored: {trade_data.get('trade_id')}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to store trade data: {e}")
            return False
    
    def get_portfolio_data(self) -> List[Dict[str, Any]]:
        """Get current portfolio data."""
        try:
            # Try MySQL first
            if self._mysql:
                sql = """
                SELECT coin, amount, entry_price, current_price, 
                       (amount * current_price) as current_value,
                       ((current_price - entry_price) / entry_price * 100) as pnl_percent
                FROM portfolio 
                WHERE amount > 0
                ORDER BY current_value DESC
                """
                return self.execute_sql(sql)
            
            # Fallback to DynamoDB
            # This would require a different query structure
            logger.warning("Portfolio data query fallback to DynamoDB not implemented")
            return []
            
        except Exception as e:
            logger.error(f"❌ Failed to get portfolio data: {e}")
            return []
    
    def store_ml_prediction(self, prediction_data: Dict[str, Any]) -> bool:
        """Store ML prediction data."""
        try:
            table = self.get_dynamodb_table('ml_predictions')
            if table:
                prediction_data['timestamp'] = datetime.now(timezone.utc).isoformat()
                table.put_item(Item=prediction_data)
                logger.info(f"✅ ML prediction stored: {prediction_data.get('coin')}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Failed to store ML prediction: {e}")
            return False
    
    def store_sentiment_data(self, sentiment_data: Dict[str, Any]) -> bool:
        """Store sentiment analysis data."""
        try:
            table = self.get_dynamodb_table('sentiment_data')
            if table:
                sentiment_data['timestamp'] = datetime.now(timezone.utc).isoformat()
                table.put_item(Item=sentiment_data)
                logger.info(f"✅ Sentiment data stored")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Failed to store sentiment data: {e}")
            return False
    
    def cache_set(self, key: str, value: str, expire: int = 3600) -> bool:
        """Set cache value with expiration."""
        try:
            if self._redis:
                self._redis.setex(key, expire, value)
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Cache set failed: {e}")
            return False
    
    def cache_get(self, key: str) -> Optional[str]:
        """Get cache value."""
        try:
            if self._redis:
                return self._redis.get(key)
            return None
        except Exception as e:
            logger.error(f"❌ Cache get failed: {e}")
            return None
    
    def health_check(self) -> Dict[str, bool]:
        """Check health of all database connections."""
        health = {}
        
        # DynamoDB health
        try:
            if self._dynamodb:
                # Try to list tables or perform a simple operation
                if hasattr(self._dynamodb, 'meta'):
                    self._dynamodb.meta.client.list_tables()
                health['dynamodb'] = True
            else:
                health['dynamodb'] = False
        except Exception:
            health['dynamodb'] = False
        
        # MySQL health
        try:
            if self._mysql:
                with self._mysql.connect() as conn:
                    conn.execute("SELECT 1")
                health['mysql'] = True
            else:
                health['mysql'] = False
        except Exception:
            health['mysql'] = False
        
        # Redis health
        try:
            if self._redis:
                self._redis.ping()
                health['redis'] = True
            else:
                health['redis'] = False
        except Exception:
            health['redis'] = False
        
        # S3 health
        try:
            if self._s3:
                self._s3.list_buckets()
                health['s3'] = True
            else:
                health['s3'] = False
        except Exception:
            health['s3'] = False
        
        return health


# Global database manager instance
_db_manager = None

def get_db_manager() -> DatabaseManager:
    """Get the global database manager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


# Convenience functions for common operations
def get_dynamodb_table(table_name: str):
    """Get DynamoDB table configured for current environment."""
    return get_db_manager().get_dynamodb_table(table_name)


def get_mysql_session():
    """Get MySQL session configured for current environment."""
    return get_db_manager().get_mysql_session()


def get_redis_client():
    """Get Redis client configured for current environment."""
    return get_db_manager().get_redis_client()


def get_s3_client():
    """Get S3/MinIO client configured for current environment."""
    return get_db_manager().get_s3_client()


def is_local_mode() -> bool:
    """Check if running in local development mode."""
    return get_db_manager().local_mode


def store_trade(trade_data: Dict[str, Any]) -> bool:
    """Store trade data in the appropriate database."""
    return get_db_manager().store_trade_data(trade_data)


def get_portfolio() -> List[Dict[str, Any]]:
    """Get current portfolio data."""
    return get_db_manager().get_portfolio_data()


def store_ml_prediction(prediction_data: Dict[str, Any]) -> bool:
    """Store ML prediction data."""
    return get_db_manager().store_ml_prediction(prediction_data)


def store_sentiment(sentiment_data: Dict[str, Any]) -> bool:
    """Store sentiment analysis data."""
    return get_db_manager().store_sentiment_data(sentiment_data)


def cache_set(key: str, value: str, expire: int = 3600) -> bool:
    """Set cache value."""
    return get_db_manager().cache_set(key, value, expire)


def cache_get(key: str) -> Optional[str]:
    """Get cache value."""
    return get_db_manager().cache_get(key)


def database_health() -> Dict[str, bool]:
    """Get database health status."""
    return get_db_manager().health_check()


# Example usage for services
if __name__ == "__main__":
    # Test the database manager
    db = get_db_manager()
    
    print(f"🚀 Database Manager Test")
    print(f"Mode: {'LOCAL' if db.local_mode else 'AWS'}")
    
    # Test health check
    health = db.health_check()
    print("\n📊 Database Health:")
    for service, status in health.items():
        status_str = "✅ OK" if status else "❌ FAILED"
        print(f"  {service:12}: {status_str}")
    
    # Test operations
    print("\n🧪 Testing Operations:")
    
    # Test cache
    if cache_set("test_key", "test_value"):
        cached_value = cache_get("test_key")
        print(f"  Cache: ✅ Set/Get works (value: {cached_value})")
    else:
        print(f"  Cache: ❌ Failed")
    
    # Test trade storage
    test_trade = {
        'trade_id': f'test_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
        'coin': 'BTC',
        'action': 'BUY',
        'amount': 0.01,
        'price': 45000.0,
        'total_value': 450.0,
        'status': 'COMPLETED',
        'ml_confidence': 0.75
    }
    
    if store_trade(test_trade):
        print(f"  Trade Storage: ✅ Success")
    else:
        print(f"  Trade Storage: ❌ Failed")
    
    print("\n✨ Database Manager test complete!")
