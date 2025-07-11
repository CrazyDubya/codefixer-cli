"""
Issue deduplication for CodeFixer.
Merges similar linting issues to avoid duplicates.
"""

from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

def deduplicate_issues(issues: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Deduplicate linting issues by merging similar ones.
    
    Args:
        issues: Dictionary mapping file paths to lists of linting issues
        
    Returns:
        Dictionary with deduplicated issues
    """
    deduplicated = {}
    
    for file_path, file_issues in issues.items():
        if not file_issues:
            continue
        
        # Group issues by position and code
        issue_groups = {}
        
        for issue in file_issues:
            # Create a key based on position and code
            key = (issue.get('row', 0), issue.get('col', 0), issue.get('code', ''))
            
            if key not in issue_groups:
                issue_groups[key] = []
            issue_groups[key].append(issue)
        
        # Merge issues in each group
        merged_issues = []
        for group_issues in issue_groups.values():
            if len(group_issues) == 1:
                merged_issues.append(group_issues[0])
            else:
                # Merge multiple issues at the same position
                merged_issue = merge_issue_group(group_issues)
                merged_issues.append(merged_issue)
        
        if merged_issues:
            deduplicated[file_path] = merged_issues
    
    return deduplicated

def merge_issue_group(issues: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Merge a group of issues at the same position.
    
    Args:
        issues: List of issues to merge
        
    Returns:
        Merged issue
    """
    if not issues:
        return {}
    
    # Use the first issue as base
    merged = issues[0].copy()
    
    # Combine messages from all issues
    messages = []
    codes = set()
    
    for issue in issues:
        text = issue.get('text', '').strip()
        code = issue.get('code', '').strip()
        
        if text and text not in messages:
            messages.append(text)
        if code and code not in codes:
            codes.add(code)
    
    # Update merged issue
    if len(messages) > 1:
        merged['text'] = '; '.join(messages)
    elif len(messages) == 1:
        merged['text'] = messages[0]
    
    if len(codes) > 1:
        merged['code'] = '+'.join(sorted(codes))
    elif len(codes) == 1:
        merged['code'] = list(codes)[0]
    
    return merged

def filter_duplicate_issues(issues: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Filter out duplicate issues based on content similarity.
    
    Args:
        issues: Dictionary mapping file paths to lists of linting issues
        
    Returns:
        Dictionary with filtered issues
    """
    filtered = {}
    
    for file_path, file_issues in issues.items():
        if not file_issues:
            continue
        
        # Remove exact duplicates
        seen = set()
        unique_issues = []
        
        for issue in file_issues:
            # Create a hash of the issue content
            issue_hash = hash_issue(issue)
            
            if issue_hash not in seen:
                seen.add(issue_hash)
                unique_issues.append(issue)
        
        if unique_issues:
            filtered[file_path] = unique_issues
    
    return filtered

def hash_issue(issue: Dict[str, Any]) -> str:
    """
    Create a hash for an issue to identify duplicates.
    
    Args:
        issue: Issue dictionary
        
    Returns:
        Hash string
    """
    # Create a string representation of the issue
    parts = [
        str(issue.get('row', '')),
        str(issue.get('col', '')),
        str(issue.get('code', '')),
        str(issue.get('text', '')).lower().strip()
    ]
    
    return '|'.join(parts)

def create_issue_key(issue: Dict[str, Any]) -> str:
    """
    Create a unique key for an issue based on its properties.
    
    Args:
        issue: Issue dictionary
        
    Returns:
        Unique key string
    """
    # Create a string representation of the issue
    parts = [
        str(issue.get('path', '')),
        str(issue.get('row', '')),
        str(issue.get('col', '')),
        str(issue.get('code', '')),
        str(issue.get('text', ''))
    ]
    
    return '|'.join(parts)

def prioritize_issues(issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Prioritize issues based on severity and type.
    
    Args:
        issues: List of linting issues
        
    Returns:
        Prioritized list of issues
    """
    # Define priority weights for different issue types
    priority_weights = {
        # High priority - security and critical issues
        'security': 100,
        'S101': 100,  # Use of assert detected
        'S105': 100,  # Possible hardcoded password
        'S106': 100,  # Possible hardcoded password
        'S107': 100,  # Possible hardcoded password
        'no-eval': 100,  # eval() usage
        'no-implied-eval': 100,  # implied eval
        
        # Medium priority - code quality issues
        'unused-variable': 50,
        'no-unused-vars': 50,
        'unused-import': 50,
        'F401': 50,  # Unused import
        'F403': 50,  # Wildcard import
        'no-console': 50,  # console.log usage
        'prefer-const': 45,  # Use const instead of let
        
        # Low priority - style issues
        'indent': 10,
        'E111': 10,  # Indentation
        'E112': 10,  # Expected indentation
        'quotes': 5,
        'semi': 5,
        'comma-dangle': 5,
        'trailing-comma': 5,
        
        # Very low priority - formatting
        'E501': 1,  # Line too long
        'max-len': 1,
        'printWidth': 1,
    }
    
    def get_priority(issue: Dict[str, Any]) -> int:
        """Get priority weight for an issue."""
        code = issue.get('code', '')
        
        # Check for security-related keywords
        if any(keyword in issue.get('text', '').lower() for keyword in ['security', 'vulnerability', 'unsafe', 'dangerous']):
            return priority_weights.get('security', 50)
        
        # Check for specific codes
        for pattern, weight in priority_weights.items():
            if pattern.lower() in code.lower():
                return weight
        
        # Default priority
        return 25
    
    # Sort issues by priority (highest first)
    prioritized = sorted(issues, key=get_priority, reverse=True)
    
    return prioritized

def filter_issues_by_severity(issues: List[Dict[str, Any]], min_severity: str = 'low') -> List[Dict[str, Any]]:
    """
    Filter issues by minimum severity level.
    
    Args:
        issues: List of linting issues
        min_severity: Minimum severity level ('low', 'medium', 'high', 'critical')
        
    Returns:
        Filtered list of issues
    """
    severity_levels = {
        'low': 1,
        'medium': 2,
        'high': 3,
        'critical': 4
    }
    
    min_level = severity_levels.get(min_severity.lower(), 1)
    
    def get_severity_level(issue: Dict[str, Any]) -> int:
        """Get severity level for an issue."""
        code = issue.get('code', '')
        text = issue.get('text', '').lower()
        
        # Critical issues
        if any(keyword in text for keyword in ['security', 'vulnerability', 'unsafe']):
            return 4
        if any(prefix in code for prefix in ['S101', 'S105', 'S106', 'S107']):
            return 4
        
        # High priority issues
        if any(prefix in code for prefix in ['F401', 'F403', 'unused', 'no-unused']):
            return 3
        if 'no-console' in code:
            return 3
        
        # Medium priority issues
        if any(prefix in code for prefix in ['E111', 'E112', 'indent']):
            return 2
        
        # Low priority issues (formatting, style)
        return 1
    
    filtered = [issue for issue in issues if get_severity_level(issue) >= min_level]
    return filtered

def group_issues_by_type(issues: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Group issues by their type/category.
    
    Args:
        issues: List of linting issues
        
    Returns:
        Dictionary mapping issue types to lists of issues
    """
    grouped = {}
    
    for issue in issues:
        code = issue.get('code', 'unknown')
        
        # Determine issue type
        if any(security_code in code for security_code in ['S101', 'S105', 'S106', 'S107']):
            issue_type = 'security'
        elif any(unused_code in code for unused_code in ['F401', 'F403', 'unused', 'no-unused']):
            issue_type = 'unused_code'
        elif any(style_code in code for style_code in ['indent', 'E111', 'E112', 'quotes', 'semi']):
            issue_type = 'style'
        elif any(format_code in code for format_code in ['E501', 'max-len', 'printWidth']):
            issue_type = 'formatting'
        elif 'no-console' in code:
            issue_type = 'debugging'
        else:
            issue_type = 'other'
        
        if issue_type not in grouped:
            grouped[issue_type] = []
        grouped[issue_type].append(issue)
    
    return grouped 