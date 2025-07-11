"""
JavaScript/TypeScript linter module for CodeFixer.
"""

import subprocess
import json
import os
from pathlib import Path
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

from .env_manager import env_manager

def get_js_temp_dir(repo_path: Path) -> Path:
    """Get temporary environment directory for JavaScript/TypeScript linters."""
    return env_manager.get_language_env("js", repo_path)

def setup_js_env(temp_dir: Path) -> bool:
    """
    Set up JavaScript/TypeScript linting environment in temporary directory.
    
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
        
        # Install linters
        subprocess.run([
            "npm", "install", "--save-dev", 
            "eslint", "prettier", 
            "@typescript-eslint/parser", "@typescript-eslint/eslint-plugin",
            "tslint", "typescript"
        ], cwd=temp_dir, check=True, capture_output=True)
        
        # Generate configs using the centralized config generator
        from .configs import generate_js_configs
        generate_js_configs(temp_dir)
        
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to setup JavaScript environment: {e}")
        if e.stderr:
            logger.error(f"stderr: {e.stderr.decode()}")
        logger.info("Please ensure Node.js and npm are installed and accessible")
        return False

def run_eslint(file_path: Path, temp_dir: Path) -> List[Dict[str, Any]]:
    """
    Run ESLint on a JavaScript/TypeScript file.
    
    Args:
        file_path: Path to the JavaScript/TypeScript file
        temp_dir: Temporary directory with npm environment
        
    Returns:
        List of linting issues
    """
    try:
        # Run ESLint
        result = subprocess.run([
            "npx", "eslint",
            "--format=json",
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
                        "col": issue.get("column", 1),
                        "code": issue.get("ruleId", "unknown"),
                        "text": issue.get("message", "")
                    })
            
            return issues
            
        except json.JSONDecodeError:
            # Fallback to parsing text output
            return parse_eslint_text_output(result.stdout, file_path)
            
    except subprocess.CalledProcessError as e:
        logger.error(f"ESLint failed for {file_path}: {e}")
        return []

def parse_eslint_text_output(output: str, file_path: Path) -> List[Dict[str, Any]]:
    """
    Parse ESLint text output with robust handling of whitespace, severity, and formatting.
    
    Args:
        output: ESLint text output
        file_path: Path to the file being linted
        
    Returns:
        List of linting issues
    """
    import re
    issues = []
    
    # Pattern to match ESLint output: file:line:col  severity  message  (rule)
    pattern = r'^(.+):(\d+):(\d+)\s+(error|warn|warning)?\s*(.+?)\s*\((\w+)\)$'
    
    for line in output.strip().split('\n'):
        if not line or line.startswith('#'):
            continue
            
        match = re.match(pattern, line)
        if match:
            try:
                line_num = int(match.group(2))
                col_num = int(match.group(3))
                severity = match.group(4) or "error"
                message = match.group(5).strip()
                rule = match.group(6)
                
                issues.append({
                    "path": str(file_path),
                    "row": line_num,
                    "col": col_num,
                    "code": rule,
                    "text": message
                })
            except (ValueError, IndexError):
                continue
        else:
            # Fallback for simpler formats: file:line:col: message (rule)
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

def run_prettier_check(file_path: Path, temp_dir: Path) -> List[Dict[str, Any]]:
    """
    Check if file needs formatting with Prettier.
    
    Args:
        file_path: Path to the JavaScript/TypeScript file
        temp_dir: Temporary directory with npm environment
        
    Returns:
        List of formatting issues
    """
    try:
        # Run Prettier in check mode
        result = subprocess.run([
            "npx", "prettier",
            "--check",
            str(file_path)
        ], cwd=temp_dir, capture_output=True, text=True)
        
        if result.returncode == 0:
            return []
        
        # Prettier found formatting issues
        return [{
            "path": str(file_path),
            "row": 1,
            "col": 1,
            "code": "prettier/prettier",
            "text": "Code formatting issues detected by Prettier"
        }]
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Prettier check failed for {file_path}: {e}")
        return []

def run_tslint(file_path: Path, temp_dir: Path) -> List[Dict[str, Any]]:
    """
    Run TSLint on a TypeScript file.
    
    Args:
        file_path: Path to the TypeScript file
        temp_dir: Temporary directory with npm environment
        
    Returns:
        List of linting issues
    """
    try:
        # Run TSLint
        result = subprocess.run([
            "npx", "tslint",
            "--format", "json",
            str(file_path)
        ], cwd=temp_dir, capture_output=True, text=True)
        
        if result.returncode == 0:
            return []
        
        # Parse JSON output
        try:
            issues_data = json.loads(result.stdout)
            issues = []
            
            for issue in issues_data:
                issues.append({
                    "path": str(file_path),
                    "row": issue.get("startPosition", {}).get("line", 1),
                    "col": issue.get("startPosition", {}).get("character", 1),
                    "code": issue.get("ruleName", "unknown"),
                    "text": issue.get("failure", "")
                })
            
            return issues
            
        except json.JSONDecodeError:
            # Fallback to parsing text output
            return parse_tslint_text_output(result.stdout, file_path)
            
    except subprocess.CalledProcessError as e:
        logger.error(f"TSLint failed for {file_path}: {e}")
        return []

def parse_tslint_text_output(output: str, file_path: Path) -> List[Dict[str, Any]]:
    """Parse TSLint text output when JSON format fails."""
    issues = []
    lines = output.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line or str(file_path) not in line:
            continue
            
        # Parse TSLint output format: file.ts[line, col]: error: message
        try:
            # Extract line and column numbers
            if '[' in line and ']' in line:
                pos_start = line.find('[') + 1
                pos_end = line.find(']')
                pos_str = line[pos_start:pos_end]
                line_col = pos_str.split(', ')
                if len(line_col) >= 2:
                    row = int(line_col[0])
                    col = int(line_col[1])
                    
                    # Extract error message
                    if 'error:' in line:
                        message = line.split('error: ', 1)[1]
                    elif 'warning:' in line:
                        message = line.split('warning: ', 1)[1]
                    else:
                        message = line
                    
                    issues.append({
                        "path": str(file_path),
                        "row": row,
                        "col": col,
                        "code": "TSLINT",
                        "text": message.strip()
                    })
        except (ValueError, IndexError):
            # If parsing fails, add as generic issue
            issues.append({
                "path": str(file_path),
                "row": 1,
                "col": 1,
                "code": "TSLINT",
                "text": line
            })
    
    return issues

def run_js_linter(files: List[Path], repo_path: Path) -> Dict[str, List[Dict[str, Any]]]:
    all_issues = {}
    temp_path = get_js_temp_dir(repo_path)
    
    # Setup JavaScript environment
    if not setup_js_env(temp_path):
        logger.error("Failed to setup JavaScript environment")
        return all_issues
    
    # Separate TypeScript and JavaScript files
    ts_files = [f for f in files if f.suffix.lower() == '.ts' or f.suffix.lower() == '.tsx']
    js_files = [f for f in files if f.suffix.lower() in ['.js', '.jsx']]
    
    logger.info(f"Found {len(ts_files)} TypeScript files and {len(js_files)} JavaScript files")
    
    # Lint each file
    for file_path in files:
        issues = []
        
        # Use appropriate linter based on file type
        if file_path.suffix.lower() in ['.ts', '.tsx']:
            # Run TSLint for TypeScript files
            tslint_issues = run_tslint(file_path, temp_path)
            issues.extend(tslint_issues)
        else:
            # Run ESLint for JavaScript files
            eslint_issues = run_eslint(file_path, temp_path)
            issues.extend(eslint_issues)
        
        # Run Prettier check for all files
        prettier_issues = run_prettier_check(file_path, temp_path)
        issues.extend(prettier_issues)
        
        if issues:
            all_issues[str(file_path)] = issues

    return all_issues 