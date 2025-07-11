"""
Optimized JSON parsing utilities for CodeFixer.
"""

import json
import logging
from typing import Any, Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

def parse_json_safe(json_str: str, fallback_parser: Optional[callable] = None) -> List[Dict[str, Any]]:
    """
    Safely parse JSON with fallback to text parsing.
    
    Args:
        json_str: JSON string to parse
        fallback_parser: Optional function to use if JSON parsing fails
        
    Returns:
        List of parsed objects
    """
    if not json_str.strip():
        return []
    
    try:
        # Try to parse as JSON array
        if json_str.strip().startswith('['):
            return json.loads(json_str)
        
        # Try to parse as JSON object
        if json_str.strip().startswith('{'):
            obj = json.loads(json_str)
            return [obj] if isinstance(obj, dict) else []
        
        # Try to parse as newline-delimited JSON
        return parse_ndjson(json_str)
        
    except json.JSONDecodeError as e:
        logger.debug(f"JSON parsing failed: {e}")
        
        if fallback_parser:
            return fallback_parser(json_str)
        
        # Try to extract JSON objects from mixed content
        return extract_json_objects(json_str)

def parse_ndjson(json_str: str) -> List[Dict[str, Any]]:
    """
    Parse newline-delimited JSON.
    
    Args:
        json_str: Newline-delimited JSON string
        
    Returns:
        List of parsed objects
    """
    objects = []
    
    for line in json_str.strip().split('\n'):
        line = line.strip()
        if not line:
            continue
        
        try:
            obj = json.loads(line)
            if isinstance(obj, dict):
                objects.append(obj)
        except json.JSONDecodeError:
            continue
    
    return objects

def extract_json_objects(text: str) -> List[Dict[str, Any]]:
    """
    Extract JSON objects from mixed text content.
    
    Args:
        text: Text that may contain JSON objects
        
    Returns:
        List of extracted JSON objects
    """
    objects = []
    
    # Find JSON-like patterns
    import re
    
    # Pattern for JSON objects
    json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    
    matches = re.finditer(json_pattern, text)
    for match in matches:
        try:
            obj = json.loads(match.group())
            if isinstance(obj, dict):
                objects.append(obj)
        except json.JSONDecodeError:
            continue
    
    return objects

def parse_linter_output(output: str, file_path: Path, linter_type: str) -> List[Dict[str, Any]]:
    """
    Parse linter output with optimized parsing for different linter types.
    
    Args:
        output: Raw linter output
        file_path: Path to the file being linted
        linter_type: Type of linter (flake8, eslint, etc.)
        
    Returns:
        List of linting issues
    """
    if not output.strip():
        return []
    
    # Try JSON parsing first
    try:
        if linter_type == "flake8":
            return parse_flake8_json(output, file_path)
        elif linter_type == "eslint":
            return parse_eslint_json(output, file_path)
        elif linter_type == "mypy":
            return parse_mypy_json(output, file_path)
        else:
            # Generic JSON parsing
            json_data = parse_json_safe(output)
            return convert_generic_json(json_data, file_path)
    except Exception as e:
        logger.debug(f"JSON parsing failed for {linter_type}: {e}")
        # Fallback to text parsing
        return parse_linter_text(output, file_path, linter_type)

def parse_flake8_json(output: str, file_path: Path) -> List[Dict[str, Any]]:
    """Parse flake8 JSON output."""
    try:
        data = json.loads(output)
        issues = []
        
        for issue in data:
            issues.append({
                "path": str(file_path),
                "row": issue.get("line_number", 1),
                "col": issue.get("column_number", 1),
                "code": issue.get("code", "unknown"),
                "text": issue.get("text", "")
            })
        
        return issues
    except (json.JSONDecodeError, TypeError):
        return []

def parse_eslint_json(output: str, file_path: Path) -> List[Dict[str, Any]]:
    """Parse ESLint JSON output."""
    try:
        data = json.loads(output)
        issues = []
        
        # ESLint can return array or object
        if isinstance(data, list):
            files_data = data
        else:
            files_data = [data]
        
        for file_data in files_data:
            if not isinstance(file_data, dict):
                continue
            
            messages = file_data.get("messages", [])
            for message in messages:
                issues.append({
                    "path": str(file_path),
                    "row": message.get("line", 1),
                    "col": message.get("column", 1),
                    "code": message.get("ruleId", "unknown"),
                    "text": message.get("message", "")
                })
        
        return issues
    except (json.JSONDecodeError, TypeError):
        return []

def parse_mypy_json(output: str, file_path: Path) -> List[Dict[str, Any]]:
    """Parse mypy JSON output."""
    try:
        data = json.loads(output)
        issues = []
        
        # mypy returns a list of file results
        for file_result in data:
            if not isinstance(file_result, dict):
                continue
            
            result_path = file_result.get("path", "")
            if result_path != str(file_path):
                continue
            
            messages = file_result.get("messages", [])
            for message in messages:
                issues.append({
                    "path": str(file_path),
                    "row": message.get("line", 1),
                    "col": message.get("column", 1),
                    "code": "mypy",
                    "text": message.get("message", "")
                })
        
        return issues
    except (json.JSONDecodeError, TypeError):
        return []

def parse_linter_text(output: str, file_path: Path, linter_type: str) -> List[Dict[str, Any]]:
    """Parse linter text output as fallback."""
    import re
    
    issues = []
    
    if linter_type == "flake8":
        # flake8 format: file:line:col: code message
        pattern = r'^(.+):(\d+):(\d+):\s*(\w+)\s+(.+)$'
    elif linter_type == "eslint":
        # ESLint format: line:col error message (rule)
        pattern = r'^\s*(\d+):(\d+)\s+(error|warning)\s+(.+?)\s+\((.+?)\)$'
    elif linter_type == "mypy":
        # mypy format: file:line: error: message
        pattern = r'^(.+):(\d+):\s*(error|warning):\s*(.+)$'
    else:
        # Generic pattern
        pattern = r'^(.+):(\d+):(\d+):\s*(.+)$'
    
    for line in output.strip().split('\n'):
        if not line or line.startswith('#'):
            continue
        
        match = re.match(pattern, line)
        if match:
            try:
                if linter_type == "flake8":
                    line_num = int(match.group(2))
                    col_num = int(match.group(3))
                    code = match.group(4)
                    message = match.group(5).strip()
                elif linter_type == "eslint":
                    line_num = int(match.group(1))
                    col_num = int(match.group(2))
                    code = match.group(5)
                    message = match.group(4).strip()
                elif linter_type == "mypy":
                    line_num = int(match.group(2))
                    col_num = 1  # mypy doesn't provide column
                    code = "mypy"
                    message = match.group(4).strip()
                else:
                    line_num = int(match.group(2))
                    col_num = int(match.group(3))
                    code = "unknown"
                    message = match.group(4).strip()
                
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

def convert_generic_json(json_data: List[Dict[str, Any]], file_path: Path) -> List[Dict[str, Any]]:
    """Convert generic JSON data to standard issue format."""
    issues = []
    
    for item in json_data:
        if not isinstance(item, dict):
            continue
        
        # Try to extract common fields
        row = item.get("line", item.get("row", item.get("line_number"), 1))
        col = item.get("column", item.get("col", item.get("column_number"), 1))
        code = item.get("code", item.get("rule", item.get("ruleId"), "unknown"))
        text = item.get("message", item.get("text", ""))
        
        issues.append({
            "path": str(file_path),
            "row": row,
            "col": col,
            "code": code,
            "text": text
        })
    
    return issues 