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

def prioritize_issues(issues: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Prioritize issues by severity and importance.
    
    Args:
        issues: Dictionary mapping file paths to lists of linting issues
        
    Returns:
        Dictionary with prioritized issues
    """
    prioritized = {}
    
    for file_path, file_issues in issues.items():
        if not file_issues:
            continue
        
        # Sort issues by priority
        sorted_issues = sorted(file_issues, key=lambda x: get_issue_priority(x), reverse=True)
        prioritized[file_path] = sorted_issues
    
    return prioritized

def get_issue_priority(issue: Dict[str, Any]) -> int:
    """
    Get priority score for an issue.
    
    Args:
        issue: Issue dictionary
        
    Returns:
        Priority score (higher = more important)
    """
    priority = 0
    code = issue.get('code', '').lower()
    text = issue.get('text', '').lower()
    
    # High priority issues
    if any(keyword in code or keyword in text for keyword in ['error', 'security', 'critical']):
        priority += 100
    
    # Medium priority issues
    if any(keyword in code or keyword in text for keyword in ['warning', 'style', 'format']):
        priority += 50
    
    # Specific high-priority codes
    high_priority_codes = ['E501', 'E302', 'E303', 'F401', 'F403', 'F405']
    if any(code in issue.get('code', '') for code in high_priority_codes):
        priority += 75
    
    # Lower priority for formatting issues
    if any(keyword in code or keyword in text for keyword in ['indent', 'whitespace', 'trailing']):
        priority += 25
    
    return priority 