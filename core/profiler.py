#!/usr/bin/env python3

import time
import logging
import functools
import cProfile
import pstats
import io
from typing import Dict, List, Callable, Any, Optional, Union

class Profiler:
    """
    A simple profiler for measuring execution time and identifying bottlenecks
    """
    def __init__(self):
        self.timings = {}
        self.call_counts = {}
        self.detailed_profiling = False
        self.profiler = None
        logging.debug("Profiler initialized")

    def start_detailed_profiling(self):
        """Start detailed profiling using cProfile"""
        self.detailed_profiling = True
        self.profiler = cProfile.Profile()
        self.profiler.enable()
        logging.debug("Detailed profiling started")

    def stop_detailed_profiling(self) -> str:
        """
        Stop detailed profiling and return the results

        Returns:
            str: Profiling results as a string
        """
        if not self.detailed_profiling or not self.profiler:
            logging.warning("Detailed profiling was not started")
            return "Detailed profiling was not started"

        self.profiler.disable()
        self.detailed_profiling = False

        # Capture profiling results
        s = io.StringIO()
        ps = pstats.Stats(self.profiler, stream=s).sort_stats('cumulative')
        ps.print_stats(30)  # Print top 30 functions by cumulative time
        
        logging.debug("Detailed profiling stopped")
        return s.getvalue()

    def time_function(self, func_name: str, func: Callable, *args, **kwargs) -> Any:
        """
        Time the execution of a function

        Args:
            func_name (str): Name of the function for logging
            func (Callable): Function to time
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function

        Returns:
            Any: Result of the function
        """
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Update timings and call counts
        if func_name not in self.timings:
            self.timings[func_name] = []
            self.call_counts[func_name] = 0
        
        self.timings[func_name].append(execution_time)
        self.call_counts[func_name] += 1
        
        logging.debug(f"Function {func_name} executed in {execution_time:.4f} seconds")
        return result

    def get_stats(self) -> Dict[str, Any]:
        """
        Get profiling statistics

        Returns:
            Dict[str, Any]: Dictionary with profiling statistics
        """
        stats = {}
        
        for func_name, times in self.timings.items():
            avg_time = sum(times) / len(times) if times else 0
            total_time = sum(times)
            call_count = self.call_counts.get(func_name, 0)
            
            stats[func_name] = {
                'avg_time': avg_time,
                'total_time': total_time,
                'call_count': call_count,
                'min_time': min(times) if times else 0,
                'max_time': max(times) if times else 0
            }
        
        return stats

    def print_stats(self) -> str:
        """
        Format and print profiling statistics

        Returns:
            str: Formatted statistics as a string
        """
        stats = self.get_stats()
        
        if not stats:
            return "No profiling data available"
        
        # Sort functions by total time (descending)
        sorted_funcs = sorted(stats.keys(), key=lambda x: stats[x]['total_time'], reverse=True)
        
        result = "Profiling Statistics:\n"
        result += "-" * 80 + "\n"
        result += f"{'Function':<30} {'Calls':<10} {'Total (s)':<15} {'Avg (s)':<15} {'Min (s)':<15} {'Max (s)':<15}\n"
        result += "-" * 80 + "\n"
        
        for func_name in sorted_funcs:
            func_stats = stats[func_name]
            result += f"{func_name:<30} {func_stats['call_count']:<10} {func_stats['total_time']:<15.4f} "
            result += f"{func_stats['avg_time']:<15.4f} {func_stats['min_time']:<15.4f} {func_stats['max_time']:<15.4f}\n"
        
        return result

    def reset(self):
        """Reset all profiling data"""
        self.timings = {}
        self.call_counts = {}
        logging.debug("Profiler reset")

def profile(func=None, *, name=None):
    """
    Decorator for profiling functions

    Args:
        func (Callable, optional): Function to decorate
        name (str, optional): Custom name for the function in profiling data

    Returns:
        Callable: Decorated function
    """
    def decorator(f):
        func_name = name or f.__qualname__
        
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            return global_profiler.time_function(func_name, f, *args, **kwargs)
        
        return wrapper
    
    if func is None:
        return decorator
    return decorator(func)

# Global profiler instance for convenience
global_profiler = Profiler()