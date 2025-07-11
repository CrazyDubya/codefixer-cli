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
    if not files:
        return {}
    
    # Determine optimal number of processes
    num_processes = min(mp.cpu_count(), len(files), 8)  # Cap at 8 processes
    
    if len(files) <= 1 or num_processes <= 1:
        # Run sequentially for small workloads
        return linter_func(files, repo_path)
    
    # Split files into chunks for parallel processing
    chunk_size = max(1, len(files) // num_processes)
    file_chunks = [files[i:i + chunk_size] for i in range(0, len(files), chunk_size)]
    
    logger.info(f"Running {linter_func.__name__} in parallel with {num_processes} processes on {len(files)} files")
    
    # Use ProcessPoolExecutor for better resource management
    from concurrent.futures import ProcessPoolExecutor, as_completed
    import functools
    
    all_issues = {}
    
    with ProcessPoolExecutor(max_workers=num_processes) as executor:
        # Submit tasks
        future_to_chunk = {
            executor.submit(_run_linter_chunk, linter_func, chunk, repo_path): chunk 
            for chunk in file_chunks
        }
        
        # Collect results
        for future in as_completed(future_to_chunk):
            try:
                chunk_issues = future.result()
                if chunk_issues:
                    all_issues.update(chunk_issues)
            except Exception as e:
                chunk = future_to_chunk[future]
                logger.error(f"Error processing chunk {chunk}: {e}")
                # Fallback to sequential processing for this chunk
                try:
                    fallback_issues = linter_func(chunk, repo_path)
                    if fallback_issues:
                        all_issues.update(fallback_issues)
                except Exception as fallback_error:
                    logger.error(f"Fallback processing also failed: {fallback_error}")
    
    return all_issues

def _run_linter_chunk(linter_func: Callable, files: List[Path], repo_path: Path) -> Dict[str, List[Dict[str, Any]]]:
    """
    Run linter on a chunk of files (worker function for multiprocessing).
    
    Args:
        linter_func: Function to run
        files: List of files to lint
        repo_path: Path to the repository
        
    Returns:
        Dictionary mapping file paths to lists of linting issues
    """
    try:
        return linter_func(files, repo_path)
    except Exception as e:
        logger.error(f"Error in linter chunk: {e}")
        return {}

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
    
    # Use ThreadPoolExecutor for language-level parallelism
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    # Determine optimal number of threads for language-level parallelism
    num_languages = len(other_languages) + (1 if js_files or ts_files else 0)
    num_threads = min(num_languages, mp.cpu_count(), 4)  # Cap at 4 threads for language parallelism
    
    logger.info(f"Running linters in parallel with {num_threads} threads for {num_languages} languages")
    
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        # Submit language linter tasks
        future_to_lang = {}
        
        # Submit JS/TS linter task
        if js_files or ts_files:
            all_js_ts_files = js_files + ts_files
            future = executor.submit(run_linter_parallel, run_js_linter, all_js_ts_files, repo_path)
            future_to_lang[future] = "javascript/typescript"
        
        # Submit other language linter tasks
        for lang, files in other_languages.items():
            if lang in linter_mappings:
                future = executor.submit(run_linter_parallel, linter_mappings[lang], files, repo_path)
                future_to_lang[future] = lang
            else:
                logger.warning(f"No linter configured for {lang}")
        
        # Collect results
        for future in as_completed(future_to_lang):
            lang = future_to_lang[future]
            try:
                issues = future.result()
                if issues:
                    all_issues.update(issues)
                    logger.info(f"Completed {lang} linting with {len(issues)} files")
            except Exception as e:
                logger.error(f"Error in {lang} linter: {e}")
    
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