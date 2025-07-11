"""
Subprocess pool for efficient subprocess management.
"""

import subprocess
import threading
import queue
import time
from typing import List, Dict, Any, Callable, Optional
import logging

logger = logging.getLogger(__name__)

class SubprocessPool:
    """Pool for managing subprocess execution with timeout and retry."""
    
    def __init__(self, max_workers: int = 4, timeout: int = 30):
        self.max_workers = max_workers
        self.timeout = timeout
        self._queue = queue.Queue()
        self._workers = []
        self._stop_event = threading.Event()
        self._start_workers()
    
    def _start_workers(self):
        """Start worker threads."""
        for i in range(self.max_workers):
            worker = threading.Thread(target=self._worker, daemon=True)
            worker.start()
            self._workers.append(worker)
    
    def _worker(self):
        """Worker thread function."""
        while not self._stop_event.is_set():
            try:
                task = self._queue.get(timeout=1)
                if task is None:
                    break
                
                func, args, kwargs, result_queue = task
                try:
                    result = func(*args, **kwargs)
                    result_queue.put(('success', result))
                except Exception as e:
                    result_queue.put(('error', e))
                finally:
                    self._queue.task_done()
            except queue.Empty:
                continue
    
    def submit(self, func: Callable, *args, **kwargs) -> queue.Queue:
        """Submit a task to the pool."""
        result_queue = queue.Queue()
        self._queue.put((func, args, kwargs, result_queue))
        return result_queue
    
    def shutdown(self, wait: bool = True):
        """Shutdown the pool."""
        self._stop_event.set()
        
        # Send None to all workers to stop them
        for _ in self._workers:
            self._queue.put(None)
        
        if wait:
            for worker in self._workers:
                worker.join()

def run_subprocess_with_timeout(cmd: List[str], timeout: int = 30, 
                               capture_output: bool = True, 
                               text: bool = True) -> subprocess.CompletedProcess:
    """
    Run subprocess with timeout and better error handling.
    
    Args:
        cmd: Command to run
        timeout: Timeout in seconds
        capture_output: Whether to capture output
        text: Whether to use text mode
        
    Returns:
        CompletedProcess result
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=capture_output,
            text=text,
            timeout=timeout,
            check=False  # Don't raise on non-zero exit codes
        )
        return result
    except subprocess.TimeoutExpired:
        logger.warning(f"Subprocess timed out after {timeout}s: {' '.join(cmd)}")
        # Return a mock result for timeout
        return subprocess.CompletedProcess(
            cmd, -1, "", f"Command timed out after {timeout} seconds"
        )
    except FileNotFoundError:
        logger.error(f"Command not found: {cmd[0]}")
        return subprocess.CompletedProcess(
            cmd, -1, "", f"Command not found: {cmd[0]}"
        )
    except Exception as e:
        logger.error(f"Subprocess error: {e}")
        return subprocess.CompletedProcess(
            cmd, -1, "", str(e)
        )

def run_subprocess_batch(commands: List[List[str]], 
                        max_workers: int = 4,
                        timeout: int = 30) -> List[subprocess.CompletedProcess]:
    """
    Run multiple subprocess commands in parallel.
    
    Args:
        commands: List of commands to run
        max_workers: Maximum number of parallel workers
        timeout: Timeout per command
        
    Returns:
        List of CompletedProcess results
    """
    if not commands:
        return []
    
    if len(commands) == 1:
        return [run_subprocess_with_timeout(commands[0], timeout)]
    
    # Use ThreadPoolExecutor for I/O bound subprocess operations
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    results = [None] * len(commands)
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all commands
        future_to_index = {
            executor.submit(run_subprocess_with_timeout, cmd, timeout): i 
            for i, cmd in enumerate(commands)
        }
        
        # Collect results
        for future in as_completed(future_to_index):
            index = future_to_index[future]
            try:
                results[index] = future.result()
            except Exception as e:
                logger.error(f"Error in subprocess batch: {e}")
                results[index] = subprocess.CompletedProcess(
                    commands[index], -1, "", str(e)
                )
    
    return results

# Global subprocess pool
subprocess_pool = SubprocessPool() 