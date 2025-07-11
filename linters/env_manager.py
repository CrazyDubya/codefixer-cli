"""
Environment manager for CodeFixer linters.
Manages temporary environments with proper cleanup and lifecycle.
"""

import os
import shutil
import hashlib
import time
import threading
from pathlib import Path
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class EnvManager:
    """Manages temporary linter environments with cleanup."""
    
    def __init__(self, base_temp_dir: Optional[Path] = None):
        if base_temp_dir is None:
            # Use system temp dir with codefixer prefix
            import tempfile
            base_temp_dir = Path(tempfile.gettempdir()) / "codefixer"
        
        self.base_temp_dir = base_temp_dir
        self.base_temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache for environment paths to avoid repeated hash calculations
        self._env_cache: Dict[str, Path] = {}
        
        # Cleanup scheduling
        self._cleanup_thread = None
        self._stop_cleanup = threading.Event()
        
        # Cleanup old environments on startup
        self._cleanup_old_environments()
        
        # Start background cleanup thread
        self._start_cleanup_scheduler()
    
    def get_env_path(self, language: str, repo_hash: str) -> Path:
        """Get environment path for a specific language and repo."""
        return self.base_temp_dir / f"{language}_{repo_hash}"
    
    def _get_repo_hash(self, repo_path: Path) -> str:
        """Generate a hash for the repo path."""
        # Use a faster hash function for better performance
        path_str = str(repo_path.absolute())
        return hashlib.sha1(path_str.encode()).hexdigest()[:8]
    
    def _cleanup_old_environments(self, max_age_hours: int = 24):
        """Clean up environments older than max_age_hours."""
        try:
            current_time = time.time()
            for env_dir in self.base_temp_dir.iterdir():
                if not env_dir.is_dir():
                    continue
                
                # Check if directory is old
                if current_time - env_dir.stat().st_mtime > (max_age_hours * 3600):
                    logger.debug(f"Cleaning up old environment: {env_dir}")
                    shutil.rmtree(env_dir, ignore_errors=True)
        except Exception as e:
            logger.warning(f"Failed to cleanup old environments: {e}")
    
    def _start_cleanup_scheduler(self):
        """Start background cleanup scheduler."""
        def cleanup_worker():
            while not self._stop_cleanup.wait(3600):  # Run every hour
                try:
                    self._cleanup_old_environments()
                except Exception as e:
                    logger.warning(f"Background cleanup failed: {e}")
        
        self._cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        self._cleanup_thread.start()
        logger.debug("Started background cleanup scheduler")
    
    def stop_cleanup_scheduler(self):
        """Stop the background cleanup scheduler."""
        if self._cleanup_thread:
            self._stop_cleanup.set()
            self._cleanup_thread.join(timeout=5)
            logger.debug("Stopped background cleanup scheduler")
    
    def cleanup_all(self):
        """Clean up all environments."""
        try:
            if self.base_temp_dir.exists():
                shutil.rmtree(self.base_temp_dir)
                logger.info("Cleaned up all temporary environments")
        except Exception as e:
            logger.error(f"Failed to cleanup environments: {e}")
    
    def get_language_env(self, language: str, repo_path: Path) -> Path:
        """Get or create environment for a language in a repo."""
        # Use cache to avoid repeated hash calculations
        cache_key = f"{language}_{repo_path.absolute()}"
        if cache_key in self._env_cache:
            env_path = self._env_cache[cache_key]
            # Touch the directory to update timestamp
            env_path.mkdir(parents=True, exist_ok=True)
            env_path.touch()
            return env_path
        
        repo_hash = self._get_repo_hash(repo_path)
        env_path = self.get_env_path(language, repo_hash)
        
        # Touch the directory to update timestamp
        env_path.mkdir(parents=True, exist_ok=True)
        env_path.touch()
        
        # Cache the result
        self._env_cache[cache_key] = env_path
        
        return env_path

# Global instance
env_manager = EnvManager() 