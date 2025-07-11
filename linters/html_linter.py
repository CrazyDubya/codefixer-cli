"""
HTML linter module for CodeFixer.
"""

import subprocess
import json
import os
from pathlib import Path
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

from .env_manager import env_manager

def get_html_temp_dir(repo_path: Path) -> Path:
    """Get temporary environment directory for HTML linters."""
    return env_manager.get_language_env("html", repo_path)

def setup_html_env(temp_dir: Path) -> bool:
    """
    Set up HTML linting environment in temporary directory.
    
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
        
        # Install htmlhint
        subprocess.run([
            "npm", "install", "--save-dev", "htmlhint"
        ], cwd=temp_dir, check=True, capture_output=True)
        
        # Generate linter configs
        from .configs import generate_html_configs
        generate_html_configs(temp_dir)
        
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to setup HTML environment: {e}")
        return False

def run_htmlhint(file_path: Path, temp_dir: Path) -> List[Dict[str, Any]]:
    """
    Run htmlhint on an HTML file.
    
    Args:
        file_path: Path to the HTML file
        temp_dir: Temporary directory with npm environment
        
    Returns:
        List of linting issues
    """
    try:
        # Run htmlhint
        result = subprocess.run([
            "npx", "htmlhint",
            "--format", "json",
            str(file_path)
        ], cwd=temp_dir, capture_output=True, text=True)
        
        if result.returncode == 0:
            return []
        
        # Parse JSON output
        try:
            issues_data = json.loads(result.stdout)
            issues = []
            
            for file_issues in issues_data:
                for issue in file_issues.get("messages", []):
                    issues.append({
                        "path": str(file_path),
                        "row": issue.get("line", 1),
                        "col": issue.get("col", 1),
                        "code": issue.get("rule", "unknown"),
                        "text": issue.get("message", "")
                    })
            
            return issues
            
        except json.JSONDecodeError:
            # Fallback to parsing text output
            return parse_htmlhint_text_output(result.stdout, file_path)
            
    except subprocess.CalledProcessError as e:
        logger.error(f"htmlhint failed for {file_path}: {e}")
        return []

def parse_htmlhint_text_output(output: str, file_path: Path) -> List[Dict[str, Any]]:
    """
    Parse htmlhint text output when JSON is not available.
    
    Args:
        output: htmlhint text output
        file_path: Path to the file being linted
        
    Returns:
        List of linting issues
    """
    issues = []
    
    for line in output.strip().split('\n'):
        if not line or ':' not in line:
            continue
            
        # Parse htmlhint output format: file:line:col: message (rule)
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

def run_html_linter(files: List[Path], repo_path: Path) -> Dict[str, List[Dict[str, Any]]]:
    all_issues = {}
    temp_path = get_html_temp_dir(repo_path)
    
    # Setup HTML environment
    if not setup_html_env(temp_path):
        logger.error("Failed to setup HTML environment")
        return all_issues
    
    # Lint each file
    for file_path in files:
        issues = []
        
        # Run htmlhint
        htmlhint_issues = run_htmlhint(file_path, temp_path)
        issues.extend(htmlhint_issues)
        
        if issues:
            all_issues[str(file_path)] = issues

    return all_issues 