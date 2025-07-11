"""
Parallel linter execution for CodeFixer.
Runs multiple linters concurrently for better performance.
"""

import multiprocessing as mp
from pathlib import Path
from typing import Dict, List, Any, Callable
import logging

logger = logging.getLogger(__name__)

def run_linter_parallel(linter_func: Callable, files: List[Path], repo_path: Path) -> Dict[str, List[Dict[str, Any]]]:
    """
    Run a linter function in parallel for multiple files.
    
    Args:
        linter_func: Function to run (e.g., run_python_linter)
        files: List of files to lint
        repo_path: Path to the repository
        
    Returns:
        Dictionary mapping file paths to lists of linting issues
    """
    # For now, run sequentially but prepare for parallel execution
    # TODO: Implement true parallel processing when linters support it
    return linter_func(files, repo_path)

def run_linters_parallel(languages: Dict[str, List[Path]], repo_path: Path) -> Dict[str, List[Dict[str, Any]]]:
    """
    Run multiple language linters in parallel.
    
    Args:
        languages: Dictionary mapping language names to lists of file paths
        repo_path: Path to the repository
        
    Returns:
        Dictionary mapping file paths to lists of linting issues
    """
    all_issues = {}
    
    # Import linter functions
    from linters.python_linter import run_python_linter
    from linters.js_linter import run_js_linter
    from linters.html_linter import run_html_linter
    from linters.css_linter import run_css_linter
    from linters.yaml_linter import run_yaml_linter
    
    # Define linter mappings
    linter_mappings = {
        'python': run_python_linter,
        'javascript': run_js_linter,
        'typescript': run_js_linter,  # JS linter handles both
        'html': run_html_linter,
        'css': run_css_linter,
        'yaml': run_yaml_linter
    }
    
    # Group JS/TS files together
    js_files = []
    ts_files = []
    other_languages = {}
    
    for lang, files in languages.items():
        if lang == 'javascript':
            js_files.extend(files)
        elif lang == 'typescript':
            ts_files.extend(files)
        else:
            other_languages[lang] = files
    
    # Run JS/TS linter once if we have JS or TS files
    if js_files or ts_files:
        logger.info("Linting JavaScript/TypeScript files...")
        all_js_ts_files = js_files + ts_files
        issues = run_js_linter(all_js_ts_files, repo_path)
        if issues:
            all_issues.update(issues)
    
    # Run other language linters
    for lang, files in other_languages.items():
        if lang in linter_mappings:
            logger.info(f"Linting {lang} files...")
            issues = linter_mappings[lang](files, repo_path)
            if issues:
                all_issues.update(issues)
        else:
            logger.warning(f"No linter configured for {lang}")
    
    return all_issues

def run_linters_sequential(languages: Dict[str, List[Path]], repo_path: Path) -> Dict[str, List[Dict[str, Any]]]:
    """
    Run linters sequentially (current implementation).
    
    Args:
        languages: Dictionary mapping language names to lists of file paths
        repo_path: Path to the repository
        
    Returns:
        Dictionary mapping file paths to lists of linting issues
    """
    all_issues = {}
    
    # Import linter functions
    from linters.python_linter import run_python_linter
    from linters.js_linter import run_js_linter
    from linters.html_linter import run_html_linter
    from linters.css_linter import run_css_linter
    from linters.yaml_linter import run_yaml_linter
    
    # Group JS/TS files together
    js_files = []
    ts_files = []
    other_languages = {}
    
    for lang, files in languages.items():
        if lang == 'javascript':
            js_files.extend(files)
        elif lang == 'typescript':
            ts_files.extend(files)
        else:
            other_languages[lang] = files
    
    # Run JS/TS linter once if we have JS or TS files
    if js_files or ts_files:
        logger.info("Linting JavaScript/TypeScript files...")
        all_js_ts_files = js_files + ts_files
        issues = run_js_linter(all_js_ts_files, repo_path)
        if issues:
            all_issues.update(issues)
    
    # Run other language linters
    for lang, files in other_languages.items():
        logger.info(f"Linting {lang} files...")
        if lang == 'python':
            issues = run_python_linter(files, repo_path)
        elif lang == 'html':
            issues = run_html_linter(files, repo_path)
        elif lang == 'css':
            issues = run_css_linter(files, repo_path)
        elif lang == 'yaml':
            issues = run_yaml_linter(files, repo_path)
        else:
            logger.warning(f"No linter configured for {lang}")
            continue
        
        if issues:
            all_issues.update(issues)
    
    return all_issues 