"""
Environment manager for CodeFixer linters.
Manages temporary environments with proper cleanup and lifecycle.
"""

import os
import shutil
import hashlib
import time
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
        
        # Cleanup old environments on startup
        self._cleanup_old_environments()
    
    def get_env_path(self, language: str, repo_hash: str) -> Path:
        """Get environment path for a specific language and repo."""
        return self.base_temp_dir / f"{language}_{repo_hash}"
    
    def _get_repo_hash(self, repo_path: Path) -> str:
        """Generate a hash for the repo path."""
        return hashlib.md5(str(repo_path.absolute()).encode()).hexdigest()[:8]
    
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
        repo_hash = self._get_repo_hash(repo_path)
        env_path = self.get_env_path(language, repo_hash)
        
        # Touch the directory to update timestamp
        env_path.mkdir(parents=True, exist_ok=True)
        env_path.touch()
        
        return env_path

# Global instance
env_manager = EnvManager() 