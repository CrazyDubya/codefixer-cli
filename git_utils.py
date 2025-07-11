"""
Git utilities module for CodeFixer.
"""

import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
from git import Repo, GitCommandError
import difflib

logger = logging.getLogger(__name__)

def check_repo_clean(repo_path: Path) -> bool:
    """
    Check if the git repository is clean (no uncommitted changes).
    
    Args:
        repo_path: Path to the repository
        
    Returns:
        True if repository is clean, False otherwise
    """
    try:
        repo = Repo(repo_path)
        
        # Check for uncommitted changes
        if repo.is_dirty():
            logger.error("Repository has uncommitted changes:")
            
            # Show modified files
            for item in repo.index.diff(None):
                logger.error(f"  Modified: {item.a_path}")
            
            # Show untracked files
            for untracked in repo.untracked_files:
                logger.error(f"  Untracked: {untracked}")
            
            # Show staged changes
            for item in repo.index.diff('HEAD'):
                logger.error(f"  Staged: {item.a_path}")
            
            logger.info("Please commit or stash your changes before running CodeFixer")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error checking repository status: {e}")
        return False

def get_repo_status_summary(repo_path: Path) -> Dict[str, Any]:
    """
    Get a summary of the repository status.
    
    Args:
        repo_path: Path to the repository
        
    Returns:
        Dictionary with status information
    """
    try:
        repo = Repo(repo_path)
        
        status = {
            "is_dirty": repo.is_dirty(),
            "modified_files": [],
            "untracked_files": [],
            "staged_files": [],
            "current_branch": repo.active_branch.name if repo.head.is_valid() else None
        }
        
        if repo.is_dirty():
            # Get modified files
            for item in repo.index.diff(None):
                status["modified_files"].append(item.a_path)
            
            # Get untracked files
            status["untracked_files"] = repo.untracked_files
            
            # Get staged files
            for item in repo.index.diff('HEAD'):
                status["staged_files"].append(item.a_path)
        
        return status
        
    except Exception as e:
        logger.error(f"Error getting repository status: {e}")
        return {"error": str(e)}

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
        backups = {}  # Track backup files for cleanup/rollback
        
        # Apply each fix
        for file_path_str, fixed_code in fixes.items():
            file_path = Path(file_path_str)
            
            # Create backup
            backup_path = backup_file(file_path)
            if backup_path:
                backups[str(file_path)] = backup_path
            
            # Write fixed code
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(fixed_code)
                logger.debug(f"Applied fix to {file_path}")
            except Exception as e:
                logger.error(f"Failed to write fix to {file_path}: {e}")
                # Rollback on failure
                _rollback_fixes(backups)
                return False
        
        # Add all changes
        repo.git.add(all=True)
        
        # Create commit
        commit_message = f"Auto fixes by CodeFixer\n\nFixed {len(fixes)} files with linting issues"
        repo.index.commit(commit_message)
        
        # Clean up backup files after successful commit
        _cleanup_backups(backups)
        
        logger.info(f"Committed fixes for {len(fixes)} files")
        return True
        
    except Exception as e:
        logger.error(f"Failed to apply fixes: {e}")
        # Rollback on any exception
        _rollback_fixes(backups)
        return False

def _rollback_fixes(backups: Dict[str, Path]) -> None:
    """Rollback fixes by restoring from backup files."""
    for file_path_str, backup_path in backups.items():
        try:
            file_path = Path(file_path_str)
            if backup_path.exists():
                shutil.copy2(backup_path, file_path)
                logger.debug(f"Rolled back {file_path} from backup")
        except Exception as e:
            logger.error(f"Failed to rollback {file_path_str}: {e}")

def _cleanup_backups(backups: Dict[str, Path]) -> None:
    """Clean up backup files after successful commit."""
    for backup_path in backups.values():
        try:
            if backup_path.exists():
                backup_path.unlink()
                logger.debug(f"Cleaned up backup: {backup_path}")
        except Exception as e:
            logger.error(f"Failed to cleanup backup {backup_path}: {e}")

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
        
        # Check if GitHub CLI is available
        import shutil
        if not shutil.which('gh'):
            logger.error("GitHub CLI (gh) not found. Please install it or create PR manually.")
            logger.info("Install GitHub CLI: https://cli.github.com/")
            logger.info(f"Then run: gh pr create --title '{title}' --body '...' --head {branch_name}")
            return None
        
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
            logger.info("You may need to authenticate with: gh auth login")
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

def push_and_pr(repo_path: Path, branch_name: str, commit_message: str, fixes: Dict[str, str], issues: Dict[str, List[Dict[str, Any]]], show_diff_in_pr: bool = False) -> bool:
    """
    Push branch and create pull request.
    
    Args:
        repo_path: Path to the repository
        branch_name: Name of the branch to push
        commit_message: Commit message
        fixes: Dictionary mapping file paths to fixed content
        issues: Dictionary mapping file paths to lists of issues
        show_diff_in_pr: Whether to include diffs in PR body
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Push the branch
        if not push_branch(repo_path, branch_name):
            logger.error("Failed to push branch")
            return False
        
        # Generate PR body
        pr_body = generate_pr_body(fixes, issues, show_diff_in_pr)
        
        # Create pull request
        pr_title = f"CodeFixer: {commit_message}"
        if not create_pull_request(repo_path, branch_name, pr_title, pr_body):
            logger.error("Failed to create pull request")
            return False
        
        logger.info("Branch pushed and pull request created successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error in push_and_pr: {e}")
        return False

def create_pull_request(repo_path: Path, branch_name: str, title: str, body: str = "") -> bool:
    """
    Create a pull request using GitHub CLI.
    
    Args:
        repo_path: Path to the repository
        branch_name: Name of the branch to create PR for
        title: PR title
        body: PR body (can include diffs)
        
    Returns:
        True if PR created successfully, False otherwise
    """
    try:
        # Get the current branch (target for PR)
        current_branch = get_current_branch(repo_path)
        if not current_branch:
            logger.error("Could not determine current branch")
            return False
        
        # Create PR using GitHub CLI
        cmd = [
            "gh", "pr", "create",
            "--title", title,
            "--body", body,
            "--head", branch_name,
            "--base", current_branch
        ]
        
        result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"Pull request created successfully: {result.stdout.strip()}")
            return True
        else:
            logger.error(f"Failed to create pull request: {result.stderr}")
            return False
            
    except subprocess.CalledProcessError as e:
        logger.error(f"Error creating pull request: {e}")
        return False

def generate_pr_body(fixes: Dict[str, str], issues: Dict[str, List[Dict[str, Any]]], show_diff: bool = False) -> str:
    """
    Generate a comprehensive PR body with issue summary and optional diffs.
    
    Args:
        fixes: Dictionary mapping file paths to fixed content
        issues: Dictionary mapping file paths to lists of issues
        show_diff: Whether to include diffs in the PR body
        
    Returns:
        Formatted PR body string
    """
    body_parts = []
    
    # Summary
    total_files = len(fixes)
    total_issues = sum(len(issues.get(file_path, [])) for file_path in fixes.keys())
    
    body_parts.append(f"## CodeFixer Automated Fixes")
    body_parts.append("")
    body_parts.append(f"This PR contains automated fixes for **{total_issues} issues** across **{total_files} files**.")
    body_parts.append("")
    
    # Files summary
    body_parts.append("### Files Modified")
    for file_path in sorted(fixes.keys()):
        file_issues = issues.get(file_path, [])
        issue_count = len(file_issues)
        body_parts.append(f"- `{file_path}` ({issue_count} issues)")
    body_parts.append("")
    
    # Issue breakdown
    body_parts.append("### Issue Breakdown")
    issue_types = {}
    for file_path, file_issues in issues.items():
        for issue in file_issues:
            issue_type = issue.get("code", "unknown")
            issue_types[issue_type] = issue_types.get(issue_type, 0) + 1
    
    for issue_type, count in sorted(issue_types.items()):
        body_parts.append(f"- **{issue_type}**: {count} issues")
    body_parts.append("")
    
    # Include diffs if requested
    if show_diff:
        body_parts.append("### Detailed Changes")
        body_parts.append("")
        
        for file_path in sorted(fixes.keys()):
            original_content = read_file_content(Path(file_path))
            fixed_content = fixes[file_path]
            
            if original_content != fixed_content:
                diff = generate_unified_diff(file_path, original_content, fixed_content)
                if diff:
                    body_parts.append(f"#### {file_path}")
                    body_parts.append("```diff")
                    body_parts.append(diff)
                    body_parts.append("```")
                    body_parts.append("")
    
    # Footer
    body_parts.append("---")
    body_parts.append("*This PR was automatically generated by CodeFixer CLI*")
    body_parts.append("*Please review all changes before merging*")
    
    return "\n".join(body_parts)

def read_file_content(file_path: Path) -> str:
    """Read file content safely."""
    try:
        return file_path.read_text(encoding='utf-8')
    except Exception as e:
        logger.warning(f"Could not read {file_path}: {e}")
        return ""

def generate_unified_diff(file_path: str, original: str, fixed: str) -> str:
    """Generate unified diff for a file."""
    try:
        diff_lines = difflib.unified_diff(
            original.splitlines(keepends=True),
            fixed.splitlines(keepends=True),
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}",
            lineterm=""
        )
        return "".join(diff_lines)
    except Exception as e:
        logger.warning(f"Could not generate diff for {file_path}: {e}")
        return "" 