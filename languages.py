"""
Language detection module for CodeFixer.
"""

import os
from pathlib import Path
from typing import Dict, List

# Language extensions mapping
LANGUAGE_EXTENSIONS = {
    'python': ['.py', '.pyx', '.pyi'],
    'javascript': ['.js', '.jsx', '.mjs'],
    'typescript': ['.ts', '.tsx'],
    'java': ['.java'],
    'cpp': ['.cpp', '.cc', '.cxx', '.hpp', '.h'],
    'c': ['.c', '.h'],
    'go': ['.go'],
    'rust': ['.rs'],
    'php': ['.php'],
    'ruby': ['.rb'],
    'swift': ['.swift'],
    'kotlin': ['.kt', '.kts'],
    'scala': ['.scala'],
    'dart': ['.dart'],
    'r': ['.r', '.R'],
    'matlab': ['.m'],
    'perl': ['.pl', '.pm'],
    'shell': ['.sh', '.bash', '.zsh', '.fish'],
    'powershell': ['.ps1'],
    'yaml': ['.yml', '.yaml'],
    'json': ['.json'],
    'xml': ['.xml'],
    'html': ['.html', '.htm'],
    'css': ['.css', '.scss', '.sass', '.less'],
    'sql': ['.sql'],
    'dockerfile': ['Dockerfile', '.dockerfile'],
    'makefile': ['Makefile', 'makefile'],
}

# Files to ignore
IGNORE_PATTERNS = [
    '.git',
    '__pycache__',
    'node_modules',
    '.venv',
    'venv',
    'env',
    'build',
    'dist',
    'target',
    '.pytest_cache',
    '.coverage',
    '*.pyc',
    '*.pyo',
    '*.log',
    '.DS_Store',
]

def should_ignore(path: Path) -> bool:
    """Check if a path should be ignored."""
    path_str = str(path)
    
    # Check ignore patterns
    for pattern in IGNORE_PATTERNS:
        if pattern in path_str:
            return True
    
    # Ignore hidden files and directories
    if any(part.startswith('.') for part in path.parts):
        return True
    
    return False

def detect_languages(repo_path: Path) -> Dict[str, List[Path]]:
    """
    Detect programming languages in the repository.
    
    Args:
        repo_path: Path to the git repository
        
    Returns:
        Dictionary mapping language names to lists of file paths
    """
    languages = {}
    
    # Create reverse mapping from extension to language
    ext_to_lang = {}
    for lang, exts in LANGUAGE_EXTENSIONS.items():
        for ext in exts:
            ext_to_lang[ext] = lang
    
    # Walk through the repository
    for root, dirs, files in os.walk(repo_path):
        # Skip ignored directories
        dirs[:] = [d for d in dirs if not should_ignore(Path(root) / d)]
        
        for file in files:
            file_path = Path(root) / file
            
            # Skip ignored files
            if should_ignore(file_path):
                continue
            
            # Check file extension
            file_ext = file_path.suffix.lower()
            file_name = file_path.name.lower()
            
            # Try to match by extension first
            if file_ext in ext_to_lang:
                lang = ext_to_lang[file_ext]
            # Try to match by filename (for files like Dockerfile, Makefile)
            elif file_name in ext_to_lang:
                lang = ext_to_lang[file_name]
            else:
                continue
            
            # Add to language mapping
            if lang not in languages:
                languages[lang] = []
            languages[lang].append(file_path)
    
    return languages

def get_supported_languages() -> List[str]:
    """Get list of supported programming languages."""
    return list(LANGUAGE_EXTENSIONS.keys())

def get_language_extensions(language: str) -> List[str]:
    """Get file extensions for a specific language."""
    return LANGUAGE_EXTENSIONS.get(language, []) 