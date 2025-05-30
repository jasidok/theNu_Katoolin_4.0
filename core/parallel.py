#!/usr/bin/env python3

import os
import time
import logging
import threading
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from typing import List, Dict, Any, Callable, Optional, Tuple, Union, TypeVar

# Type variable for generic function return type
T = TypeVar('T')

class ParallelExecutor:
    """
    Class for executing tasks in parallel using threading or multiprocessing
    """
    def __init__(self, max_workers: Optional[int] = None, use_processes: bool = False):
        """
        Initialize the parallel executor

        Args:
            max_workers (Optional[int]): Maximum number of workers (threads or processes)
                If None, defaults to number of CPU cores for processes or 5x that for threads
            use_processes (bool): Whether to use processes instead of threads
                Use processes for CPU-bound tasks, threads for I/O-bound tasks
        """
        self.use_processes = use_processes
        
        # Determine the number of workers
        if max_workers is None:
            cpu_count = os.cpu_count() or 4
            self.max_workers = cpu_count if use_processes else cpu_count * 5
        else:
            self.max_workers = max_workers
        
        logging.debug(f"Initialized ParallelExecutor with {self.max_workers} workers "
                     f"using {'processes' if use_processes else 'threads'}")

    def map(self, func: Callable[..., T], items: List[Any], *args, **kwargs) -> List[T]:
        """
        Apply a function to each item in a list in parallel

        Args:
            func (Callable): Function to apply to each item
            items (List[Any]): List of items to process
            *args: Additional positional arguments to pass to the function
            **kwargs: Additional keyword arguments to pass to the function

        Returns:
            List[T]: List of results
        """
        if not items:
            logging.debug("No items to process in parallel")
            return []
        
        logging.debug(f"Processing {len(items)} items in parallel with "
                     f"{'processes' if self.use_processes else 'threads'}")
        
        # Create a wrapper function that applies the additional args and kwargs
        def wrapper(item):
            return func(item, *args, **kwargs)
        
        # Choose the appropriate executor based on the use_processes flag
        executor_class = ProcessPoolExecutor if self.use_processes else ThreadPoolExecutor
        
        results = []
        with executor_class(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_item = {executor.submit(wrapper, item): item for item in items}
            
            # Process results as they complete
            for future in as_completed(future_to_item):
                item = future_to_item[future]
                try:
                    result = future.result()
                    results.append(result)
                    logging.debug(f"Completed parallel task for item: {item}")
                except Exception as e:
                    logging.error(f"Error in parallel task for item {item}: {str(e)}")
                    # Re-raise the exception to be handled by the caller
                    raise
        
        return results

    def execute(self, tasks: List[Tuple[Callable[..., T], List[Any], Dict[str, Any]]]) -> List[T]:
        """
        Execute a list of tasks in parallel

        Args:
            tasks (List[Tuple[Callable, List, Dict]]): List of (function, args, kwargs) tuples

        Returns:
            List[T]: List of results
        """
        if not tasks:
            logging.debug("No tasks to execute in parallel")
            return []
        
        logging.debug(f"Executing {len(tasks)} tasks in parallel with "
                     f"{'processes' if self.use_processes else 'threads'}")
        
        # Choose the appropriate executor based on the use_processes flag
        executor_class = ProcessPoolExecutor if self.use_processes else ThreadPoolExecutor
        
        results = []
        with executor_class(max_workers=self.max_workers) as executor:
            # Submit all tasks
            futures = []
            for func, args, kwargs in tasks:
                futures.append(executor.submit(func, *args, **kwargs))
            
            # Process results as they complete
            for i, future in enumerate(as_completed(futures)):
                try:
                    result = future.result()
                    results.append(result)
                    logging.debug(f"Completed parallel task {i+1}/{len(tasks)}")
                except Exception as e:
                    logging.error(f"Error in parallel task {i+1}/{len(tasks)}: {str(e)}")
                    # Re-raise the exception to be handled by the caller
                    raise
        
        return results

# Convenience functions for common parallel operations

def parallel_map(func: Callable[..., T], items: List[Any], 
                max_workers: Optional[int] = None, use_processes: bool = False, 
                *args, **kwargs) -> List[T]:
    """
    Apply a function to each item in a list in parallel

    Args:
        func (Callable): Function to apply to each item
        items (List[Any]): List of items to process
        max_workers (Optional[int]): Maximum number of workers
        use_processes (bool): Whether to use processes instead of threads
        *args: Additional positional arguments to pass to the function
        **kwargs: Additional keyword arguments to pass to the function

    Returns:
        List[T]: List of results
    """
    executor = ParallelExecutor(max_workers=max_workers, use_processes=use_processes)
    return executor.map(func, items, *args, **kwargs)

def parallel_execute(tasks: List[Tuple[Callable[..., T], List[Any], Dict[str, Any]]],
                    max_workers: Optional[int] = None, use_processes: bool = False) -> List[T]:
    """
    Execute a list of tasks in parallel

    Args:
        tasks (List[Tuple[Callable, List, Dict]]): List of (function, args, kwargs) tuples
        max_workers (Optional[int]): Maximum number of workers
        use_processes (bool): Whether to use processes instead of threads

    Returns:
        List[T]: List of results
    """
    executor = ParallelExecutor(max_workers=max_workers, use_processes=use_processes)
    return executor.execute(tasks)

# Decorator for parallel execution
def parallel(max_workers: Optional[int] = None, use_processes: bool = False):
    """
    Decorator for executing a function in parallel for each item in the first argument

    Args:
        max_workers (Optional[int]): Maximum number of workers
        use_processes (bool): Whether to use processes instead of threads

    Returns:
        Callable: Decorated function
    """
    def decorator(func):
        def wrapper(items, *args, **kwargs):
            if not isinstance(items, list):
                # If the first argument is not a list, just call the function normally
                return func(items, *args, **kwargs)
            
            # Create a parallel executor
            executor = ParallelExecutor(max_workers=max_workers, use_processes=use_processes)
            
            # Apply the function to each item in parallel
            return executor.map(func, items, *args, **kwargs)
        
        return wrapper
    
    return decorator