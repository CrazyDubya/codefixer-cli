"""
Python linter module for CodeFixer.
"""

import subprocess
import json
import os
from pathlib import Path
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

from .env_manager import env_manager

def get_python_temp_dir(repo_path: Path) -> Path:
    """Get temporary environment directory for Python linters."""
    return env_manager.get_language_env("python", repo_path)

def setup_python_env(temp_dir: Path) -> bool:
    """
    Set up Python linting environment in persistent temp directory.
    """
    try:
        venv_path = temp_dir / "venv"
        # Only create venv if missing
        if not (venv_path / "bin" / "python").exists() and not (venv_path / "Scripts" / "python.exe").exists():
            subprocess.run([
                "python3", "-m", "venv", str(venv_path)
            ], check=True, capture_output=True)
        # Get pip path
        if os.name == 'nt':
            pip_path = venv_path / "Scripts" / "pip"
        else:
            pip_path = venv_path / "bin" / "pip"
        # Always try to install/upgrade linters (idempotent)
        subprocess.run([
            str(pip_path), "install", "--upgrade", "flake8", "black", "pytest", "mypy"
        ], check=True, capture_output=True)
        # Generate configs if missing
        from .configs import generate_python_configs
        generate_python_configs(temp_dir)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to setup Python environment: {e}")
        if e.stderr:
            logger.error(f"stderr: {e.stderr.decode()}")
        logger.info("Please ensure Python 3.8+ is installed and accessible")
        return False

def run_flake8(file_path: Path, temp_dir: Path, is_test: bool = False) -> List[Dict[str, Any]]:
    """
    Run flake8 on a Python file.
    
    Args:
        file_path: Path to the Python file
        temp_dir: Temporary directory with venv
        is_test: Whether this is a test file
        
    Returns:
        List of linting issues
    """
    try:
        if os.name == 'nt':
            flake8_path = temp_dir / "venv" / "Scripts" / "flake8"
        else:
            flake8_path = temp_dir / "venv" / "bin" / "flake8"
        
        # Use different config for test files
        config_file = temp_dir / "flake8_test.ini" if is_test else temp_dir / "flake8.ini"
        
        result = subprocess.run([
            str(flake8_path),
            "--format=json",
            "--config", str(config_file),
            str(file_path)
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            return []
        
        # Parse JSON output
        try:
            issues_data = json.loads(result.stdout)
            issues = []
            
            for issue in issues_data:
                issues.append({
                    "path": str(file_path),
                    "row": issue.get("line_number", 1),
                    "col": issue.get("column_number", 1),
                    "code": issue.get("code", "unknown"),
                    "text": issue.get("text", "")
                })
            
            return issues
            
        except json.JSONDecodeError:
            # Fallback to parsing text output
            return parse_flake8_text_output(result.stdout, file_path)
            
    except subprocess.CalledProcessError as e:
        logger.error(f"flake8 failed for {file_path}: {e}")
        return []

def parse_flake8_text_output(output: str, file_path: Path) -> List[Dict[str, Any]]:
    """Parse flake8 text output with robust handling of whitespace and formatting."""
    import re
    issues = []
    
    # Pattern to match flake8 output: file:line:col: code message
    pattern = r'^(.+):(\d+):(\d+):\s*(\w+)\s+(.+)$'
    
    for line in output.strip().split('\n'):
        if not line or line.startswith('#'):
            continue
            
        match = re.match(pattern, line)
        if match:
            try:
                line_num = int(match.group(2))
                col_num = int(match.group(3))
                code = match.group(4)
                message = match.group(5).strip()
                
                issues.append({
                    "path": str(file_path),
                    "row": line_num,
                    "col": col_num,
                    "code": code,
                    "text": message
                })
            except (ValueError, IndexError):
                continue
        else:
            # Fallback for non-standard formats
            parts = line.split(':', 3)
            if len(parts) >= 4:
                try:
                    line_num = int(parts[1])
                    col_num = int(parts[2])
                    code_and_message = parts[3].strip()
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
    try:
        if os.name == 'nt':
            black_path = temp_dir / "venv" / "Scripts" / "black"
        else:
            black_path = temp_dir / "venv" / "bin" / "black"
        result = subprocess.run([
            str(black_path),
            "--check",
            "--diff",
            "--config", str(temp_dir / "pyproject.toml"),
            str(file_path)
        ], capture_output=True, text=True)
        if result.returncode == 0:
            return []
        return [{
            "path": str(file_path),
            "row": 1,
            "col": 1,
            "code": "E501",
            "text": "Code formatting issues detected by black"
        }]
    except subprocess.CalledProcessError as e:
        logger.error(f"Black check failed for {file_path}: {e}")
        return []

def run_mypy(file_path: Path, temp_dir: Path) -> List[Dict[str, Any]]:
    """Run mypy type checker on a Python file."""
    try:
        if os.name == 'nt':
            mypy_path = temp_dir / "venv" / "Scripts" / "mypy"
        else:
            mypy_path = temp_dir / "venv" / "bin" / "mypy"
        
        result = subprocess.run([
            str(mypy_path),
            "--no-error-summary",
            "--no-pretty",
            str(file_path)
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            return []
        
        return parse_mypy_output(result.stdout, file_path)
        
    except subprocess.CalledProcessError as e:
        logger.error(f"mypy failed for {file_path}: {e}")
        return []

def parse_mypy_output(output: str, file_path: Path) -> List[Dict[str, Any]]:
    """Parse mypy output."""
    import re
    issues = []
    
    # Pattern: file:line: error: message
    pattern = r'^(.+):(\d+):\s*error:\s*(.+)$'
    
    for line in output.strip().split('\n'):
        if not line or line.startswith('Found'):
            continue
            
        match = re.match(pattern, line)
        if match:
            try:
                line_num = int(match.group(2))
                message = match.group(3).strip()
                
                issues.append({
                    "path": str(file_path),
                    "row": line_num,
                    "col": 1,
                    "code": "mypy",
                    "text": message
                })
            except (ValueError, IndexError):
                continue
    
    return issues

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
    temp_path = get_python_temp_dir(repo_path)
    
    # Setup Python environment
    if not setup_python_env(temp_path):
        logger.error("Failed to setup Python environment")
        return all_issues
    
    # Separate test files from regular files
    test_files = [f for f in files if is_test_file(f)]
    regular_files = [f for f in files if not is_test_file(f)]
    
    logger.info(f"Found {len(test_files)} test files and {len(regular_files)} regular files")
    
    # Run tests if test files exist
    if test_files:
        test_results = run_pytest_tests(test_files, temp_path, repo_path)
        if test_results:
            all_issues.update(test_results)
    
    # Lint each file
    for file_path in files:
        issues = []
        
        # Run flake8 with appropriate config for test vs regular files
        flake8_issues = run_flake8(file_path, temp_path, is_test_file(file_path))
        issues.extend(flake8_issues)
        
        # Run black check
        black_issues = run_black_check(file_path, temp_path)
        issues.extend(black_issues)
        
        # Run mypy (skip for test files by default)
        if not is_test_file(file_path):
            mypy_issues = run_mypy(file_path, temp_path)
            issues.extend(mypy_issues)
        
        if issues:
            all_issues[str(file_path)] = issues

    return all_issues

def is_test_file(file_path: Path) -> bool:
    """Check if a file is a test file."""
    filename = file_path.name.lower()
    return (
        filename.startswith('test_') or
        filename.endswith('_test.py') or
        'test' in file_path.parts or
        'tests' in file_path.parts
    )

def run_pytest_tests(test_files: List[Path], temp_dir: Path, repo_path: Path) -> Dict[str, List[Dict[str, Any]]]:
    """Run pytest on test files and return test failures as lint issues."""
    try:
        if os.name == 'nt':
            pytest_path = temp_dir / "venv" / "Scripts" / "pytest"
        else:
            pytest_path = temp_dir / "venv" / "bin" / "pytest"
        
        # Run pytest on all test files
        result = subprocess.run([
            str(pytest_path),
            "--tb=short",
            "--no-header",
            "--no-summary",
            "--json-report",
            "--json-report-file=none",
            *[str(f) for f in test_files]
        ], cwd=repo_path, capture_output=True, text=True)
        
        if result.returncode == 0:
            return {}
        
        # Parse test failures
        issues = {}
        lines = result.stdout.split('\n')
        current_file = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Look for file paths in test output
            if line.endswith('.py') and ('test_' in line or '_test.py' in line):
                for test_file in test_files:
                    if test_file.name in line or str(test_file) in line:
                        current_file = str(test_file)
                        if current_file not in issues:
                            issues[current_file] = []
                        break
            
            # Look for test failures
            if current_file and ('FAILED' in line or 'ERROR' in line or 'AssertionError' in line):
                issues[current_file].append({
                    "path": current_file,
                    "row": 1,
                    "col": 1,
                    "code": "TEST_FAILURE",
                    "text": f"Test failure: {line}"
                })
        
        return issues
        
    except subprocess.CalledProcessError as e:
        logger.error(f"pytest failed: {e}")
        return {} 