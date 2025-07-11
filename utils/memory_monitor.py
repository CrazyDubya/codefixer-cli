"""
Memory monitoring and optimization utilities for CodeFixer.
"""

import psutil
import gc
import logging
from typing import Optional, Callable
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class MemoryMonitor:
    """Monitor and manage memory usage."""
    
    def __init__(self, warning_threshold_mb: int = 500, critical_threshold_mb: int = 1000):
        self.warning_threshold = warning_threshold_mb * 1024 * 1024  # Convert to bytes
        self.critical_threshold = critical_threshold_mb * 1024 * 1024
        self.process = psutil.Process()
    
    def get_memory_usage(self) -> int:
        """Get current memory usage in bytes."""
        try:
            return self.process.memory_info().rss
        except Exception as e:
            logger.warning(f"Failed to get memory usage: {e}")
            return 0
    
    def get_memory_usage_mb(self) -> float:
        """Get current memory usage in MB."""
        return self.get_memory_usage() / (1024 * 1024)
    
    def check_memory_usage(self) -> str:
        """Check memory usage and return status."""
        usage = self.get_memory_usage()
        
        if usage > self.critical_threshold:
            return "critical"
        elif usage > self.warning_threshold:
            return "warning"
        else:
            return "normal"
    
    def log_memory_usage(self, context: str = ""):
        """Log current memory usage."""
        usage_mb = self.get_memory_usage_mb()
        status = self.check_memory_usage()
        
        if context:
            logger.info(f"Memory usage ({context}): {usage_mb:.1f} MB ({status})")
        else:
            logger.info(f"Memory usage: {usage_mb:.1f} MB ({status})")
        
        if status == "critical":
            logger.warning("Memory usage is critical, consider cleanup")
    
    def force_cleanup(self):
        """Force garbage collection and memory cleanup."""
        logger.info("Forcing memory cleanup...")
        
        # Force garbage collection
        collected = gc.collect()
        logger.info(f"Garbage collection freed {collected} objects")
        
        # Log memory after cleanup
        self.log_memory_usage("after cleanup")
    
    @contextmanager
    def monitor_memory(self, context: str = ""):
        """Context manager to monitor memory usage."""
        initial_usage = self.get_memory_usage_mb()
        
        try:
            yield
        finally:
            final_usage = self.get_memory_usage_mb()
            difference = final_usage - initial_usage
            
            if context:
                logger.info(f"Memory change ({context}): {difference:+.1f} MB")
            else:
                logger.info(f"Memory change: {difference:+.1f} MB")
            
            # Force cleanup if memory increased significantly
            if difference > 100:  # More than 100MB increase
                logger.info("Significant memory increase detected, forcing cleanup")
                self.force_cleanup()

# Global instance
memory_monitor = MemoryMonitor()

def optimize_memory_usage():
    """Optimize memory usage by cleaning up caches and forcing GC."""
    logger.info("Optimizing memory usage...")
    
    # Force garbage collection
    gc.collect()
    
    # Clear any module-level caches
    import sys
    for module_name in list(sys.modules.keys()):
        if module_name.startswith('codefixer') or module_name.startswith('linters'):
            module = sys.modules[module_name]
            if hasattr(module, '_cache'):
                module._cache.clear()
    
    # Log memory after optimization
    memory_monitor.log_memory_usage("after optimization")

def memory_efficient_operation(operation: Callable, *args, **kwargs):
    """Execute an operation with memory monitoring and cleanup."""
    with memory_monitor.monitor_memory("operation"):
        result = operation(*args, **kwargs)
        
        # Check if cleanup is needed
        if memory_monitor.check_memory_usage() == "critical":
            memory_monitor.force_cleanup()
        
        return result 