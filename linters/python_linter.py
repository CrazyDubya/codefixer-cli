"""
Python linter module for CodeFixer.
"""

import subprocess
import tempfile
import json
import os
from pathlib import Path
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

def setup_python_env(temp_dir: Path) -> bool:
    """
    Set up Python linting environment in temporary directory.
    
    Args:
        temp_dir: Temporary directory to set up
        
    Returns:
        True if setup successful, False otherwise
    """
    try:
        # Create virtual environment
        venv_path = temp_dir / "venv"
        subprocess.run([
            "python3", "-m", "venv", str(venv_path)
        ], check=True, capture_output=True)
        
        # Get pip path
        if os.name == 'nt':  # Windows
            pip_path = venv_path / "Scripts" / "pip"
        else:  # Unix-like
            pip_path = venv_path / "bin" / "pip"
        
        # Install linters
        subprocess.run([
            str(pip_path), "install", "flake8", "black"
        ], check=True, capture_output=True)
        
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to setup Python environment: {e}")
        return False

def run_flake8(file_path: Path, temp_dir: Path) -> List[Dict[str, Any]]:
    """
    Run flake8 on a Python file.
    
    Args:
        file_path: Path to the Python file
        temp_dir: Temporary directory with virtual environment
        
    Returns:
        List of linting issues
    """
    try:
        # Get flake8 path
        if os.name == 'nt':  # Windows
            flake8_path = temp_dir / "venv" / "Scripts" / "flake8"
        else:  # Unix-like
            flake8_path = temp_dir / "venv" / "bin" / "flake8"
        
        # Run flake8
        result = subprocess.run([
            str(flake8_path),
            "--format=json",
            str(file_path)
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            return []
        
        # Parse JSON output
        try:
            issues = json.loads(result.stdout)
            return issues
        except json.JSONDecodeError:
            # Fallback to parsing text output
            return parse_flake8_text_output(result.stdout, file_path)
            
    except subprocess.CalledProcessError as e:
        logger.error(f"Flake8 failed for {file_path}: {e}")
        return []

def parse_flake8_text_output(output: str, file_path: Path) -> List[Dict[str, Any]]:
    """
    Parse flake8 text output when JSON is not available.
    
    Args:
        output: Flake8 text output
        file_path: Path to the file being linted
        
    Returns:
        List of linting issues
    """
    issues = []
    
    for line in output.strip().split('\n'):
        if not line:
            continue
            
        # Parse flake8 output format: file:line:col:code message
        parts = line.split(':', 3)
        if len(parts) >= 4:
            try:
                line_num = int(parts[1])
                col_num = int(parts[2])
                code_and_message = parts[3].strip()
                
                # Split code and message
                if ' ' in code_and_message:
                    code, message = code_and_message.split(' ', 1)
                else:
                    code = code_and_message
                    message = ""
                
                issues.append({
                    "path": str(file_path),
                    "row": line_num,
                    "col": col_num,
                    "code": code,
                    "text": message
                })
            except (ValueError, IndexError):
                continue
    
    return issues

def run_black_check(file_path: Path, temp_dir: Path) -> List[Dict[str, Any]]:
    """
    Check if file needs formatting with black.
    
    Args:
        file_path: Path to the Python file
        temp_dir: Temporary directory with virtual environment
        
    Returns:
        List of formatting issues
    """
    try:
        # Get black path
        if os.name == 'nt':  # Windows
            black_path = temp_dir / "venv" / "Scripts" / "black"
        else:  # Unix-like
            black_path = temp_dir / "venv" / "bin" / "black"
        
        # Run black in check mode
        result = subprocess.run([
            str(black_path),
            "--check",
            "--diff",
            str(file_path)
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            return []
        
        # Black found formatting issues
        return [{
            "path": str(file_path),
            "row": 1,
            "col": 1,
            "code": "E501",  # Use a generic code for formatting
            "text": "Code formatting issues detected by black"
        }]
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Black check failed for {file_path}: {e}")
        return []

def run_python_linter(files: List[Path], repo_path: Path) -> Dict[str, List[Dict[str, Any]]]:
    """
    Run Python linters on a list of files.
    
    Args:
        files: List of Python file paths
        repo_path: Path to the repository root
        
    Returns:
        Dictionary mapping file paths to lists of linting issues
    """
    all_issues = {}
    
    # Create temporary environment
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Setup Python environment
        if not setup_python_env(temp_path):
            logger.error("Failed to setup Python environment")
            return all_issues
        
        # Lint each file
        for file_path in files:
            issues = []
            
            # Run flake8
            flake8_issues = run_flake8(file_path, temp_path)
            issues.extend(flake8_issues)
            
            # Run black check
            black_issues = run_black_check(file_path, temp_path)
            issues.extend(black_issues)
            
            if issues:
                all_issues[str(file_path)] = issues
    
    return all_issues 