"""
CSS linter module for CodeFixer.
"""

import subprocess
import json
import os
from pathlib import Path
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

from .env_manager import env_manager

def get_css_temp_dir(repo_path: Path) -> Path:
    """Get temporary environment directory for CSS linters."""
    return env_manager.get_language_env("css", repo_path)

def setup_css_env(temp_dir: Path) -> bool:
    """
    Set up CSS linting environment in temporary directory.
    
    Args:
        temp_dir: Temporary directory to set up
        
    Returns:
        True if setup successful, False otherwise
    """
    try:
        # Initialize npm project
        subprocess.run([
            "npm", "init", "-y"
        ], cwd=temp_dir, check=True, capture_output=True)
        
        # Install stylelint and config
        subprocess.run([
            "npm", "install", "--save-dev", "stylelint", "stylelint-config-standard"
        ], cwd=temp_dir, check=True, capture_output=True)
        
        # Generate linter configs
        from .configs import generate_css_configs
        generate_css_configs(temp_dir)
        
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to setup CSS environment: {e}")
        return False

def run_stylelint(file_path: Path, temp_dir: Path) -> List[Dict[str, Any]]:
    """
    Run stylelint on a CSS file.
    
    Args:
        file_path: Path to the CSS file
        temp_dir: Temporary directory with npm environment
        
    Returns:
        List of linting issues
    """
    try:
        # Run stylelint
        result = subprocess.run([
            "npx", "stylelint",
            "--formatter", "json",
            str(file_path)
        ], cwd=temp_dir, capture_output=True, text=True)
        
        if result.returncode == 0:
            return []
        
        # Parse JSON output
        try:
            issues_data = json.loads(result.stdout)
            issues = []
            
            for file_issues in issues_data:
                for issue in file_issues.get("warnings", []):
                    issues.append({
                        "path": str(file_path),
                        "row": issue.get("line", 1),
                        "col": issue.get("column", 1),
                        "code": issue.get("rule", "unknown"),
                        "text": issue.get("text", "")
                    })
            
            return issues
            
        except json.JSONDecodeError:
            # Fallback to parsing text output
            return parse_stylelint_text_output(result.stdout, file_path)
            
    except subprocess.CalledProcessError as e:
        logger.error(f"stylelint failed for {file_path}: {e}")
        return []

def parse_stylelint_text_output(output: str, file_path: Path) -> List[Dict[str, Any]]:
    """
    Parse stylelint text output when JSON is not available.
    
    Args:
        output: stylelint text output
        file_path: Path to the file being linted
        
    Returns:
        List of linting issues
    """
    issues = []
    
    for line in output.strip().split('\n'):
        if not line or ':' not in line:
            continue
            
        # Parse stylelint output format: file:line:col: message (rule)
        parts = line.split(':', 3)
        if len(parts) >= 4:
            try:
                line_num = int(parts[1])
                col_num = int(parts[2])
                message_part = parts[3].strip()
                
                # Extract message and rule
                if ' (' in message_part and message_part.endswith(')'):
                    message, rule = message_part.rsplit(' (', 1)
                    rule = rule.rstrip(')')
                else:
                    message = message_part
                    rule = "unknown"
                
                issues.append({
                    "path": str(file_path),
                    "row": line_num,
                    "col": col_num,
                    "code": rule,
                    "text": message
                })
            except (ValueError, IndexError):
                continue
    
    return issues

def run_css_linter(files: List[Path], repo_path: Path) -> Dict[str, List[Dict[str, Any]]]:
    all_issues = {}
    temp_path = get_css_temp_dir(repo_path)
    
    # Setup CSS environment
    if not setup_css_env(temp_path):
        logger.error("Failed to setup CSS environment")
        return all_issues
    
    # Lint each file
    for file_path in files:
        issues = []
        
        # Run stylelint
        stylelint_issues = run_stylelint(file_path, temp_path)
        issues.extend(stylelint_issues)
        
        if issues:
            all_issues[str(file_path)] = issues

    return all_issues 