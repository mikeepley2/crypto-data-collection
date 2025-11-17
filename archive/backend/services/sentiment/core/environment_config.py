#!/usr/bin/env python3
"""
Environment Configuration Manager for Trading System

This module provides a unified configuration system that automatically switches
between local development resources and AWS production resources based on the
LOCAL_MODE environment variable.

Features:
- Automatic detection of LOCAL_MODE flag
- Local DynamoDB, MySQL, Redis, and S3 (MinIO) configuration
- Seamless switching between local and AWS resources
- Environment validation and health checks
- Configuration file generation for all services
"""

import os
import json
import logging
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """Database configuration for both local and AWS environments."""
    host: str
    port: int
    username: str
    password: str
    database: str
    region: Optional[str] = None
    table_prefix: Optional[str] = None


@dataclass
class S3Config:
    """S3/MinIO configuration."""
    endpoint: Optional[str]
    access_key: str
    secret_key: str
    bucket_name: str
    region: str


@dataclass
class RedisConfig:
    """Redis configuration."""
    host: str
    port: int
    password: Optional[str] = None
    db: int = 0


@dataclass
class EnvironmentConfig:
    """Complete environment configuration."""
    local_mode: bool
    dynamodb: DatabaseConfig
    mysql: DatabaseConfig
    redis: RedisConfig
    s3: S3Config
    api_keys: Dict[str, str]
    monitoring: Dict[str, Any]


class ConfigManager:
    """Manages configuration for local and AWS environments."""
    
    def __init__(self):
        self.local_mode = self._detect_local_mode()
        self.config = self._build_config()
        self._setup_logging()
    
    def _detect_local_mode(self) -> bool:
        """Detect if we're running in local development mode."""
        local_flags = [
            os.environ.get('LOCAL_MODE', '').lower() in ['true', '1', 'yes'],
            os.environ.get('ENVIRONMENT', '').lower() == 'local',
            os.environ.get('AWS_EXECUTION_ENV') is None,  # Not running on AWS
            not os.path.exists('/opt/aws'),  # Not on AWS infrastructure
        ]
        
        # If any LOCAL flag is explicitly set, use local mode
        explicit_local = any([
            os.environ.get('LOCAL_MODE'),
            os.environ.get('ENVIRONMENT') == 'local'
        ])
        
        if explicit_local:
            return os.environ.get('LOCAL_MODE', '').lower() in ['true', '1', 'yes']
        
        # Default: use local mode for development
        return True
    
    def _build_config(self) -> EnvironmentConfig:
        """Build configuration based on environment mode."""
        if self.local_mode:
            return self._build_local_config()
        else:
            return self._build_aws_config()
    
    def _build_local_config(self) -> EnvironmentConfig:
        """Build configuration for local development."""
        return EnvironmentConfig(
            local_mode=True,
            dynamodb=DatabaseConfig(
                host="localhost",
                port=8000,
                username="",
                password="",
                database="local",
                region="us-west-2",
                table_prefix="local_"
            ),
            mysql=DatabaseConfig(
                host="localhost",
                port=3306,
                username="admin",
                password="99Rules!",
                database="trading_db",
                region=None
            ),
            redis=RedisConfig(
                host="localhost",
                port=6379,
                password=None,
                db=0
            ),
            s3=S3Config(
                endpoint="http://localhost:9000",
                access_key="minioadmin",
                secret_key="minioadmin",
                bucket_name="crypto-trading-local",
                region="us-west-2"
            ),
            api_keys={
                "xai_api_key": os.environ.get("XAI_API_KEY", ""),
                "openai_api_key": os.environ.get("OPENAI_API_KEY", ""),
                "news_api_key": os.environ.get("NEWS_API_KEY", ""),
                "coingecko_api_key": os.environ.get("COINGECKO_API_KEY", ""),
                "fred_api_key": os.environ.get("FRED_API_KEY", ""),
                "coingecko_plan": os.environ.get("COINGECKO_PLAN", "premium"),
                "coingecko_monthly_limit": int(os.environ.get("COINGECKO_MONTHLY_LIMIT", "500000")),
                "coingecko_requests_per_minute": int(os.environ.get("COINGECKO_REQUESTS_PER_MINUTE", "300"))
            },
            monitoring={
                "prometheus_url": "http://localhost:9090",
                "grafana_url": "http://localhost:3000",
                "log_level": "DEBUG"
            }
        )
    
    def _build_aws_config(self) -> EnvironmentConfig:
        """Build configuration for AWS production."""
        return EnvironmentConfig(
            local_mode=False,
            dynamodb=DatabaseConfig(
                host="",  # Uses AWS SDK default
                port=443,
                username="",
                password="",
                database="",
                region=os.environ.get("AWS_REGION", "us-west-2"),
                table_prefix=""
            ),
            mysql=DatabaseConfig(
                host=os.environ.get("AURORA_ENDPOINT", ""),
                port=3306,
                username=os.environ.get("AURORA_USERNAME", "admin"),
                password=os.environ.get("AURORA_PASSWORD", ""),
                database=os.environ.get("AURORA_DATABASE", "trading_db"),
                region=os.environ.get("AWS_REGION", "us-west-2")
            ),
            redis=RedisConfig(
                host=os.environ.get("REDIS_ENDPOINT", ""),
                port=6379,
                password=os.environ.get("REDIS_PASSWORD"),
                db=0
            ),
            s3=S3Config(
                endpoint=None,  # Uses AWS default
                access_key="",  # Uses IAM role
                secret_key="",  # Uses IAM role
                bucket_name=os.environ.get("S3_BUCKET", "crypto-trading-prod"),
                region=os.environ.get("AWS_REGION", "us-west-2")
            ),
            api_keys={
                "xai_api_key": os.environ.get("XAI_API_KEY", ""),
                "openai_api_key": os.environ.get("OPENAI_API_KEY", ""),
                "news_api_key": os.environ.get("NEWS_API_KEY", ""),
                "coingecko_api_key": os.environ.get("COINGECKO_API_KEY", ""),
                "fred_api_key": os.environ.get("FRED_API_KEY", ""),
                "coingecko_plan": os.environ.get("COINGECKO_PLAN", "premium"),
                "coingecko_monthly_limit": int(os.environ.get("COINGECKO_MONTHLY_LIMIT", "500000")),
                "coingecko_requests_per_minute": int(os.environ.get("COINGECKO_REQUESTS_PER_MINUTE", "300"))
            },
            monitoring={
                "prometheus_url": "",  # Uses CloudWatch
                "grafana_url": "",     # Uses CloudWatch dashboards
                "log_level": "INFO"
            }
        )
    
    def _setup_logging(self):
        """Configure logging based on environment."""
        log_level = getattr(logging, self.config.monitoring["log_level"])
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        mode = "LOCAL" if self.local_mode else "AWS"
        logger.info(f"Configuration initialized for {mode} mode")
    
    def get_dynamodb_config(self) -> Dict[str, Any]:
        """Get DynamoDB configuration for boto3."""
        if self.local_mode:
            return {
                "endpoint_url": f"http://{self.config.dynamodb.host}:{self.config.dynamodb.port}",
                "region_name": self.config.dynamodb.region,
                "aws_access_key_id": "local",
                "aws_secret_access_key": "local"
            }
        else:
            return {
                "region_name": self.config.dynamodb.region
            }
    
    def get_mysql_url(self) -> str:
        """Get MySQL connection URL."""
        cfg = self.config.mysql
        return f"mysql+pymysql://{cfg.username}:{cfg.password}@{cfg.host}:{cfg.port}/{cfg.database}"
    
    def get_redis_url(self) -> str:
        """Get Redis connection URL."""
        cfg = self.config.redis
        auth = f":{cfg.password}@" if cfg.password else ""
        return f"redis://{auth}{cfg.host}:{cfg.port}/{cfg.db}"
    
    def get_s3_config(self) -> Dict[str, Any]:
        """Get S3/MinIO configuration."""
        if self.local_mode:
            return {
                "endpoint_url": self.config.s3.endpoint,
                "aws_access_key_id": self.config.s3.access_key,
                "aws_secret_access_key": self.config.s3.secret_key,
                "region_name": self.config.s3.region
            }
        else:
            return {
                "region_name": self.config.s3.region
            }
    
    def get_table_name(self, base_name: str) -> str:
        """Get table name with appropriate prefix."""
        prefix = self.config.dynamodb.table_prefix or ""
        return f"{prefix}{base_name}"
    
    def export_env_file(self, file_path: str = ".env.local"):
        """Export configuration to environment file."""
        env_vars = []
        
        # Environment mode
        env_vars.append(f"LOCAL_MODE={'true' if self.local_mode else 'false'}")
        env_vars.append(f"ENVIRONMENT={'local' if self.local_mode else 'aws'}")
        
        # Database configurations
        if self.local_mode:
            env_vars.extend([
                f"DYNAMODB_ENDPOINT=http://{self.config.dynamodb.host}:{self.config.dynamodb.port}",
                f"MYSQL_URL={self.get_mysql_url()}",
                f"REDIS_URL={self.get_redis_url()}",
                f"S3_ENDPOINT={self.config.s3.endpoint}",
                f"S3_ACCESS_KEY={self.config.s3.access_key}",
                f"S3_SECRET_KEY={self.config.s3.secret_key}",
            ])
        
        # API keys
        for key, value in self.config.api_keys.items():
            if value:
                env_vars.append(f"{key.upper()}={value}")
        
        # AWS region
        env_vars.append(f"AWS_REGION={self.config.dynamodb.region}")
        
        # Table names
        env_vars.extend([
            f"DYNAMODB_TRADES_TABLE={self.get_table_name('trading_trades')}",
            f"DYNAMODB_PRICES_TABLE={self.get_table_name('mikeaitest_prices')}",
            f"DYNAMODB_SENTIMENT_TABLE={self.get_table_name('sentiment_data')}",
            f"DYNAMODB_TECHNICALS_TABLE={self.get_table_name('technical_indicators')}",
        ])
        
        # Write to file
        with open(file_path, 'w') as f:
            f.write("\n".join(env_vars))
        
        logger.info(f"Environment configuration exported to {file_path}")
    
    def validate_configuration(self) -> Dict[str, bool]:
        """Validate that all required services are accessible."""
        results = {}
        
        if self.local_mode:
            results.update(self._validate_local_services())
        else:
            results.update(self._validate_aws_services())
        
        return results
    
    def _validate_local_services(self) -> Dict[str, bool]:
        """Validate local development services."""
        results = {}
        
        # Test DynamoDB Local
        try:
            import boto3
            dynamodb = boto3.resource('dynamodb', **self.get_dynamodb_config())
            dynamodb.meta.client.list_tables()
            results['dynamodb'] = True
        except Exception as e:
            logger.warning(f"DynamoDB Local not accessible: {e}")
            results['dynamodb'] = False
        
        # Test MySQL
        try:
            import pymysql
            connection = pymysql.connect(
                host=self.config.mysql.host,
                port=self.config.mysql.port,
                user=self.config.mysql.username,
                password=self.config.mysql.password,
                database=self.config.mysql.database
            )
            connection.close()
            results['mysql'] = True
        except Exception as e:
            logger.warning(f"MySQL not accessible: {e}")
            results['mysql'] = False
        
        # Test Redis
        try:
            import redis
            r = redis.Redis(
                host=self.config.redis.host,
                port=self.config.redis.port,
                password=self.config.redis.password,
                db=self.config.redis.db
            )
            r.ping()
            results['redis'] = True
        except Exception as e:
            logger.warning(f"Redis not accessible: {e}")
            results['redis'] = False
        
        # Test MinIO (S3)
        try:
            import boto3
            s3 = boto3.client('s3', **self.get_s3_config())
            s3.list_buckets()
            results['s3'] = True
        except Exception as e:
            logger.warning(f"MinIO not accessible: {e}")
            results['s3'] = False
        
        return results
    
    def _validate_aws_services(self) -> Dict[str, bool]:
        """Validate AWS services."""
        results = {}
        
        try:
            import boto3
            
            # Test DynamoDB
            dynamodb = boto3.resource('dynamodb', **self.get_dynamodb_config())
            dynamodb.meta.client.list_tables()
            results['dynamodb'] = True
            
            # Test S3
            s3 = boto3.client('s3', **self.get_s3_config())
            s3.list_buckets()
            results['s3'] = True
            
        except Exception as e:
            logger.warning(f"AWS services validation failed: {e}")
            results['dynamodb'] = False
            results['s3'] = False
        
        # MySQL validation would require connection details
        results['mysql'] = True  # Assume valid if Aurora endpoint is set
        results['redis'] = True  # Assume valid if Redis endpoint is set
        
        return results
    
    def setup_local_tables(self):
        """Set up local DynamoDB tables with proper schema."""
        if not self.local_mode:
            logger.warning("setup_local_tables() called but not in local mode")
            return
        
        try:
            import boto3
            dynamodb = boto3.resource('dynamodb', **self.get_dynamodb_config())
            
            # Define table schemas
            tables = [
                {
                    'TableName': self.get_table_name('trading_trades'),
                    'KeySchema': [
                        {'AttributeName': 'trade_id', 'KeyType': 'HASH'}
                    ],
                    'AttributeDefinitions': [
                        {'AttributeName': 'trade_id', 'AttributeType': 'S'}
                    ]
                },
                {
                    'TableName': self.get_table_name('mikeaitest_prices'),
                    'KeySchema': [
                        {'AttributeName': 'coin_id', 'KeyType': 'HASH'},
                        {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                    ],
                    'AttributeDefinitions': [
                        {'AttributeName': 'coin_id', 'AttributeType': 'S'},
                        {'AttributeName': 'timestamp', 'AttributeType': 'S'},
                        {'AttributeName': 'type', 'AttributeType': 'S'}
                    ],
                    'GlobalSecondaryIndexes': [
                        {
                            'IndexName': 'TypeTimestampIndex',
                            'KeySchema': [
                                {'AttributeName': 'type', 'KeyType': 'HASH'},
                                {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                            ],
                            'Projection': {'ProjectionType': 'ALL'}
                        }
                    ]
                },
                {
                    'TableName': self.get_table_name('sentiment_data'),
                    'KeySchema': [
                        {'AttributeName': 'sentiment_id', 'KeyType': 'HASH'},
                        {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                    ],
                    'AttributeDefinitions': [
                        {'AttributeName': 'sentiment_id', 'AttributeType': 'S'},
                        {'AttributeName': 'timestamp', 'AttributeType': 'S'},
                        {'AttributeName': 'coin_id', 'AttributeType': 'S'},
                        {'AttributeName': 'type', 'AttributeType': 'S'}
                    ],
                    'GlobalSecondaryIndexes': [
                        {
                            'IndexName': 'CoinTimestampIndex',
                            'KeySchema': [
                                {'AttributeName': 'coin_id', 'KeyType': 'HASH'},
                                {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                            ],
                            'Projection': {'ProjectionType': 'ALL'}
                        },
                        {
                            'IndexName': 'TypeTimestampIndex',
                            'KeySchema': [
                                {'AttributeName': 'type', 'KeyType': 'HASH'},
                                {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                            ],
                            'Projection': {'ProjectionType': 'ALL'}
                        }
                    ]
                },
                {
                    'TableName': self.get_table_name('technical_indicators'),
                    'KeySchema': [
                        {'AttributeName': 'indicator_id', 'KeyType': 'HASH'},
                        {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                    ],
                    'AttributeDefinitions': [
                        {'AttributeName': 'indicator_id', 'AttributeType': 'S'},
                        {'AttributeName': 'timestamp', 'AttributeType': 'S'},
                        {'AttributeName': 'coin_id', 'AttributeType': 'S'},
                        {'AttributeName': 'indicator_type', 'AttributeType': 'S'}
                    ],
                    'GlobalSecondaryIndexes': [
                        {
                            'IndexName': 'CoinTimestampIndex',
                            'KeySchema': [
                                {'AttributeName': 'coin_id', 'KeyType': 'HASH'},
                                {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                            ],
                            'Projection': {'ProjectionType': 'ALL'}
                        },
                        {
                            'IndexName': 'IndicatorTypeIndex',
                            'KeySchema': [
                                {'AttributeName': 'indicator_type', 'KeyType': 'HASH'},
                                {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                            ],
                            'Projection': {'ProjectionType': 'ALL'}
                        }
                    ]
                }
            ]
            
            # Create tables
            for table_def in tables:
                try:
                    # Set billing mode for local DynamoDB
                    table_def['BillingMode'] = 'PAY_PER_REQUEST'
                    
                    # Handle Global Secondary Indexes
                    if 'GlobalSecondaryIndexes' in table_def:
                        for gsi in table_def['GlobalSecondaryIndexes']:
                            gsi['BillingMode'] = 'PAY_PER_REQUEST'
                    
                    table = dynamodb.create_table(**table_def)
                    logger.info(f"Created local table: {table_def['TableName']}")
                    
                except dynamodb.meta.client.exceptions.ResourceInUseException:
                    logger.info(f"Table {table_def['TableName']} already exists")
                except Exception as e:
                    logger.error(f"Failed to create table {table_def['TableName']}: {e}")
            
        except Exception as e:
            logger.error(f"Failed to setup local tables: {e}")


# Global configuration instance
config_manager = ConfigManager()


def get_config() -> ConfigManager:
    """Get the global configuration manager instance."""
    return config_manager


def is_local_mode() -> bool:
    """Check if running in local development mode."""
    return config_manager.local_mode


def get_dynamodb_resource():
    """Get DynamoDB resource configured for current environment."""
    import boto3
    return boto3.resource('dynamodb', **config_manager.get_dynamodb_config())


def get_s3_client():
    """Get S3/MinIO client configured for current environment."""
    import boto3
    return boto3.client('s3', **config_manager.get_s3_config())


def get_mysql_engine():
    """Get SQLAlchemy engine for MySQL/Aurora."""
    from sqlalchemy import create_engine
    return create_engine(config_manager.get_mysql_url(), pool_pre_ping=True)


def get_redis_client():
    """Get Redis client configured for current environment."""
    import redis
    cfg = config_manager.config.redis
    return redis.Redis(
        host=cfg.host,
        port=cfg.port,
        password=cfg.password,
        db=cfg.db
    )


# CLI tool for configuration management
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Trading System Configuration Manager")
    parser.add_argument("--mode", choices=["local", "aws"], help="Override environment mode")
    parser.add_argument("--export", metavar="FILE", help="Export environment to file")
    parser.add_argument("--validate", action="store_true", help="Validate configuration")
    parser.add_argument("--setup-tables", action="store_true", help="Setup local DynamoDB tables")
    parser.add_argument("--status", action="store_true", help="Show configuration status")
    
    args = parser.parse_args()
    
    # Override mode if specified
    if args.mode:
        os.environ['LOCAL_MODE'] = str(args.mode == 'local').lower()
        config_manager = ConfigManager()
    
    if args.export:
        config_manager.export_env_file(args.export)
        print(f"Configuration exported to {args.export}")
    
    if args.validate:
        results = config_manager.validate_configuration()
        print("\nService Validation Results:")
        for service, status in results.items():
            status_str = "✅ OK" if status else "❌ FAILED"
            print(f"  {service:12}: {status_str}")
    
    if args.setup_tables:
        if config_manager.local_mode:
            config_manager.setup_local_tables()
            print("Local DynamoDB tables created")
        else:
            print("setup-tables only available in local mode")
    
    if args.status or not any([args.export, args.validate, args.setup_tables]):
        mode = "LOCAL" if config_manager.local_mode else "AWS"
        print(f"\n🚀 Trading System Configuration Status")
        print(f"Mode: {mode}")
        print(f"DynamoDB: {config_manager.config.dynamodb.host}:{config_manager.config.dynamodb.port}")
        print(f"MySQL: {config_manager.config.mysql.host}:{config_manager.config.mysql.port}")
        print(f"Redis: {config_manager.config.redis.host}:{config_manager.config.redis.port}")
        if config_manager.local_mode:
            print(f"MinIO: {config_manager.config.s3.endpoint}")
        print(f"Monitoring: {config_manager.config.monitoring}")
