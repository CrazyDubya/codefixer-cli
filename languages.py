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
    'html': ['.html', '.htm', '.xhtml'],
    'css': ['.css', '.scss', '.sass', '.less'],
    'yaml': ['.yml', '.yaml'],
    'go': ['.go'],
    'rust': ['.rs'],
    'java': ['.java'],
    'c': ['.c', '.h'],
    'cpp': ['.cpp', '.cc', '.cxx', '.hpp', '.hh', '.hxx'],
    'php': ['.php', '.phtml'],
    'ruby': ['.rb', '.erb'],
    'shell': ['.sh', '.bash', '.zsh', '.fish', '.ksh'],
    'markdown': ['.md', '.markdown'],
    'json': ['.json'],
    'xml': ['.xml'],
    'sql': ['.sql'],
    'dockerfile': ['Dockerfile', '.dockerfile'],
    'makefile': ['Makefile', 'makefile'],
    'toml': ['.toml'],
    'ini': ['.ini', '.cfg', '.conf'],
    'properties': ['.properties'],
    'gradle': ['.gradle', '.gradle.kts'],
    'maven': ['pom.xml'],
    'npm': ['package.json'],
    'cargo': ['Cargo.toml'],
    'go_mod': ['go.mod'],
    'requirements': ['requirements.txt', 'pyproject.toml', 'setup.py', 'Pipfile', 'poetry.lock'],
    'gemfile': ['Gemfile', 'Gemfile.lock'],
    'composer': ['composer.json', 'composer.lock'],
    'pubspec': ['pubspec.yaml', 'pubspec.lock'],
}

# Files to ignore
IGNORE_PATTERNS = [
    '.git',
    '__pycache__',
    'node_modules',
    '.venv',
    'venv',
    'env',
    '/build/',
    '/dist/',
    '/target/',
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
    
    # Create reverse mapping from extension to language (optimized)
    ext_to_lang = {}
    for lang, exts in LANGUAGE_EXTENSIONS.items():
        for ext in exts:
            ext_to_lang[ext] = lang
    
    # Use pathlib for more efficient file walking
    try:
        # Use rglob for more efficient recursive globbing
        all_files = list(repo_path.rglob('*'))
    except PermissionError:
        # Fallback to os.walk if rglob fails
        all_files = []
        for root, dirs, files in os.walk(repo_path):
            # Skip ignored directories
            dirs[:] = [d for d in dirs if not should_ignore(Path(root) / d)]
            for file in files:
                all_files.append(Path(root) / file)
    
    # Process files in batches for better performance
    batch_size = 1000
    for i in range(0, len(all_files), batch_size):
        batch = all_files[i:i + batch_size]
        
        for file_path in batch:
            # Skip directories and ignored files
            if not file_path.is_file() or should_ignore(file_path):
                continue
            
            # Check file extension and name
            file_ext = file_path.suffix.lower()
            file_name = file_path.name
            file_name_lower = file_name.lower()
            
            # Try to match by exact filename first (for files like Dockerfile, Makefile, package.json)
            if file_name in ext_to_lang:
                lang = ext_to_lang[file_name]
            # Try to match by lowercase filename
            elif file_name_lower in ext_to_lang:
                lang = ext_to_lang[file_name_lower]
            # Try to match by extension
            elif file_ext in ext_to_lang:
                lang = ext_to_lang[file_ext]
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