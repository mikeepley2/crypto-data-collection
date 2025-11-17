#!/usr/bin/env python3
"""
Premium CoinGecko API Rate Limiter and Usage Tracker

This module provides intelligent rate limiting for premium CoinGecko accounts,
usage tracking, and fallback mechanisms for sustainable data collection.

Features:
- Monthly usage tracking (500k requests/month)
- Per-minute rate limiting (300 requests/minute for premium)
- Intelligent fallback to alternative sources
- Usage monitoring and alerts
- Request prioritization for critical data
"""

import os
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, asdict
from pathlib import Path
import threading
from collections import deque
import requests

logger = logging.getLogger(__name__)

@dataclass
class UsageStats:
    """Track API usage statistics"""
    monthly_requests: int = 0
    daily_requests: int = 0
    requests_this_minute: int = 0
    last_reset_month: int = 0
    last_reset_day: int = 0
    last_reset_minute: int = 0
    total_fallback_requests: int = 0
    
class PremiumCoinGeckoRateLimiter:
    """Rate limiter for premium CoinGecko API with intelligent fallback"""
    
    def __init__(self):
        self.api_key = os.environ.get("COINGECKO_API_KEY", "")
        self.plan = os.environ.get("COINGECKO_PLAN", "premium").lower()  # Default to premium
        self.monthly_limit = int(os.environ.get("COINGECKO_MONTHLY_LIMIT", "500000"))  # Premium default
        self.requests_per_minute = int(os.environ.get("COINGECKO_REQUESTS_PER_MINUTE", "300"))  # Premium default
        
        # Usage tracking
        self.usage_file = Path("coingecko_usage.json")
        self.usage = self._load_usage()
        self.request_times = deque(maxlen=self.requests_per_minute)
        
        # Thread safety
        self.lock = threading.Lock()
        
        # Premium features
        self.premium_endpoints = {
            "pro": ["coins/{id}/history", "coins/{id}/market_chart/range", "coins/markets"],
            "premium": ["coins/{id}/history", "coins/{id}/market_chart", "global/market_cap_chart"],
            "demo": ["coins/{id}", "simple/price"]
        }
        
        logger.info(f"🚀 Initialized CoinGecko rate limiter - Plan: {self.plan}, Limit: {self.monthly_limit}/month")
    
    def _load_usage(self) -> UsageStats:
        """Load usage statistics from file"""
        try:
            if self.usage_file.exists():
                with open(self.usage_file, 'r') as f:
                    data = json.load(f)
                return UsageStats(**data)
        except Exception as e:
            logger.warning(f"Could not load usage stats: {e}")
        return UsageStats()
    
    def _save_usage(self):
        """Save usage statistics to file"""
        try:
            with open(self.usage_file, 'w') as f:
                json.dump(asdict(self.usage), f, indent=2)
        except Exception as e:
            logger.error(f"Could not save usage stats: {e}")
    
    def _reset_counters_if_needed(self):
        """Reset counters for new time periods"""
        now = datetime.now()
        
        # Reset monthly counter
        if now.month != self.usage.last_reset_month:
            self.usage.monthly_requests = 0
            self.usage.last_reset_month = now.month
            logger.info("📅 Monthly usage counter reset")
        
        # Reset daily counter  
        if now.day != self.usage.last_reset_day:
            self.usage.daily_requests = 0
            self.usage.last_reset_day = now.day
        
        # Reset minute counter
        if now.minute != self.usage.last_reset_minute:
            self.usage.requests_this_minute = 0
            self.usage.last_reset_minute = now.minute
    
    def can_make_request(self, priority: str = "normal") -> Dict[str, Any]:
        """Check if we can make a request without hitting limits"""
        with self.lock:
            self._reset_counters_if_needed()
            
            # Check monthly limit
            if self.usage.monthly_requests >= self.monthly_limit:
                return {
                    "allowed": False,
                    "reason": "monthly_limit_exceeded",
                    "remaining_monthly": 0,
                    "use_fallback": True
                }
            
            # Check per-minute limit
            now = time.time()
            # Remove requests older than 1 minute
            while self.request_times and now - self.request_times[0] > 60:
                self.request_times.popleft()
            
            if len(self.request_times) >= self.requests_per_minute:
                return {
                    "allowed": False,
                    "reason": "rate_limit_exceeded", 
                    "wait_seconds": 60 - (now - self.request_times[0]),
                    "use_fallback": priority == "low"
                }
            
            return {
                "allowed": True,
                "remaining_monthly": self.monthly_limit - self.usage.monthly_requests,
                "remaining_minute": self.requests_per_minute - len(self.request_times)
            }
    
    def record_request(self, success: bool = True):
        """Record a successful request"""
        with self.lock:
            self._reset_counters_if_needed()
            
            if success:
                self.usage.monthly_requests += 1
                self.usage.daily_requests += 1
                self.usage.requests_this_minute += 1
                self.request_times.append(time.time())
                
                # Log usage milestones
                if self.usage.monthly_requests % 10000 == 0:
                    percentage = (self.usage.monthly_requests / self.monthly_limit) * 100
                    logger.info(f"📊 CoinGecko Usage: {self.usage.monthly_requests:,}/{self.monthly_limit:,} ({percentage:.1f}%)")
                
                self._save_usage()
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics"""
        with self.lock:
            self._reset_counters_if_needed()
            return {
                "monthly_usage": {
                    "requests": self.usage.monthly_requests,
                    "limit": self.monthly_limit,
                    "percentage": (self.usage.monthly_requests / self.monthly_limit) * 100,
                    "remaining": self.monthly_limit - self.usage.monthly_requests
                },
                "daily_requests": self.usage.daily_requests,
                "requests_this_minute": len(self.request_times),
                "rate_limit": self.requests_per_minute,
                "fallback_requests": self.usage.total_fallback_requests,
                "plan": self.plan
            }
    
    def make_request_with_fallback(self, url: str, params: Dict[str, Any] = None, 
                                 priority: str = "normal", fallback_func: Optional[Callable] = None) -> Optional[requests.Response]:
        """Make a request with automatic fallback handling"""
        
        # Check if we can make the request
        check = self.can_make_request(priority)
        
        if not check["allowed"]:
            if check.get("use_fallback") and fallback_func:
                logger.info(f"🔄 Using fallback for {url} - Reason: {check['reason']}")
                self.usage.total_fallback_requests += 1
                return fallback_func()
            
            if check.get("wait_seconds"):
                logger.warning(f"⏱️ Rate limit hit, waiting {check['wait_seconds']:.1f}s")
                time.sleep(check["wait_seconds"])
                return self.make_request_with_fallback(url, params, priority, fallback_func)
            
            logger.error(f"❌ Cannot make request to {url}: {check['reason']}")
            return None
        
        # Make the request
        try:
            headers = {'User-Agent': 'CryptoML-Premium-Collector/1.0'}
            if self.api_key:
                headers['x-cg-pro-api-key'] = self.api_key
            
            response = requests.get(url, params=params or {}, headers=headers, timeout=30)
            
            # Record the request
            self.record_request(success=response.status_code == 200)
            
            if response.status_code == 429:  # Rate limited
                retry_after = int(response.headers.get('Retry-After', 60))
                logger.warning(f"⏱️ Rate limited by server, waiting {retry_after}s")
                time.sleep(retry_after)
                return self.make_request_with_fallback(url, params, priority, fallback_func)
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Request failed for {url}: {e}")
            self.record_request(success=False)
            
            # Try fallback if available
            if fallback_func:
                logger.info(f"🔄 Using fallback due to error")
                self.usage.total_fallback_requests += 1
                return fallback_func()
            
            return None
    
    def get_premium_endpoints(self) -> List[str]:
        """Get available endpoints for current plan"""
        return self.premium_endpoints.get(self.plan, self.premium_endpoints["demo"])
    
    def is_premium_endpoint_available(self, endpoint: str) -> bool:
        """Check if an endpoint is available for current plan"""
        available = self.get_premium_endpoints()
        return any(ep in endpoint for ep in available)

# Global rate limiter instance
rate_limiter = PremiumCoinGeckoRateLimiter()

def with_rate_limit(priority: str = "normal"):
    """Decorator for rate-limited API calls"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            check = rate_limiter.can_make_request(priority)
            if not check["allowed"]:
                logger.warning(f"Rate limit check failed for {func.__name__}: {check}")
                return None
            
            result = func(*args, **kwargs)
            rate_limiter.record_request(success=result is not None)
            return result
        return wrapper
    return decorator
