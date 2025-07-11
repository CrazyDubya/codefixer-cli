"""
Git utilities module for CodeFixer.
"""

import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
from git import Repo, GitCommandError

logger = logging.getLogger(__name__)

def check_repo_clean(repo_path: Path) -> bool:
    """
    Check if the repository is clean (no uncommitted changes).
    
    Args:
        repo_path: Path to the git repository
        
    Returns:
        True if clean, False otherwise
    """
    try:
        repo = Repo(repo_path)
        return not repo.is_dirty()
    except Exception as e:
        logger.error(f"Failed to check repository status: {e}")
        return False

def create_branch(repo_path: Path, branch_name: str) -> bool:
    """
    Create and checkout a new branch.
    
    Args:
        repo_path: Path to the git repository
        branch_name: Name of the new branch
        
    Returns:
        True if successful, False otherwise
    """
    try:
        repo = Repo(repo_path)
        
        # Check if branch already exists
        if branch_name in [branch.name for branch in repo.branches]:
            logger.warning(f"Branch {branch_name} already exists, checking it out")
            repo.heads[branch_name].checkout()
            return True
        
        # Create new branch
        new_branch = repo.create_head(branch_name)
        new_branch.checkout()
        
        logger.info(f"Created and checked out branch: {branch_name}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create branch {branch_name}: {e}")
        return False

def backup_file(file_path: Path) -> Optional[Path]:
    """
    Create a backup of a file.
    
    Args:
        file_path: Path to the file to backup
        
    Returns:
        Path to backup file or None if failed
    """
    try:
        backup_path = file_path.with_suffix(file_path.suffix + '.backup')
        shutil.copy2(file_path, backup_path)
        logger.debug(f"Created backup: {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"Failed to backup {file_path}: {e}")
        return None

def apply_fixes(repo_path: Path, fixes: Dict[str, str]) -> bool:
    """
    Apply fixes to files and commit them.
    
    Args:
        repo_path: Path to the git repository
        fixes: Dictionary mapping file paths to fixed code
        
    Returns:
        True if successful, False otherwise
    """
    try:
        repo = Repo(repo_path)
        
        # Apply each fix
        for file_path_str, fixed_code in fixes.items():
            file_path = Path(file_path_str)
            
            # Create backup
            backup_file(file_path)
            
            # Write fixed code
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(fixed_code)
                logger.debug(f"Applied fix to {file_path}")
            except Exception as e:
                logger.error(f"Failed to write fix to {file_path}: {e}")
                return False
        
        # Add all changes
        repo.git.add(all=True)
        
        # Create commit
        commit_message = f"Auto fixes by CodeFixer\n\nFixed {len(fixes)} files with linting issues"
        repo.index.commit(commit_message)
        
        logger.info(f"Committed fixes for {len(fixes)} files")
        return True
        
    except Exception as e:
        logger.error(f"Failed to apply fixes: {e}")
        return False

def detect_remote_host(repo_path: Path) -> Optional[str]:
    """
    Detect the remote host (GitHub, GitLab, etc.) from remote URL.
    
    Args:
        repo_path: Path to the git repository
        
    Returns:
        Host name (github, gitlab, etc.) or None if unknown
    """
    try:
        repo = Repo(repo_path)
        origin = repo.remotes.origin
        
        if not origin:
            return None
        
        url = origin.url.lower()
        
        if 'github.com' in url:
            return 'github'
        elif 'gitlab.com' in url:
            return 'gitlab'
        elif 'bitbucket.org' in url:
            return 'bitbucket'
        else:
            return None
            
    except Exception as e:
        logger.error(f"Failed to detect remote host: {e}")
        return None

def push_branch(repo_path: Path, branch_name: str) -> bool:
    """
    Push a branch to remote.
    
    Args:
        repo_path: Path to the git repository
        branch_name: Name of the branch to push
        
    Returns:
        True if successful, False otherwise
    """
    try:
        repo = Repo(repo_path)
        repo.git.push('origin', branch_name)
        logger.info(f"Pushed branch {branch_name} to remote")
        return True
    except GitCommandError as e:
        logger.error(f"Failed to push branch {branch_name}: {e}")
        return False

def create_github_pr(repo_path: Path, branch_name: str, issues: Dict[str, List[Dict[str, Any]]], fixes: Dict[str, str]) -> Optional[str]:
    """
    Create a pull request on GitHub.
    
    Args:
        repo_path: Path to the git repository
        branch_name: Name of the branch
        issues: Dictionary of linting issues
        fixes: Dictionary of applied fixes
        
    Returns:
        PR URL or None if failed
    """
    try:
        # Count issues
        total_issues = sum(len(file_issues) for file_issues in issues.values())
        fixed_files = len(fixes)
        
        # Create PR title and body
        title = f"Auto fixes by CodeFixer - {fixed_files} files"
        body = f"""## Summary

This PR contains automated fixes for linting issues detected by CodeFixer.

### Changes
- Fixed {fixed_files} files
- Resolved {total_issues} linting issues

### Files Modified
"""
        
        for file_path in fixes.keys():
            body += f"- `{file_path}`\n"
        
        body += "\n### Linting Issues Fixed\n"
        for file_path, file_issues in issues.items():
            if file_path in fixes:
                body += f"\n**{file_path}:**\n"
                for issue in file_issues:
                    body += f"- Line {issue.get('row', '?')}: {issue.get('code', 'unknown')} - {issue.get('text', '')}\n"
        
        # Create PR using GitHub CLI
        result = subprocess.run([
            "gh", "pr", "create",
            "--title", title,
            "--body", body,
            "--head", branch_name
        ], cwd=repo_path, capture_output=True, text=True)
        
        if result.returncode == 0:
            # Extract PR URL from output
            output_lines = result.stdout.strip().split('\n')
            for line in output_lines:
                if line.startswith('https://github.com/') and '/pull/' in line:
                    return line.strip()
            
            logger.warning("PR created but URL not found in output")
            return "PR created successfully"
        else:
            logger.error(f"Failed to create GitHub PR: {result.stderr}")
            return None
            
    except Exception as e:
        logger.error(f"Failed to create GitHub PR: {e}")
        return None

def create_gitlab_mr(repo_path: Path, branch_name: str, issues: Dict[str, List[Dict[str, Any]]], fixes: Dict[str, str]) -> Optional[str]:
    """
    Create a merge request on GitLab.
    
    Args:
        repo_path: Path to the git repository
        branch_name: Name of the branch
        issues: Dictionary of linting issues
        fixes: Dictionary of applied fixes
        
    Returns:
        MR URL or None if failed
    """
    try:
        # Count issues
        total_issues = sum(len(file_issues) for file_issues in issues.values())
        fixed_files = len(fixes)
        
        # Create MR title and description
        title = f"Auto fixes by CodeFixer - {fixed_files} files"
        description = f"""## Summary

This MR contains automated fixes for linting issues detected by CodeFixer.

### Changes
- Fixed {fixed_files} files
- Resolved {total_issues} linting issues

### Files Modified
"""
        
        for file_path in fixes.keys():
            description += f"- `{file_path}`\n"
        
        description += "\n### Linting Issues Fixed\n"
        for file_path, file_issues in issues.items():
            if file_path in fixes:
                description += f"\n**{file_path}:**\n"
                for issue in file_issues:
                    description += f"- Line {issue.get('row', '?')}: {issue.get('code', 'unknown')} - {issue.get('text', '')}\n"
        
        # Create MR using GitLab CLI
        result = subprocess.run([
            "glab", "mr", "create",
            "--title", title,
            "--description", description,
            "--source-branch", branch_name
        ], cwd=repo_path, capture_output=True, text=True)
        
        if result.returncode == 0:
            # Extract MR URL from output
            output_lines = result.stdout.strip().split('\n')
            for line in output_lines:
                if line.startswith('https://gitlab.com/') and '/-/merge_requests/' in line:
                    return line.strip()
            
            logger.warning("MR created but URL not found in output")
            return "MR created successfully"
        else:
            logger.error(f"Failed to create GitLab MR: {result.stderr}")
            return None
            
    except Exception as e:
        logger.error(f"Failed to create GitLab MR: {e}")
        return None

def push_and_pr(repo_path: Path, branch_name: str, issues: Dict[str, List[Dict[str, Any]]], fixes: Dict[str, str]) -> Optional[str]:
    """
    Push branch and create pull/merge request.
    
    Args:
        repo_path: Path to the git repository
        branch_name: Name of the branch
        issues: Dictionary of linting issues
        fixes: Dictionary of applied fixes
        
    Returns:
        PR/MR URL or None if failed
    """
    # Push branch
    if not push_branch(repo_path, branch_name):
        return None
    
    # Detect remote host
    host = detect_remote_host(repo_path)
    
    if host == 'github':
        return create_github_pr(repo_path, branch_name, issues, fixes)
    elif host == 'gitlab':
        return create_gitlab_mr(repo_path, branch_name, issues, fixes)
    else:
        logger.warning(f"Unknown remote host: {host}. Please create PR/MR manually.")
        logger.info(f"Branch {branch_name} has been pushed to remote.")
        return None 