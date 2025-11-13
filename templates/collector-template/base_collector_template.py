#!/usr/bin/env python3
"""
Base Collector Template for Crypto Data Collection System
Provides standardized logging, metrics, health checks, and backfill capabilities
"""

import asyncio
import logging
import os
import json
import time
import uuid
from datetime import datetime, timedelta, timezone
from contextlib import contextmanager
from typing import Dict, Any, List, Optional, Tuple
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

import mysql.connector
import aiohttp
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, validator
import uvicorn
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import structlog
import hashlib
import signal
from functools import wraps
import asyncio
from collections import defaultdict, deque
import threading

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.dev.ConsoleRenderer() if os.getenv('LOG_FORMAT', 'json') == 'console' else structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

class LogLevel(Enum):
    TRACE = "trace"
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    NONE = "none"

class CircuitBreakerState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    """Circuit breaker for external API calls"""
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60, expected_exception=Exception):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitBreakerState.CLOSED
        self._lock = threading.Lock()

    def call(self, func, *args, **kwargs):
        with self._lock:
            if self.state == CircuitBreakerState.OPEN:
                if time.time() - self.last_failure_time > self.timeout:
                    self.state = CircuitBreakerState.HALF_OPEN
                else:
                    raise Exception("Circuit breaker is OPEN")
            
            try:
                result = func(*args, **kwargs)
                self._on_success()
                return result
            except self.expected_exception as e:
                self._on_failure()
                raise e

    def _on_success(self):
        self.failure_count = 0
        self.state = CircuitBreakerState.CLOSED

    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN

class RateLimiter:
    """Token bucket rate limiter"""
    
    def __init__(self, max_tokens: int = 60, refill_rate: float = 1.0):
        self.max_tokens = max_tokens
        self.tokens = max_tokens
        self.refill_rate = refill_rate
        self.last_refill = time.time()
        self._lock = threading.Lock()

    async def acquire(self, tokens: int = 1) -> bool:
        with self._lock:
            now = time.time()
            elapsed = now - self.last_refill
            self.tokens = min(self.max_tokens, self.tokens + elapsed * self.refill_rate)
            self.last_refill = now
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    async def wait_for_token(self, tokens: int = 1):
        while not await self.acquire(tokens):
            await asyncio.sleep(0.1)

class DataValidator:
    """Data validation utilities"""
    
    @staticmethod
    def validate_required_fields(data: dict, required_fields: list) -> bool:
        return all(field in data and data[field] is not None for field in required_fields)
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = 1000) -> str:
        if not isinstance(value, str):
            return str(value)[:max_length]
        return value.strip()[:max_length]
    
    @staticmethod
    def validate_numeric_range(value, min_val=None, max_val=None) -> bool:
        if not isinstance(value, (int, float)):
            return False
        if min_val is not None and value < min_val:
            return False
        if max_val is not None and value > max_val:
            return False
        return True
    
    @staticmethod
    def generate_data_hash(data: dict) -> str:
        """Generate consistent hash for duplicate detection"""
        # Sort keys for consistent hashing
        sorted_data = json.dumps(data, sort_keys=True, default=str)
        return hashlib.md5(sorted_data.encode()).hexdigest()

@dataclass
class CollectorConfig:
    """Central configuration for collectors"""
    # Database configuration
    mysql_host: str
    mysql_port: int
    mysql_user: str
    mysql_password: str
    mysql_database: str
    
    # Collection configuration
    collection_interval: int
    backfill_batch_size: int
    max_retry_attempts: int
    api_timeout: int
    api_rate_limit: int
    
    # Date configuration
    collector_beginning_date: str  # Format: YYYY-MM-DD
    backfill_lookback_days: int
    
    # Logging configuration
    log_level: LogLevel
    log_format: str
    enable_audit_logging: bool
    
    # Service configuration
    service_name: str
    service_version: str
    health_check_interval: int
    
    # Rate limiting and circuit breaker
    enable_rate_limiting: bool
    api_rate_limit_per_minute: int
    circuit_breaker_failure_threshold: int
    circuit_breaker_timeout: int
    
    # Data validation and quality
    enable_data_validation: bool
    enable_duplicate_detection: bool
    data_retention_days: int
    
    # Performance and optimization
    connection_pool_size: int
    query_timeout: int
    batch_commit_size: int
    
    # Alerting and notifications
    enable_alerting: bool
    alert_webhook_url: Optional[str]
    alert_error_threshold: int
    
    @classmethod
    def from_env(cls) -> 'CollectorConfig':
        """Load configuration from environment variables"""
        return cls(
            # Database
            mysql_host=os.getenv('MYSQL_HOST', 'host.docker.internal'),
            mysql_port=int(os.getenv('MYSQL_PORT', '3306')),
            mysql_user=os.getenv('MYSQL_USER', 'news_collector'),
            mysql_password=os.getenv('MYSQL_PASSWORD', '99Rules!'),
            mysql_database=os.getenv('MYSQL_DATABASE', 'crypto_prices'),
            
            # Collection
            collection_interval=int(os.getenv('COLLECTION_INTERVAL', '900')),  # 15 minutes
            backfill_batch_size=int(os.getenv('BACKFILL_BATCH_SIZE', '100')),
            max_retry_attempts=int(os.getenv('MAX_RETRY_ATTEMPTS', '3')),
            api_timeout=int(os.getenv('API_TIMEOUT', '30')),
            api_rate_limit=int(os.getenv('API_RATE_LIMIT', '60')),
            
            # Dates
            collector_beginning_date=os.getenv('COLLECTOR_BEGINNING_DATE', '2023-01-01'),
            backfill_lookback_days=int(os.getenv('BACKFILL_LOOKBACK_DAYS', '30')),
            
            # Logging
            log_level=LogLevel(os.getenv('LOG_LEVEL', 'trace').lower()),
            log_format=os.getenv('LOG_FORMAT', 'json'),
            enable_audit_logging=os.getenv('ENABLE_AUDIT_LOGGING', 'true').lower() == 'true',
            
            # Service
            service_name=os.getenv('SERVICE_NAME', 'base-collector'),
            service_version=os.getenv('SERVICE_VERSION', '1.0.0'),
            health_check_interval=int(os.getenv('HEALTH_CHECK_INTERVAL', '30')),
            
            # Rate limiting and circuit breaker
            enable_rate_limiting=os.getenv('ENABLE_RATE_LIMITING', 'true').lower() == 'true',
            api_rate_limit_per_minute=int(os.getenv('API_RATE_LIMIT_PER_MINUTE', '60')),
            circuit_breaker_failure_threshold=int(os.getenv('CIRCUIT_BREAKER_FAILURE_THRESHOLD', '5')),
            circuit_breaker_timeout=int(os.getenv('CIRCUIT_BREAKER_TIMEOUT', '60')),
            
            # Data validation and quality
            enable_data_validation=os.getenv('ENABLE_DATA_VALIDATION', 'true').lower() == 'true',
            enable_duplicate_detection=os.getenv('ENABLE_DUPLICATE_DETECTION', 'true').lower() == 'true',
            data_retention_days=int(os.getenv('DATA_RETENTION_DAYS', '365')),
            
            # Performance and optimization
            connection_pool_size=int(os.getenv('CONNECTION_POOL_SIZE', '10')),
            query_timeout=int(os.getenv('QUERY_TIMEOUT', '30')),
            batch_commit_size=int(os.getenv('BATCH_COMMIT_SIZE', '1000')),
            
            # Alerting and notifications
            enable_alerting=os.getenv('ENABLE_ALERTING', 'false').lower() == 'true',
            alert_webhook_url=os.getenv('ALERT_WEBHOOK_URL'),
            alert_error_threshold=int(os.getenv('ALERT_ERROR_THRESHOLD', '10'))
        )

class BaseModel(BaseModel):
    """Base Pydantic model for API responses"""
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    service: str
    version: str
    uptime_seconds: float
    database_connected: bool
    last_collection: Optional[datetime]
    last_successful_collection: Optional[datetime]
    collection_errors: int

class ReadinessResponse(BaseModel):
    ready: bool
    timestamp: datetime
    service: str
    checks: Dict[str, bool]

class StatusResponse(BaseModel):
    service_info: Dict[str, Any]
    database_status: Dict[str, Any]
    collection_status: Dict[str, Any]
    metrics: Dict[str, Any]
    configuration: Dict[str, Any]

class BackfillRequest(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    symbols: Optional[List[str]] = None
    force: bool = False

class BackfillResponse(BaseModel):
    task_id: str
    status: str
    message: str
    estimated_records: Optional[int] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class DataQualityReport(BaseModel):
    total_records: int
    valid_records: int
    invalid_records: int
    duplicate_records: int
    validation_errors: List[str]
    data_quality_score: float
    
class AlertRequest(BaseModel):
    alert_type: str
    severity: str
    message: str
    service: str
    additional_data: Optional[Dict[str, Any]] = None

class PerformanceMetrics(BaseModel):
    avg_collection_time: float
    success_rate: float
    error_rate: float
    database_latency: float
    api_latency: float
    memory_usage_mb: float
    cpu_usage_percent: float

class BaseCollector(ABC):
    """
    Base class for all data collectors in the crypto data collection system.
    Provides standardized logging, metrics, health checks, and backfill capabilities.
    """
    
    def __init__(self, config: CollectorConfig):
        self.config = config
        self.app = FastAPI(
            title=f"{config.service_name.replace('-', ' ').title()}",
            version=config.service_version,
            description=f"Standardized data collector for {config.service_name}"
        )
        
        # Service state
        self.start_time = datetime.now(timezone.utc)
        self.session_id = str(uuid.uuid4())
        self.is_collecting = False
        self.collection_task = None
        self.last_collection = None
        self.last_successful_collection = None
        self.collection_errors = 0
        self.startup_complete = False
        
        # Additional components
        self.rate_limiter = RateLimiter(max_tokens=config.api_rate_limit_per_minute, refill_rate=1.0) if config.enable_rate_limiting else None
        self.circuit_breaker = CircuitBreaker(failure_threshold=config.circuit_breaker_failure_threshold, timeout=config.circuit_breaker_timeout)
        self.data_validator = DataValidator()
        self.duplicate_hashes = deque(maxlen=10000)  # Keep track of recent data hashes
        self.performance_metrics = defaultdict(list)
        
        # Graceful shutdown handling
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        self._shutdown_event = asyncio.Event()
        
        # Setup logging
        self._setup_logging()
        self.logger = structlog.get_logger(service=config.service_name, session=self.session_id)
        
        # Setup metrics
        self._setup_metrics()
        
        # Setup routes
        self._setup_routes()
        
        self.logger.info(
            "collector_initialized",
            service=config.service_name,
            version=config.service_version,
            session_id=self.session_id
        )

    def _setup_logging(self):
        """Configure logging based on configuration"""
        log_levels = {
            LogLevel.TRACE: logging.DEBUG,
            LogLevel.DEBUG: logging.DEBUG,
            LogLevel.INFO: logging.INFO,
            LogLevel.WARNING: logging.WARNING,
            LogLevel.ERROR: logging.ERROR,
            LogLevel.CRITICAL: logging.CRITICAL,
            LogLevel.NONE: logging.CRITICAL + 1
        }
        
        logging.basicConfig(
            level=log_levels.get(self.config.log_level, logging.INFO),
            format='%(message)s' if self.config.log_format == 'json' else 
                   '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def _setup_metrics(self):
        """Setup Prometheus metrics"""
        service_name = self.config.service_name.replace('-', '_')
        
        self.metrics = {
            'collection_requests_total': Counter(
                f'{service_name}_collection_requests_total',
                'Total collection requests',
                ['status']
            ),
            'collection_duration_seconds': Histogram(
                f'{service_name}_collection_duration_seconds',
                'Collection duration in seconds'
            ),
            'records_processed_total': Counter(
                f'{service_name}_records_processed_total',
                'Total records processed',
                ['operation']
            ),
            'database_operations_total': Counter(
                f'{service_name}_database_operations_total',
                'Total database operations',
                ['operation', 'status']
            ),
            'api_requests_total': Counter(
                f'{service_name}_api_requests_total',
                'Total API requests',
                ['endpoint', 'status']
            ),
            'backfill_operations_total': Counter(
                f'{service_name}_backfill_operations_total',
                'Total backfill operations',
                ['status']
            ),
            'active_collections': Gauge(
                f'{service_name}_active_collections',
                'Number of active collection processes'
            )
        }

    def _setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/health", response_model=HealthResponse)
        async def health():
            """Health check endpoint - Kubernetes liveness probe"""
            database_connected = await self._check_database_connection()
            
            return HealthResponse(
                status="healthy" if database_connected else "unhealthy",
                timestamp=datetime.now(timezone.utc),
                service=self.config.service_name,
                version=self.config.service_version,
                uptime_seconds=(datetime.now(timezone.utc) - self.start_time).total_seconds(),
                database_connected=database_connected,
                last_collection=self.last_collection,
                last_successful_collection=self.last_successful_collection,
                collection_errors=self.collection_errors
            )

        @self.app.get("/ready", response_model=ReadinessResponse)
        async def ready():
            """Readiness check endpoint - Kubernetes readiness probe"""
            is_ready = await self._check_service_readiness()
            
            return ReadinessResponse(
                ready=is_ready,
                timestamp=datetime.now(timezone.utc),
                service=self.config.service_name,
                checks={
                    "database": await self._check_database_connection(),
                    "configuration": self._check_configuration_valid(),
                    "dependencies": await self._check_dependencies(),
                    "circuit_breaker": self.circuit_breaker.state.value != "open",
                    "rate_limiter": self.rate_limiter is not None if self.config.enable_rate_limiting else True,
                    "startup_complete": self.startup_complete
                }
            )

        @self.app.get("/status", response_model=StatusResponse)
        async def status():
            """Detailed status endpoint"""
            database_status = await self._get_database_status()
            collection_status = await self._get_collection_status()
            metrics_summary = self._get_metrics_summary()
            
            return StatusResponse(
                service_info={
                    "name": self.config.service_name,
                    "version": self.config.service_version,
                    "uptime_seconds": (datetime.now(timezone.utc) - self.start_time).total_seconds(),
                    "session_id": self.session_id,
                    "start_time": self.start_time,
                    "is_collecting": self.is_collecting
                },
                database_status=database_status,
                collection_status=collection_status,
                metrics=metrics_summary,
                configuration=self._get_safe_config()
            )

        @self.app.get("/logs")
        async def logs(
            level: str = Query("info", description="Log level filter"),
            limit: int = Query(100, description="Number of log entries to return"),
            since: Optional[str] = Query(None, description="ISO timestamp to filter logs since")
        ):
            """Logs endpoint (placeholder - integrate with Loki)"""
            # This would integrate with Loki in production
            return {
                "message": "Log endpoint - integrate with Loki for production",
                "parameters": {
                    "level": level,
                    "limit": limit,
                    "since": since
                },
                "loki_query_url": f"http://loki:3100/loki/api/v1/query_range?query={{service=\"{self.config.service_name}\"}}"
            }

        @self.app.get("/metrics")
        async def metrics():
            """Prometheus metrics endpoint"""
            return JSONResponse(
                content=generate_latest().decode('utf-8'),
                media_type="text/plain"
            )

        @self.app.post("/collect")
        async def manual_collect(background_tasks: BackgroundTasks):
            """Manual collection trigger"""
            if self.is_collecting:
                return {"status": "already_collecting", "message": "Collection is already in progress"}
            
            task_id = str(uuid.uuid4())
            background_tasks.add_task(self._perform_collection, task_id)
            
            self.logger.info("manual_collection_triggered", task_id=task_id)
            return {"status": "started", "message": "Manual collection started", "task_id": task_id}

        @self.app.post("/backfill", response_model=BackfillResponse)
        async def backfill(request: BackfillRequest, background_tasks: BackgroundTasks):
            """Backfill endpoint for missing data"""
            task_id = str(uuid.uuid4())
            
            # Determine date range
            if request.start_date:
                start_date = datetime.fromisoformat(request.start_date)
            else:
                start_date = datetime.fromisoformat(self.config.collector_beginning_date)
            
            if request.end_date:
                end_date = datetime.fromisoformat(request.end_date)
            else:
                end_date = datetime.now(timezone.utc) - timedelta(days=1)
            
            # Estimate records to backfill
            estimated_records = await self._estimate_backfill_records(start_date, end_date, request.symbols)
            
            # Start backfill task
            background_tasks.add_task(
                self._perform_backfill,
                task_id,
                start_date,
                end_date,
                request.symbols,
                request.force
            )
            
            self.logger.info(
                "backfill_started",
                task_id=task_id,
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
                symbols=request.symbols,
                estimated_records=estimated_records
            )
            
            return BackfillResponse(
                task_id=task_id,
                status="started",
                message="Backfill operation started",
                estimated_records=estimated_records,
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat()
            )

        @self.app.get("/data-quality", response_model=DataQualityReport)
        async def data_quality():
            """Data quality report endpoint"""
            report = await self._generate_data_quality_report()
            return report

        @self.app.get("/performance", response_model=PerformanceMetrics)
        async def performance():
            """Performance metrics endpoint"""
            metrics = await self._get_performance_metrics()
            return metrics

        @self.app.post("/alert")
        async def send_alert(alert: AlertRequest):
            """Send alert notification"""
            if self.config.enable_alerting:
                await self._send_alert(alert)
                return {"status": "alert_sent", "message": "Alert notification sent successfully"}
            else:
                return {"status": "alerting_disabled", "message": "Alerting is not enabled"}

        @self.app.post("/validate-data")
        async def validate_data(data: dict):
            """Validate data structure and content"""
            if not self.config.enable_data_validation:
                return {"status": "validation_disabled", "message": "Data validation is not enabled"}
            
            validation_result = await self._validate_data(data)
            return validation_result

        @self.app.get("/circuit-breaker-status")
        async def circuit_breaker_status():
            """Get circuit breaker status"""
            return {
                "state": self.circuit_breaker.state.value,
                "failure_count": self.circuit_breaker.failure_count,
                "last_failure_time": self.circuit_breaker.last_failure_time
            }

    @contextmanager
    def get_database_connection(self):
        """Database connection context manager"""
        conn = None
        try:
            conn = mysql.connector.connect(
                host=self.config.mysql_host,
                port=self.config.mysql_port,
                user=self.config.mysql_user,
                password=self.config.mysql_password,
                database=self.config.mysql_database,
                charset='utf8mb4',
                autocommit=False
            )
            yield conn
        except Exception as e:
            self.logger.error("database_connection_error", error=str(e))
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

    async def _check_database_connection(self) -> bool:
        """Check database connectivity"""
        try:
            with self.get_database_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                return True
        except Exception as e:
            self.logger.error("database_health_check_failed", error=str(e))
            return False

    async def _check_service_readiness(self) -> bool:
        """Check if service is ready to receive traffic"""
        checks = {
            "database": await self._check_database_connection(),
            "configuration": self._check_configuration_valid(),
            "dependencies": await self._check_dependencies(),
            "circuit_breaker": self.circuit_breaker.state.value != "open",
            "rate_limiter": self.rate_limiter is not None if self.config.enable_rate_limiting else True,
            "startup_complete": self.startup_complete
        }
        
        # All checks must pass for service to be ready
        return all(checks.values())

    def _check_configuration_valid(self) -> bool:
        """Check if configuration is valid"""
        try:
            # Check required configuration
            required_config = [
                self.config.mysql_host,
                self.config.mysql_database,
                self.config.mysql_user,
                self.config.service_name
            ]
            
            return all(config_item is not None for config_item in required_config)
        except Exception as e:
            self.logger.error("configuration_validation_failed", error=str(e))
            return False

    async def _check_dependencies(self) -> bool:
        """Check if external dependencies are available"""
        # Override in subclasses for service-specific dependency checks
        # For example: check if external APIs are reachable
        return True

    async def _get_database_status(self) -> Dict[str, Any]:
        """Get detailed database status"""
        try:
            with self.get_database_connection() as conn:
                cursor = conn.cursor()
                
                # Check connection
                cursor.execute("SELECT 1")
                connected = True
                
                # Get database info
                cursor.execute("SELECT VERSION()")
                db_version = cursor.fetchone()[0]
                
                # Get table info for this collector
                table_info = await self._get_table_status(cursor)
                
                return {
                    "connected": connected,
                    "version": db_version,
                    "host": self.config.mysql_host,
                    "database": self.config.mysql_database,
                    "tables": table_info
                }
        except Exception as e:
            self.logger.error("database_status_check_failed", error=str(e))
            return {
                "connected": False,
                "error": str(e)
            }

    async def _get_collection_status(self) -> Dict[str, Any]:
        """Get collection status"""
        return {
            "is_active": self.is_collecting,
            "last_collection": self.last_collection,
            "last_successful_collection": self.last_successful_collection,
            "collection_errors": self.collection_errors,
            "collection_interval_seconds": self.config.collection_interval
        }

    def _get_metrics_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        # This would extract current metric values
        return {
            "collection_requests_total": "Available via /metrics endpoint",
            "records_processed_total": "Available via /metrics endpoint",
            "active_collections": int(self.is_collecting),
            "uptime_seconds": (datetime.now(timezone.utc) - self.start_time).total_seconds()
        }

    def _get_safe_config(self) -> Dict[str, Any]:
        """Get configuration without sensitive data"""
        config_dict = {
            "service_name": self.config.service_name,
            "service_version": self.config.service_version,
            "collection_interval": self.config.collection_interval,
            "backfill_batch_size": self.config.backfill_batch_size,
            "collector_beginning_date": self.config.collector_beginning_date,
            "backfill_lookback_days": self.config.backfill_lookback_days,
            "log_level": self.config.log_level.value,
            "log_format": self.config.log_format,
            "enable_audit_logging": self.config.enable_audit_logging
        }
        return config_dict

    async def _perform_collection(self, task_id: str):
        """Perform collection operation"""
        if self.is_collecting:
            self.logger.warning("collection_already_active", task_id=task_id)
            return

        self.is_collecting = True
        self.metrics['active_collections'].set(1)
        
        try:
            start_time = time.time()
            self.last_collection = datetime.now(timezone.utc)
            
            self.logger.info("collection_started", task_id=task_id)
            
            # Call the abstract method implemented by child classes
            await self.collect_data()
            
            duration = time.time() - start_time
            self.metrics['collection_duration_seconds'].observe(duration)
            self.metrics['collection_requests_total'].labels(status='success').inc()
            
            self.last_successful_collection = datetime.now(timezone.utc)
            
            self.logger.info(
                "collection_completed",
                task_id=task_id,
                duration_seconds=duration
            )
            
        except Exception as e:
            self.metrics['collection_requests_total'].labels(status='error').inc()
            self.collection_errors += 1
            
            self.logger.error(
                "collection_failed",
                task_id=task_id,
                error=str(e)
            )
        finally:
            self.is_collecting = False
            self.metrics['active_collections'].set(0)

    async def _perform_backfill(
        self,
        task_id: str,
        start_date: datetime,
        end_date: datetime,
        symbols: Optional[List[str]],
        force: bool
    ):
        """Perform backfill operation"""
        try:
            self.logger.info(
                "backfill_operation_started",
                task_id=task_id,
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
                symbols=symbols,
                force=force
            )
            
            # Analyze missing data
            missing_data = await self._analyze_missing_data(start_date, end_date, symbols)
            
            self.logger.info(
                "backfill_analysis_complete",
                task_id=task_id,
                missing_periods=len(missing_data)
            )
            
            # Perform backfill
            backfilled_records = await self.backfill_data(missing_data, force)
            
            self.metrics['backfill_operations_total'].labels(status='success').inc()
            
            self.logger.info(
                "backfill_operation_completed",
                task_id=task_id,
                records_backfilled=backfilled_records
            )
            
        except Exception as e:
            self.metrics['backfill_operations_total'].labels(status='error').inc()
            
            self.logger.error(
                "backfill_operation_failed",
                task_id=task_id,
                error=str(e)
            )

    # Abstract methods to be implemented by child classes
    @abstractmethod
    async def collect_data(self) -> int:
        """
        Collect data from the source.
        Should be implemented by child classes.
        Returns number of records collected.
        """
        pass

    @abstractmethod
    async def backfill_data(self, missing_periods: List[Dict], force: bool = False) -> int:
        """
        Backfill missing data.
        Should be implemented by child classes.
        Returns number of records backfilled.
        """
        pass

    @abstractmethod
    async def _get_table_status(self, cursor) -> Dict[str, Any]:
        """
        Get status of tables used by this collector.
        Should be implemented by child classes.
        """
        pass

    @abstractmethod
    async def _analyze_missing_data(
        self,
        start_date: datetime,
        end_date: datetime,
        symbols: Optional[List[str]]
    ) -> List[Dict]:
        """
        Analyze what data is missing for backfill.
        Should be implemented by child classes.
        Returns list of missing data periods.
        """
        pass

    @abstractmethod
    async def _estimate_backfill_records(
        self,
        start_date: datetime,
        end_date: datetime,
        symbols: Optional[List[str]]
    ) -> int:
        """
        Estimate number of records that would be backfilled.
        Should be implemented by child classes.
        """
        pass

    async def run_collection_loop(self):
        """Main collection loop"""
        self.logger.info("collection_loop_started")
        
        # Mark service as ready to receive traffic
        self.startup_complete = True
        self.logger.info("service_startup_complete")
        
        while True:
            try:
                if not self.is_collecting:
                    task_id = str(uuid.uuid4())
                    await self._perform_collection(task_id)
                
                # Wait for next collection
                await asyncio.sleep(self.config.collection_interval)
                
            except asyncio.CancelledError:
                self.logger.info("collection_loop_cancelled")
                break
            except Exception as e:
                self.logger.error("collection_loop_error", error=str(e))
                await asyncio.sleep(60)  # Wait 1 minute on error

    async def _validate_data(self, data: dict) -> Dict[str, Any]:
        """Validate data using the data validator"""
        required_fields = await self._get_required_fields()
        
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Check required fields
        if not self.data_validator.validate_required_fields(data, required_fields):
            validation_result["is_valid"] = False
            validation_result["errors"].append("Missing required fields")
        
        # Check for duplicates if enabled
        if self.config.enable_duplicate_detection:
            data_hash = self.data_validator.generate_data_hash(data)
            if data_hash in self.duplicate_hashes:
                validation_result["warnings"].append("Potential duplicate data detected")
            else:
                self.duplicate_hashes.append(data_hash)
        
        return validation_result

    async def _generate_data_quality_report(self) -> DataQualityReport:
        """Generate comprehensive data quality report"""
        # This should be implemented by child classes
        return DataQualityReport(
            total_records=0,
            valid_records=0,
            invalid_records=0,
            duplicate_records=0,
            validation_errors=[],
            data_quality_score=100.0
        )

    async def _get_performance_metrics(self) -> PerformanceMetrics:
        """Get current performance metrics"""
        import psutil
        import os
        
        # Calculate averages from stored metrics
        avg_collection_time = sum(self.performance_metrics.get('collection_time', [0])) / max(len(self.performance_metrics.get('collection_time', [1])), 1)
        total_requests = self.collection_errors + len(self.performance_metrics.get('successful_collections', []))
        success_rate = (len(self.performance_metrics.get('successful_collections', [])) / max(total_requests, 1)) * 100
        error_rate = (self.collection_errors / max(total_requests, 1)) * 100
        
        # Get system metrics
        process = psutil.Process(os.getpid())
        memory_usage = process.memory_info().rss / 1024 / 1024  # MB
        cpu_usage = process.cpu_percent()
        
        return PerformanceMetrics(
            avg_collection_time=avg_collection_time,
            success_rate=success_rate,
            error_rate=error_rate,
            database_latency=sum(self.performance_metrics.get('db_latency', [0])) / max(len(self.performance_metrics.get('db_latency', [1])), 1),
            api_latency=sum(self.performance_metrics.get('api_latency', [0])) / max(len(self.performance_metrics.get('api_latency', [1])), 1),
            memory_usage_mb=memory_usage,
            cpu_usage_percent=cpu_usage
        )

    async def _send_alert(self, alert: AlertRequest):
        """Send alert notification via webhook"""
        if not self.config.alert_webhook_url:
            self.logger.warning("alert_webhook_not_configured")
            return
        
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "alert_type": alert.alert_type,
                    "severity": alert.severity,
                    "message": alert.message,
                    "service": alert.service,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "additional_data": alert.additional_data
                }
                
                async with session.post(self.config.alert_webhook_url, json=payload) as response:
                    if response.status == 200:
                        self.logger.info("alert_sent_successfully", alert_type=alert.alert_type)
                    else:
                        self.logger.error("alert_send_failed", status=response.status)
                        
        except Exception as e:
            self.logger.error("alert_send_error", error=str(e))

    def _signal_handler(self, signum, frame):
        """Handle graceful shutdown signals"""
        self.logger.info("shutdown_signal_received", signal=signum)
        self._shutdown_event.set()

    async def _get_required_fields(self) -> List[str]:
        """Get required fields for data validation. Should be implemented by child classes."""
        return []

    def run_server(self, host: str = "0.0.0.0", port: int = 8000):
        """Run the FastAPI server"""
        uvicorn.run(
            self.app,
            host=host,
            port=port,
            log_level=self.config.log_level.value if self.config.log_level != LogLevel.NONE else "critical"
        )