"""
YAML linter module for CodeFixer.
"""

import subprocess
import json
import os
from pathlib import Path
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

from .env_manager import env_manager

def get_yaml_temp_dir(repo_path: Path) -> Path:
    """Get temporary environment directory for YAML linters."""
    return env_manager.get_language_env("yaml", repo_path)

def setup_yaml_env(temp_dir: Path) -> bool:
    """
    Set up YAML linting environment in temporary directory.
    
    Args:
        temp_dir: Temporary directory to set up
        
    Returns:
        True if setup successful, False otherwise
    """
    try:
        # Create virtual environment
        venv_path = temp_dir / "venv"
        if not (venv_path / "bin" / "python").exists() and not (venv_path / "Scripts" / "python.exe").exists():
            subprocess.run([
                "python3", "-m", "venv", str(venv_path)
            ], check=True, capture_output=True)
        
        # Get pip path
        if os.name == 'nt':
            pip_path = venv_path / "Scripts" / "pip"
        else:
            pip_path = venv_path / "bin" / "pip"
        
        # Install yamllint
        subprocess.run([
            str(pip_path), "install", "--upgrade", "yamllint"
        ], check=True, capture_output=True)
        
        # Generate configs using the centralized config generator
        from .configs import generate_yaml_configs
        generate_yaml_configs(temp_dir)
        
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to setup YAML environment: {e}")
        if e.stderr:
            logger.error(f"stderr: {e.stderr.decode()}")
        logger.info("Please ensure Python 3.8+ is installed and accessible")
        return False

def run_yamllint(file_path: Path, temp_dir: Path) -> List[Dict[str, Any]]:
    """
    Run yamllint on a YAML file.
    
    Args:
        file_path: Path to the YAML file
        temp_dir: Temporary directory with venv environment
        
    Returns:
        List of linting issues
    """
    try:
        if os.name == 'nt':
            yamllint_path = temp_dir / "venv" / "Scripts" / "yamllint"
        else:
            yamllint_path = temp_dir / "venv" / "bin" / "yamllint"
        
        result = subprocess.run([
            str(yamllint_path),
            "--format", "parsable",
            str(file_path)
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            return []
        
        return parse_yamllint_output(result.stdout, file_path)
        
    except subprocess.CalledProcessError as e:
        logger.error(f"yamllint failed for {file_path}: {e}")
        return []

def parse_yamllint_output(output: str, file_path: Path) -> List[Dict[str, Any]]:
    """Parse yamllint output."""
    import re
    issues = []
    
    # Pattern: file:line:col: [level] message (rule)
    pattern = r'^(.+):(\d+):(\d+):\s*\[(\w+)\]\s*(.+?)\s*\((\w+)\)$'
    
    for line in output.strip().split('\n'):
        if not line or line.startswith('#'):
            continue
            
        match = re.match(pattern, line)
        if match:
            try:
                line_num = int(match.group(2))
                col_num = int(match.group(3))
                level = match.group(4)
                message = match.group(5).strip()
                rule = match.group(6)
                
                issues.append({
                    "path": str(file_path),
                    "row": line_num,
                    "col": col_num,
                    "code": rule,
                    "text": f"[{level}] {message}"
                })
            except (ValueError, IndexError):
                continue
    
    return issues

def run_yaml_linter(files: List[Path], repo_path: Path) -> Dict[str, List[Dict[str, Any]]]:
    """
    Run YAML linter on a list of files.
    
    Args:
        files: List of YAML files to lint
        repo_path: Path to the repository
        
    Returns:
        Dictionary mapping file paths to lists of linting issues
    """
    all_issues = {}
    temp_path = get_yaml_temp_dir(repo_path)
    
    if not setup_yaml_env(temp_path):
        logger.error("Failed to setup YAML environment")
        return all_issues
    
    for file_path in files:
        issues = run_yamllint(file_path, temp_path)
        if issues:
            all_issues[str(file_path)] = issues
    
    return all_issues 