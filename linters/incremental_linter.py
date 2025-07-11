"""
Incremental linting support for CodeFixer.
Tracks file modifications to avoid re-linting unchanged files.
"""

import hashlib
import json
import time
from pathlib import Path
from typing import Dict, List, Set, Any, Optional
import logging

logger = logging.getLogger(__name__)

class IncrementalLinter:
    """Tracks file modifications for incremental linting."""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        if cache_dir is None:
            cache_dir = Path.home() / ".cache" / "codefixer"
        
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "file_hashes.json"
        self._load_cache()
    
    def _load_cache(self):
        """Load the file hash cache."""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r') as f:
                    self.file_hashes = json.load(f)
            else:
                self.file_hashes = {}
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")
            self.file_hashes = {}
    
    def _save_cache(self):
        """Save the file hash cache."""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.file_hashes, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")
    
    def _get_file_hash(self, file_path: Path) -> str:
        """Calculate hash of file content."""
        try:
            if not file_path.exists():
                return ""
            
            # Use modification time and size for quick check
            stat = file_path.stat()
            quick_hash = f"{stat.st_mtime}_{stat.st_size}"
            
            # For small files, also hash content
            if stat.st_size < 1024 * 1024:  # 1MB
                with open(file_path, 'rb') as f:
                    content_hash = hashlib.md5(f.read()).hexdigest()
                return f"{quick_hash}_{content_hash}"
            
            return quick_hash
        except Exception as e:
            logger.warning(f"Failed to hash file {file_path}: {e}")
            return ""
    
    def get_changed_files(self, files: List[Path]) -> List[Path]:
        """Get list of files that have changed since last lint."""
        changed_files = []
        
        for file_path in files:
            current_hash = self._get_file_hash(file_path)
            cached_hash = self.file_hashes.get(str(file_path), "")
            
            if current_hash != cached_hash:
                changed_files.append(file_path)
                # Update cache
                self.file_hashes[str(file_path)] = current_hash
        
        if changed_files:
            logger.info(f"Found {len(changed_files)} changed files out of {len(files)} total")
            self._save_cache()
        
        return changed_files
    
    def mark_files_linted(self, files: List[Path]):
        """Mark files as recently linted."""
        for file_path in files:
            current_hash = self._get_file_hash(file_path)
            self.file_hashes[str(file_path)] = current_hash
        
        self._save_cache()
    
    def clear_cache(self):
        """Clear the entire cache."""
        self.file_hashes = {}
        self._save_cache()
        logger.info("Cleared incremental linting cache")
    
    def cleanup_old_entries(self, max_age_days: int = 30):
        """Remove cache entries for files that no longer exist."""
        current_time = time.time()
        removed_count = 0
        
        for file_path_str in list(self.file_hashes.keys()):
            file_path = Path(file_path_str)
            if not file_path.exists():
                del self.file_hashes[file_path_str]
                removed_count += 1
        
        if removed_count > 0:
            logger.info(f"Removed {removed_count} stale cache entries")
            self._save_cache()

# Global instance
incremental_linter = IncrementalLinter() 