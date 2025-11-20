"""
Test package for crypto-data-collection project.

This module provides test utilities and base classes for testing
the various components of the crypto data collection system.
"""

__version__ = "1.0.0"

# Import common test utilities
from .test_base_collector import BaseCollectorTestCase

__all__ = [
    "BaseCollectorTestCase",
]