"""
JavaScript/TypeScript linter module for CodeFixer.
"""

import subprocess
import tempfile
import json
import os
from pathlib import Path
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

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
            "npm", "install", "--save-dev", "eslint", "prettier", "@typescript-eslint/parser", "@typescript-eslint/eslint-plugin"
        ], cwd=temp_dir, check=True, capture_output=True)
        
        # Create basic ESLint config
        eslint_config = {
            "env": {
                "browser": True,
                "es2021": True,
                "node": True
            },
            "extends": [
                "eslint:recommended",
                "@typescript-eslint/recommended"
            ],
            "parser": "@typescript-eslint/parser",
            "parserOptions": {
                "ecmaVersion": "latest",
                "sourceType": "module"
            },
            "plugins": [
                "@typescript-eslint"
            ],
            "rules": {
                "indent": ["error", 2],
                "linebreak-style": ["error", "unix"],
                "quotes": ["error", "single"],
                "semi": ["error", "always"]
            }
        }
        
        with open(temp_dir / ".eslintrc.json", "w") as f:
            json.dump(eslint_config, f, indent=2)
        
        # Create basic Prettier config
        prettier_config = {
            "semi": True,
            "trailingComma": "es5",
            "singleQuote": True,
            "printWidth": 80,
            "tabWidth": 2
        }
        
        with open(temp_dir / ".prettierrc.json", "w") as f:
            json.dump(prettier_config, f, indent=2)
        
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to setup JavaScript environment: {e}")
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
    Parse ESLint text output when JSON is not available.
    
    Args:
        output: ESLint text output
        file_path: Path to the file being linted
        
    Returns:
        List of linting issues
    """
    issues = []
    
    for line in output.strip().split('\n'):
        if not line or ':' not in line:
            continue
            
        # Parse ESLint output format: file:line:col: message (rule)
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

def run_js_linter(files: List[Path], repo_path: Path) -> Dict[str, List[Dict[str, Any]]]:
    """
    Run JavaScript/TypeScript linters on a list of files.
    
    Args:
        files: List of JavaScript/TypeScript file paths
        repo_path: Path to the repository root
        
    Returns:
        Dictionary mapping file paths to lists of linting issues
    """
    all_issues = {}
    
    # Create temporary environment
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Setup JavaScript environment
        if not setup_js_env(temp_path):
            logger.error("Failed to setup JavaScript environment")
            return all_issues
        
        # Lint each file
        for file_path in files:
            issues = []
            
            # Run ESLint
            eslint_issues = run_eslint(file_path, temp_path)
            issues.extend(eslint_issues)
            
            # Run Prettier check
            prettier_issues = run_prettier_check(file_path, temp_path)
            issues.extend(prettier_issues)
            
            if issues:
                all_issues[str(file_path)] = issues
    
    return all_issues 