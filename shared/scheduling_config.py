#!/usr/bin/env python3
"""
Centralized Scheduling Configuration
Single source of truth for all data collection frequencies, gap monitoring, and backfill settings
"""

import os
from typing import Dict, Any, Optional
from datetime import timedelta

# ==============================================================================
# MASTER SCHEDULING REGISTRY
# ==============================================================================

# Core collector scheduling configuration
COLLECTOR_SCHEDULES = {
    "onchain": {
        "frequency_hours": 6,
        "frequency_minutes": 360,
        "schedule_type": "hours",
        "schedule_value": 6,
        "description": "Blockchain metrics - slow changing data",
        "gap_tolerance_hours": 8,
        "auto_backfill": True,
        "priority": "medium",
        "max_backfill_days": 30
    },
    "technical": {
        "frequency_hours": 5/60,  # 5 minutes
        "frequency_minutes": 5,
        "schedule_type": "minutes", 
        "schedule_value": 5,
        "description": "Technical indicators - real-time price analysis",
        "gap_tolerance_hours": 0.25,  # 15 minutes
        "auto_backfill": True,
        "priority": "high",
        "max_backfill_days": 7
    },
    "macro": {
        "frequency_hours": 1,
        "frequency_minutes": 60,
        "schedule_type": "hours",
        "schedule_value": 1,
        "description": "Macroeconomic indicators - hourly updates",
        "gap_tolerance_hours": 2,
        "auto_backfill": True,
        "priority": "medium",
        "max_backfill_days": 90
    },
    "news": {
        "frequency_hours": 15/60,  # 15 minutes
        "frequency_minutes": 15,
        "schedule_type": "minutes",
        "schedule_value": 15,
        "description": "Crypto news collection - moderate flow",
        "gap_tolerance_hours": 1,
        "auto_backfill": True,
        "priority": "medium",
        "max_backfill_days": 14
    },
    "ohlc": {
        "frequency_hours": 24,
        "frequency_minutes": 1440,
        "schedule_type": "daily",
        "schedule_value": "02:00",  # 2 AM UTC
        "description": "OHLC daily candles - end of day processing",
        "gap_tolerance_hours": 26,
        "auto_backfill": True,
        "priority": "high",
        "max_backfill_days": 30
    },
    "sentiment": {
        "frequency_hours": 15/60,  # 15 minutes
        "frequency_minutes": 15,
        "schedule_type": "minutes",
        "schedule_value": 15,
        "description": "Sentiment analysis - tied to news flow",
        "gap_tolerance_hours": 1,
        "auto_backfill": True,
        "priority": "medium",
        "max_backfill_days": 7
    },
    "price": {
        "frequency_hours": 5/60,  # 5 minutes
        "frequency_minutes": 5,
        "schedule_type": "minutes",
        "schedule_value": 5,
        "description": "Real-time price data - high frequency",
        "gap_tolerance_hours": 0.25,  # 15 minutes
        "auto_backfill": True,
        "priority": "critical",
        "max_backfill_days": 3
    }
}

# ==============================================================================
# GAP MONITORING CONFIGURATION
# ==============================================================================

GAP_MONITORING = {
    "enabled": True,
    "check_interval_minutes": 5,  # How often to check for gaps
    "alert_thresholds": {
        "critical": 0.5,  # 30 minutes
        "warning": 0.25,   # 15 minutes
        "info": 0.1        # 6 minutes
    },
    "auto_backfill_triggers": {
        "immediate": ["price", "technical"],  # Backfill immediately
        "scheduled": ["onchain", "macro", "news", "sentiment", "ohlc"]  # Backfill on schedule
    },
    "max_concurrent_backfills": 3,
    "backfill_batch_size": 100
}

# ==============================================================================
# RATE LIMITING CONFIGURATION
# ==============================================================================

RATE_LIMITS = {
    "coingecko_premium": {
        "calls_per_minute": 500,
        "calls_per_month": 500000,
        "delay_between_calls": 0.120,  # 120ms for 500/min
        "burst_allowance": 10
    },
    "fred_api": {
        "calls_per_minute": 120,
        "calls_per_day": 1000,
        "delay_between_calls": 0.5
    },
    "news_apis": {
        "calls_per_minute": 60,
        "delay_between_calls": 1.0
    }
}

# ==============================================================================
# ENVIRONMENT OVERRIDES
# ==============================================================================

def get_env_override(collector_name: str, setting: str) -> Optional[Any]:
    """Get environment variable override for collector setting"""
    env_key = f"{collector_name.upper()}_{setting.upper()}"
    
    # Special handling for different setting types
    if setting in ["frequency_hours", "gap_tolerance_hours"]:
        return float(os.getenv(env_key)) if os.getenv(env_key) else None
    elif setting in ["frequency_minutes", "schedule_value", "max_backfill_days"]:
        return int(os.getenv(env_key)) if os.getenv(env_key) else None
    elif setting == "auto_backfill":
        return os.getenv(env_key, "").lower() in ["true", "1", "yes"] if os.getenv(env_key) else None
    else:
        return os.getenv(env_key)

# ==============================================================================
# CONFIGURATION ACCESS FUNCTIONS
# ==============================================================================

def get_collector_schedule(collector_name: str) -> Dict[str, Any]:
    """Get scheduling configuration for a specific collector with environment overrides"""
    if collector_name not in COLLECTOR_SCHEDULES:
        raise ValueError(f"Unknown collector: {collector_name}")
    
    config = COLLECTOR_SCHEDULES[collector_name].copy()
    
    # Apply environment overrides
    for setting in config.keys():
        env_override = get_env_override(collector_name, setting)
        if env_override is not None:
            config[setting] = env_override
    
    return config

def get_all_schedules() -> Dict[str, Dict[str, Any]]:
    """Get all collector schedules with environment overrides applied"""
    return {name: get_collector_schedule(name) for name in COLLECTOR_SCHEDULES.keys()}

def get_frequency_minutes(collector_name: str) -> float:
    """Get collection frequency in minutes for a collector"""
    config = get_collector_schedule(collector_name)
    return config["frequency_minutes"]

def get_frequency_hours(collector_name: str) -> float:
    """Get collection frequency in hours for a collector"""
    config = get_collector_schedule(collector_name)
    return config["frequency_hours"]

def get_gap_tolerance(collector_name: str) -> float:
    """Get gap tolerance in hours for a collector"""
    config = get_collector_schedule(collector_name)
    return config["gap_tolerance_hours"]

def should_auto_backfill(collector_name: str) -> bool:
    """Check if collector should automatically backfill gaps"""
    config = get_collector_schedule(collector_name)
    return config["auto_backfill"]

def get_max_backfill_days(collector_name: str) -> int:
    """Get maximum days to backfill for a collector"""
    config = get_collector_schedule(collector_name)
    return config["max_backfill_days"]

def get_schedule_expression(collector_name: str) -> str:
    """Get schedule expression for Python schedule library"""
    config = get_collector_schedule(collector_name)
    
    if config["schedule_type"] == "minutes":
        return f"schedule.every({config['schedule_value']}).minutes"
    elif config["schedule_type"] == "hours":
        return f"schedule.every({config['schedule_value']}).hours"
    elif config["schedule_type"] == "daily":
        return f"schedule.every().day.at('{config['schedule_value']}')"
    else:
        raise ValueError(f"Unknown schedule type: {config['schedule_type']}")

# ==============================================================================
# GAP MONITORING FUNCTIONS
# ==============================================================================

def get_gap_monitoring_config() -> Dict[str, Any]:
    """Get gap monitoring configuration"""
    return GAP_MONITORING.copy()

def is_gap_critical(collector_name: str, gap_hours: float) -> bool:
    """Check if a gap is critical for a collector"""
    tolerance = get_gap_tolerance(collector_name)
    return gap_hours > tolerance

def get_backfill_priority(collector_name: str) -> str:
    """Get backfill priority for a collector"""
    config = get_collector_schedule(collector_name)
    return config["priority"]

# ==============================================================================
# RATE LIMITING FUNCTIONS
# ==============================================================================

def get_rate_limit_config(api_name: str) -> Dict[str, Any]:
    """Get rate limiting configuration for an API"""
    if api_name not in RATE_LIMITS:
        raise ValueError(f"Unknown API: {api_name}")
    return RATE_LIMITS[api_name].copy()

def get_api_delay(api_name: str) -> float:
    """Get delay between API calls"""
    config = get_rate_limit_config(api_name)
    return config["delay_between_calls"]

# ==============================================================================
# VALIDATION FUNCTIONS
# ==============================================================================

def validate_collector_config(collector_name: str) -> Dict[str, Any]:
    """Validate collector configuration and return status"""
    try:
        config = get_collector_schedule(collector_name)
        
        validation = {
            "collector": collector_name,
            "valid": True,
            "config": config,
            "warnings": [],
            "errors": []
        }
        
        # Validate frequency
        if config["frequency_minutes"] < 1:
            validation["warnings"].append("Very high frequency (< 1 minute) may cause rate limiting")
        
        if config["frequency_hours"] > 24:
            validation["warnings"].append("Very low frequency (> 24 hours) may cause stale data")
        
        # Validate gap tolerance
        if config["gap_tolerance_hours"] < config["frequency_hours"]:
            validation["errors"].append("Gap tolerance should be >= frequency")
            validation["valid"] = False
        
        return validation
        
    except Exception as e:
        return {
            "collector": collector_name,
            "valid": False,
            "config": None,
            "warnings": [],
            "errors": [str(e)]
        }

def validate_all_configs() -> Dict[str, Dict[str, Any]]:
    """Validate all collector configurations"""
    return {name: validate_collector_config(name) for name in COLLECTOR_SCHEDULES.keys()}

# ==============================================================================
# UTILITY FUNCTIONS
# ==============================================================================

def list_collectors() -> list:
    """List all configured collectors"""
    return list(COLLECTOR_SCHEDULES.keys())

def get_schedule_summary() -> Dict[str, str]:
    """Get human-readable schedule summary"""
    summary = {}
    for name in COLLECTOR_SCHEDULES.keys():
        config = get_collector_schedule(name)
        if config["schedule_type"] == "minutes":
            summary[name] = f"Every {config['schedule_value']} minutes"
        elif config["schedule_type"] == "hours":
            summary[name] = f"Every {config['schedule_value']} hours"
        elif config["schedule_type"] == "daily":
            summary[name] = f"Daily at {config['schedule_value']}"
    return summary

# ==============================================================================
# INTEGRATION HELPERS
# ==============================================================================

def create_schedule_for_collector(collector_name: str, schedule_module, collection_function):
    """Create schedule using Python schedule library"""
    config = get_collector_schedule(collector_name)
    
    if config["schedule_type"] == "minutes":
        return schedule_module.every(config["schedule_value"]).minutes.do(collection_function)
    elif config["schedule_type"] == "hours":
        return schedule_module.every(config["schedule_value"]).hours.do(collection_function)
    elif config["schedule_type"] == "daily":
        return schedule_module.every().day.at(config["schedule_value"]).do(collection_function)
    else:
        raise ValueError(f"Unknown schedule type: {config['schedule_type']}")

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================

if __name__ == "__main__":
    print("📅 CENTRALIZED SCHEDULING CONFIGURATION")
    print("=" * 60)
    
    print(f"\n🔧 Configured Collectors ({len(list_collectors())}):")
    for name in list_collectors():
        config = get_collector_schedule(name)
        print(f"   {name:12} | {config['description']}")
    
    print(f"\n⏰ Schedule Summary:")
    for name, schedule in get_schedule_summary().items():
        print(f"   {name:12} | {schedule}")
    
    print(f"\n🔍 Gap Monitoring:")
    gap_config = get_gap_monitoring_config()
    print(f"   Enabled: {gap_config['enabled']}")
    print(f"   Check Interval: {gap_config['check_interval_minutes']} minutes")
    print(f"   Auto-backfill: {len(gap_config['auto_backfill_triggers']['immediate'])} immediate, {len(gap_config['auto_backfill_triggers']['scheduled'])} scheduled")
    
    print(f"\n✅ Validation Results:")
    validations = validate_all_configs()
    for name, validation in validations.items():
        status = "✅" if validation["valid"] else "❌"
        print(f"   {status} {name:12} | {'Valid' if validation['valid'] else 'Invalid'}")
        if validation["warnings"]:
            for warning in validation["warnings"]:
                print(f"      ⚠️  {warning}")
        if validation["errors"]:
            for error in validation["errors"]:
                print(f"      ❌ {error}")