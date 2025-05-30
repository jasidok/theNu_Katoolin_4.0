#!/usr/bin/env python3

import os
import json
import time
import logging
from typing import Dict, Any, Optional, Union, List
from functools import wraps

class Cache:
    """
    A simple caching system for storing and retrieving data
    """
    def __init__(self, cache_dir: str = "/tmp/katoolin_cache", ttl: int = 3600):
        """
        Initialize the cache

        Args:
            cache_dir (str): Directory to store cache files
            ttl (int): Time to live in seconds (default: 1 hour)
        """
        self.cache_dir = cache_dir
        self.ttl = ttl
        self._ensure_cache_dir()
        logging.debug(f"Cache initialized with directory: {cache_dir} and TTL: {ttl} seconds")

    def _ensure_cache_dir(self) -> None:
        """Ensure the cache directory exists"""
        if not os.path.exists(self.cache_dir):
            try:
                os.makedirs(self.cache_dir)
                logging.debug(f"Created cache directory: {self.cache_dir}")
            except Exception as e:
                logging.warning(f"Failed to create cache directory: {str(e)}")
                # Fall back to a temporary directory
                self.cache_dir = "/tmp"
                logging.debug(f"Using fallback cache directory: {self.cache_dir}")

    def _get_cache_path(self, key: str) -> str:
        """
        Get the file path for a cache key

        Args:
            key (str): Cache key

        Returns:
            str: Path to the cache file
        """
        # Create a safe filename from the key
        safe_key = "".join(c if c.isalnum() else "_" for c in key)
        return os.path.join(self.cache_dir, f"{safe_key}.json")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from the cache

        Args:
            key (str): Cache key
            default (Any): Default value to return if key not found or expired

        Returns:
            Any: Cached value or default
        """
        cache_path = self._get_cache_path(key)
        
        if not os.path.exists(cache_path):
            logging.debug(f"Cache miss for key: {key} (file not found)")
            return default
        
        try:
            with open(cache_path, 'r') as f:
                cache_data = json.load(f)
            
            # Check if cache is expired
            if time.time() - cache_data.get('timestamp', 0) > self.ttl:
                logging.debug(f"Cache expired for key: {key}")
                return default
            
            logging.debug(f"Cache hit for key: {key}")
            return cache_data.get('value')
        except Exception as e:
            logging.warning(f"Error reading cache for key {key}: {str(e)}")
            return default

    def set(self, key: str, value: Any) -> bool:
        """
        Set a value in the cache

        Args:
            key (str): Cache key
            value (Any): Value to cache

        Returns:
            bool: True if successful, False otherwise
        """
        cache_path = self._get_cache_path(key)
        
        try:
            cache_data = {
                'timestamp': time.time(),
                'value': value
            }
            
            with open(cache_path, 'w') as f:
                json.dump(cache_data, f)
            
            logging.debug(f"Cached value for key: {key}")
            return True
        except Exception as e:
            logging.warning(f"Error writing cache for key {key}: {str(e)}")
            return False

    def delete(self, key: str) -> bool:
        """
        Delete a value from the cache

        Args:
            key (str): Cache key

        Returns:
            bool: True if successful, False otherwise
        """
        cache_path = self._get_cache_path(key)
        
        if not os.path.exists(cache_path):
            logging.debug(f"Cache key not found for deletion: {key}")
            return False
        
        try:
            os.remove(cache_path)
            logging.debug(f"Deleted cache for key: {key}")
            return True
        except Exception as e:
            logging.warning(f"Error deleting cache for key {key}: {str(e)}")
            return False

    def clear(self) -> bool:
        """
        Clear all cached values

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.json'):
                    os.remove(os.path.join(self.cache_dir, filename))
            
            logging.debug("Cleared all cache files")
            return True
        except Exception as e:
            logging.warning(f"Error clearing cache: {str(e)}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics

        Returns:
            Dict[str, Any]: Dictionary with cache statistics
        """
        try:
            files = [f for f in os.listdir(self.cache_dir) if f.endswith('.json')]
            total_size = sum(os.path.getsize(os.path.join(self.cache_dir, f)) for f in files)
            
            return {
                'entries': len(files),
                'size_bytes': total_size,
                'size_kb': round(total_size / 1024, 2),
                'directory': self.cache_dir,
                'ttl': self.ttl
            }
        except Exception as e:
            logging.warning(f"Error getting cache stats: {str(e)}")
            return {
                'entries': 0,
                'size_bytes': 0,
                'size_kb': 0,
                'directory': self.cache_dir,
                'ttl': self.ttl,
                'error': str(e)
            }

def cached(ttl: int = 3600, key_prefix: str = ""):
    """
    Decorator for caching function results

    Args:
        ttl (int): Time to live in seconds (default: 1 hour)
        key_prefix (str): Prefix for cache keys

    Returns:
        Callable: Decorated function
    """
    cache = Cache(ttl=ttl)
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create a cache key from the function name, args, and kwargs
            key_parts = [key_prefix, func.__name__]
            
            # Add args to key
            for arg in args:
                key_parts.append(str(arg))
            
            # Add kwargs to key (sorted for consistency)
            for k, v in sorted(kwargs.items()):
                key_parts.append(f"{k}={v}")
            
            cache_key = ":".join(key_parts)
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logging.debug(f"Using cached result for {func.__name__}")
                return cached_result
            
            # Call the function and cache the result
            result = func(*args, **kwargs)
            cache.set(cache_key, result)
            return result
        
        return wrapper
    
    return decorator

# Global cache instance for convenience
global_cache = Cache()