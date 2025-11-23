"""
Configuration Management Module

Centralized, type-safe configuration with environment variable support.
"""

from .settings import VesselsConfig, get_config, load_config

__all__ = ['VesselsConfig', 'get_config', 'load_config']
