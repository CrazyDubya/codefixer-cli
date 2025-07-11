#!/usr/bin/env python3
"""
CodeFixer CLI - A local-only command-line utility for automated code fixing.
"""

import click
import os
import sys
from pathlib import Path
import difflib
from tqdm import tqdm
from typing import List, Dict, Any

# Import our modules
from languages import detect_languages
from linters.python_linter import run_python_linter
from linters.js_linter import run_js_linter
from linters.html_linter import run_html_linter
from linters.css_linter import run_css_linter
from linters.yaml_linter import run_yaml_linter
from linters.go_linter import GoLinter
from linters.rust_linter import RustLinter
from linters.java_linter import JavaLinter
from linters.env_manager import EnvironmentManager
from llm import generate_fix
from git_utils import create_branch, apply_fixes, push_and_pr, commit_changes
from logger import setup_logger

logger = setup_logger()

def show_colored_diff(file_path: str, original_content: str, fixed_content: str):
    """Show colored diff output for a file."""
    try:
        original_lines = original_content.splitlines(keepends=True)
        fixed_lines = fixed_content.splitlines(keepends=True)
        
        diff_lines = difflib.unified_diff(
            original_lines, 
            fixed_lines, 
            fromfile=f"a/{file_path}", 
            tofile=f"b/{file_path}", 
            lineterm=""
        )
        
        logger.info(f"Diff for {file_path}:")
        for line in diff_lines:
            if line.startswith('+'):
                print(f"\033[32m{line}\033[0m")  # Green for additions
            elif line.startswith('-'):
                print(f"\033[31m{line}\033[0m")  # Red for deletions
            elif line.startswith('@'):
                print(f"\033[36m{line}\033[0m")  # Cyan for context
            else:
                print(line)
                
    except Exception as e:
        logger.warning(f"Could not show diff for {file_path}: {e}")

def show_issues_for_file(file_path: str, issues: List[Dict[str, Any]]):
    """Show detailed issues for a file."""
    logger.info(f"Issues for {file_path}:")
    for issue in issues:
        logger.info(f"  Line {issue['row']}, Col {issue['col']}: {issue['code']} - {issue['text']}")

def generate_report(repo_path: Path, languages: Dict[str, List[Path]], all_issues: Dict[str, List[Dict[str, Any]]], 
                   fixes: Dict[str, str], model: str, runner: str, dry_run: bool, report_path: str) -> None:
    """
    Generate a detailed report of the fixing process.
    
    Args:
        repo_path: Path to the repository
        languages: Detected languages and their files
        all_issues: All linting issues found
        fixes: Generated fixes
        model: LLM model used
        runner: LLM runner used
        dry_run: Whether this was a dry run
        report_path: Path to save the report
    """
    try:
        from datetime import datetime
        import json
        
        # Calculate statistics
        total_files = sum(len(files) for files in languages.values())
        total_issues = sum(len(issues) for issues in all_issues.values())
        files_with_issues = len(all_issues)
        files_fixed = len(fixes)
        
        # Group issues by type
        all_issues_flat = []
        for issues in all_issues.values():
            all_issues_flat.extend(issues)
        
        from issue_deduplicator import group_issues_by_type
        grouped_issues = group_issues_by_type(all_issues_flat)
        
        # Create report data
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "repository": str(repo_path),
            "summary": {
                "total_files_analyzed": total_files,
                "languages_detected": list(languages.keys()),
                "files_with_issues": files_with_issues,
                "total_issues_found": total_issues,
                "files_fixed": files_fixed,
                "dry_run": dry_run
            },
            "llm_config": {
                "model": model,
                "runner": runner
            },
            "languages": {
                lang: [str(f) for f in files] for lang, files in languages.items()
            },
            "issues_by_type": {
                issue_type: len(type_issues) for issue_type, type_issues in grouped_issues.items()
            },
            "files_with_issues": {
                file_path: {
                    "issue_count": len(issues),
                    "issues": issues
                } for file_path, issues in all_issues.items()
            },
            "fixes_applied": {
                file_path: {
                    "original_issue_count": len(all_issues.get(file_path, [])),
                    "fixed_content_length": len(fixed_content)
                } for file_path, fixed_content in fixes.items()
            }
        }
        
        # Write report
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2)
        
        logger.info(f"Detailed report saved to: {report_path}")
        
    except Exception as e:
        logger.error(f"Failed to generate report: {e}")

@click.command()
@click.option('--repo', help='Path to the git repository')
@click.option('--branch', default='codefixer-fixes', help='Branch name for fixes')
@click.option('--model', default='gemma3:1b', help='Local LLM model to use')
@click.option('--runner', default='auto', help='LLM runner (auto, ollama, llama.cpp, vllm, lmstudio, huggingface)')
@click.option('--no-push', is_flag=True, help='Skip pushing branch and creating PR')
@click.option('--dry-run', is_flag=True, help='Show what would be done without applying changes')
@click.option('--output', type=click.Choice(['text', 'json']), default='text', help='Output format')
@click.option('--verbose', '-v', is_flag=True, help='Verbose logging')
@click.option('--cleanup', is_flag=True, help='Clean up all temporary environments')
@click.option('--local-only', is_flag=True, help='Apply fixes locally without git operations')
@click.option('--show-issues', is_flag=True, help='Show all lint issues per file in dry-run mode')
@click.option('--show-diff', is_flag=True, help='Show unified diff of proposed fixes in dry-run mode')
@click.option('--config', is_flag=True, help='Show current configuration')
@click.option('--config-reset', is_flag=True, help='Reset configuration to defaults')
@click.option('--list-models', is_flag=True, help='List available LLM models')
@click.option('--timeout', default=30, help='LLM request timeout in seconds')
@click.option('--retries', default=3, help='Number of retries for LLM requests')
@click.option('--report', help='Generate detailed report file')
@click.option('--show-diff-in-pr', is_flag=True, help='Include diffs in PR body')
def main(repo, branch, model, runner, no_push, dry_run, output, verbose, cleanup, 
         show_issues, show_diff, config, config_reset, list_models, timeout, retries, show_diff_in_pr, local_only, report):
    """CodeFixer - Automated code fixing with local LLM and best-practice linters.
    
    CodeFixer is a privacy-first, local-only CLI tool that automatically analyzes your git repositories,
    detects programming languages, runs industry-standard linters in isolated environments, and uses a
    local LLM (≤7B parameters) to generate safe, human-reviewable code fixes. It applies fixes to a
    new git branch and can create a pull request for your review. No code or data ever leaves your machine.
    
    WORKFLOW:
    1. Language Detection: Scans repository for Python, JavaScript/TypeScript, HTML, and CSS files
    2. Linting: Runs flake8/black (Python), ESLint/Prettier (JS/TS), htmlhint (HTML), stylelint (CSS)
    3. LLM Fixing: Uses local LLM to generate fixes for detected lint issues
    4. Git Operations: Creates branch, applies fixes, commits changes
    5. PR Creation: Pushes branch and creates pull request for human review
    
    USAGE EXAMPLES:
    
    # One-click automated fixing (creates PR)
    codefixer --repo ~/projects/myrepo
    
    # Preview what would be fixed (dry run)
    codefixer --repo ~/projects/myrepo --dry-run
    
    # See all issues and diffs before applying
    codefixer --repo ~/projects/myrepo --dry-run --show-issues --show-diff
    
    # Machine-readable output for LLMs/scripts
    codefixer --repo ~/projects/myrepo --dry-run --output json --show-issues --show-diff
    
    # Use specific LLM model
    codefixer --repo ~/projects/myrepo --model smollm2:135m --runner ollama
    
    # Skip PR creation (just apply fixes locally)
    codefixer --repo ~/projects/myrepo --no-push
    
    # Clean up temporary environments
    codefixer --cleanup
    
    # Show configuration and available models
    codefixer --config
    codefixer --list-models
    
    ENVIRONMENT MANAGEMENT:
    - Temporary linter environments are stored in your system temp directory
    - Environments older than 24 hours are automatically cleaned up
    - Use --cleanup to manually remove all temporary environments
    - Each repository gets its own cached environments for faster subsequent runs
    
    PRIVACY & SECURITY:
    - All analysis, linting, and LLM inference happens locally
    - No code, metadata, or telemetry is sent anywhere
    - All fixes are proposed in a new branch and PR for human review
    - Temporary environments are isolated and automatically cleaned up
    
    SUPPORTED LANGUAGES & LINTERS:
    - Python: flake8, black, mypy, pytest
    - JavaScript/TypeScript: ESLint, Prettier
    - HTML: htmlhint
    - CSS: stylelint
    - YAML: yamllint
    - Go: golangci-lint
    - Rust: clippy
    - Java: PMD, Checkstyle
    
    For more information, visit: https://github.com/CrazyDubya/codefixer-cli
    """
    
    if verbose:
        logger.setLevel('DEBUG')
    
    # Handle configuration commands
    if config:
        from config_manager import show_config
        show_config()
        return
    
    if config_reset:
        from config_manager import reset_config
        if reset_config():
            logger.info("Configuration reset to defaults")
        else:
            logger.error("Failed to reset configuration")
        return
    
    if list_models:
        from llm import list_available_models
        models = list_available_models(runner)
        if models:
            logger.info(f"Available {runner} models:")
            for model in models:
                logger.info(f"  - {model}")
        else:
            logger.warning(f"No models found for {runner}")
        return
    
    # Handle cleanup command
    if cleanup:
        from linters.env_manager import env_manager
        env_manager.cleanup_all()
        return
    
    logger.info(f"Starting CodeFixer on repository: {repo}")
    
    # Validate repository path (skip if cleanup only)
    if not repo and not cleanup:
        logger.error("Repository path is required (use --repo)")
        sys.exit(1)
        
    if repo:
        repo_path = Path(repo)
        if not repo_path.exists():
            logger.error(f"Repository path does not exist: {repo}")
            sys.exit(1)
        
        # Check if repository is clean (skip for local-only mode)
        if not local_only:
            if not (repo_path / '.git').exists():
                logger.error(f"Not a git repository: {repo}")
                sys.exit(1)
            
            from git_utils import check_repo_clean
            if not check_repo_clean(repo_path):
                logger.error(f"Repository has uncommitted changes. Please commit or stash them first.")
                sys.exit(1)
        else:
            # For local-only mode, just check if path exists
            if not repo_path.exists():
                logger.error(f"Path does not exist: {repo}")
                sys.exit(1)
    
    try:
        # Phase 1: Detect languages
        logger.info("Detecting languages...")
        languages = detect_languages(repo_path)
        logger.info(f"Detected languages: {list(languages.keys())}")
        
        if not languages:
            logger.warning("No supported languages detected")
            return
        
        # Phase 2: Run linters
        all_issues = {}
        
        # Handle JS/TS together to avoid redundant linting
        js_files = []
        ts_files = []
        other_languages = {}
        
        for lang, files in languages.items():
            if lang == 'javascript':
                js_files.extend(files)
            elif lang == 'typescript':
                ts_files.extend(files)
            else:
                other_languages[lang] = files
        
        # Run JS/TS linter once if we have JS or TS files
        if js_files or ts_files:
            logger.info("Linting JavaScript/TypeScript files...")
            combined_files = js_files + ts_files
            with tqdm(total=len(combined_files), desc="JS/TS files", unit="file") as pbar:
                issues = run_js_linter(combined_files, repo_path)
                pbar.update(len(combined_files))
            all_issues.update(issues)
        
        # Initialize environment manager and new linters
        env_manager = EnvironmentManager()
        go_linter = GoLinter(env_manager)
        rust_linter = RustLinter(env_manager)
        java_linter = JavaLinter(env_manager)
        
        # Run other language linters
        for lang, files in other_languages.items():
            logger.info(f"Linting {lang} files...")
            with tqdm(total=len(files), desc=f"{lang} files", unit="file") as pbar:
                if lang == 'python':
                    issues = run_python_linter(files, repo_path)
                elif lang == 'html':
                    issues = run_html_linter(files, repo_path)
                elif lang == 'css':
                    issues = run_css_linter(files, repo_path)
                elif lang == 'yaml':
                    issues = run_yaml_linter(files, repo_path)
                elif lang == 'go':
                    issues = go_linter.lint_files(repo_path, files)
                elif lang == 'rust':
                    issues = rust_linter.lint_files(repo_path, files)
                elif lang == 'java':
                    issues = java_linter.lint_files(repo_path, files)
                else:
                    logger.warning(f"No linter available for {lang}")
                    continue
                pbar.update(len(files))
            all_issues.update(issues)
        
        if not all_issues:
            logger.info("No linting issues found")
            return
        
        # Deduplicate and prioritize issues
        from issue_deduplicator import deduplicate_issues, prioritize_issues, filter_issues_by_severity, group_issues_by_type
        
        logger.info("Deduplicating and prioritizing issues...")
        deduplicated_issues = {}
        
        for file_path, issues in all_issues.items():
            # Deduplicate issues for this file
            unique_issues = deduplicate_issues(issues)
            
            # Prioritize issues (most important first)
            prioritized_issues = prioritize_issues(unique_issues)
            
            # Filter by minimum severity (optional - could be configurable)
            filtered_issues = filter_issues_by_severity(prioritized_issues, min_severity='low')
            
            if filtered_issues:
                deduplicated_issues[file_path] = filtered_issues
        
        all_issues = deduplicated_issues
        total_issues = sum(len(issues) for issues in all_issues.values())
        logger.info(f"Found {total_issues} issues across {len(all_issues)} files (after deduplication and prioritization)")
        
        # Show issue breakdown by type
        if verbose:
            all_issues_flat = []
            for issues in all_issues.values():
                all_issues_flat.extend(issues)
            
            grouped = group_issues_by_type(all_issues_flat)
            logger.info("Issue breakdown by type:")
            for issue_type, type_issues in grouped.items():
                logger.info(f"  {issue_type}: {len(type_issues)} issues")
        
        # Phase 3: Generate fixes using LLM
        logger.info("Generating fixes using LLM...")
        fixes = {}
        
        # Try to use tqdm for progress bar
        try:
            progress_bar = tqdm(all_issues.items(), desc="Generating fixes", unit="file")
        except ImportError:
            progress_bar = all_issues.items()
        
        for file_path, issues in progress_bar:
            logger.debug(f"Generating fix for {file_path}")
            fix = generate_fix(Path(file_path), issues, model, runner, timeout, retries)
            if fix:
                fixes[file_path] = fix
            else:
                logger.warning(f"Failed to generate fix for {file_path}")
        
        total_issues = sum(len(issues) for issues in all_issues.values())
        logger.info(f"Generated fixes for {len(fixes)} files")
        
        # Phase 4: Git operations
        if not dry_run:
            if local_only:
                # Apply fixes directly to files
                logger.info("Applying fixes locally...")
                files_modified = 0
                for file_path, fixed_content in fixes.items():
                    try:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(fixed_content)
                        files_modified += 1
                        logger.info(f"Fixed: {file_path}")
                    except Exception as e:
                        logger.error(f"Failed to write {file_path}: {e}")
                
                logger.info(f"Applied fixes to {files_modified} files locally")
                
            else:
                # Git workflow
                logger.info("Creating git branch...")
                if not create_branch(repo_path, branch):
                    logger.error("Failed to create branch")
                    return
                
                logger.info("Applying fixes...")
                if not apply_fixes(repo_path, fixes):
                    logger.error("Failed to apply fixes")
                    return
                
                logger.info("Committing changes...")
                commit_message = f"CodeFixer: Fix {len(fixes)} files with {total_issues} issues"
                if not commit_changes(repo_path, commit_message):
                    logger.error("Failed to commit changes")
                    return
                
                if not no_push:
                    logger.info("Pushing branch and creating PR...")
                    if not push_and_pr(repo_path, branch, commit_message, fixes, all_issues, show_diff_in_pr):
                        logger.error("Failed to push branch or create PR")
                        return
                else:
                    logger.info("Skipping push (--no-push flag)")
        else:
            logger.info("Dry run mode - no changes applied")
            
            # Show detailed information in dry-run mode
            if show_issues or show_diff or output == 'json':
                logger.info("DRY RUN - Would apply the following fixes:")
                
                for file_path, fix in fixes.items():
                    # Show issues if requested
                    if show_issues:
                        show_issues_for_file(file_path, all_issues[file_path])
                    
                    # Show diff if requested
                    if show_diff:
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                original_content = f.read()
                            show_colored_diff(file_path, original_content, fix)
                        except Exception as e:
                            logger.warning(f"Could not read {file_path} for diff: {e}")
                    
                    # Count changed lines
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            original_lines = f.read().splitlines()
                        fixed_lines = fix.splitlines()
                        diff_lines = list(difflib.unified_diff(original_lines, fixed_lines, fromfile=f"a/{file_path}", tofile=f"b/{file_path}", lineterm=''))
                        num_changed_lines = sum(1 for l in diff_lines if l.startswith('+') or l.startswith('-'))
                    except Exception as e:
                        logger.warning(f"Could not count changes for {file_path}: {e}")
                        num_changed_lines = len(fix.splitlines())
                    
                    logger.info(f"  {file_path}: {num_changed_lines} changed lines")
                
                # JSON output
                if output == 'json':
                    import json
                    result = {
                        'languages_detected': list(languages.keys()),
                        'files_analyzed': len(all_issues),
                        'total_issues': sum(len(issues) for issues in all_issues.values()),
                        'files_with_fixes': len(fixes),
                        'dry_run': True,
                        'fixes': {}
                    }
                    
                    for file_path, fix in fixes.items():
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                original_content = f.read()
                            diff = list(difflib.unified_diff(
                                original_content.splitlines(keepends=True), 
                                fix.splitlines(keepends=True), 
                                fromfile=f"a/{file_path}", 
                                tofile=f"b/{file_path}"
                            )) if show_diff else None
                        except Exception:
                            diff = None
                        
                        result['fixes'][file_path] = {
                            'num_changed_lines': len(fix.splitlines()),
                            'issues': all_issues[file_path],
                            'diff': diff
                        }
                    
                    print(json.dumps(result, indent=2))
        
        logger.info("CodeFixer completed successfully")
        
        # Generate report if requested
        if report:
            generate_report(repo_path, languages, all_issues, fixes, model, runner, dry_run, report)
        
    except Exception as e:
        logger.error(f"CodeFixer failed: {e}")
        sys.exit(1)

def list_available_models():
    """List available LLM models."""
    print("Available LLM Models:")
    print("\nOllama Models (recommended):")
    print("  smollm2:135m     - Very fast, good for simple fixes")
    print("  phi3:3b          - Good balance of speed and quality")
    print("  gemma:2b         - Reliable, good code understanding")
    print("  llama3.2:3b      - Excellent code generation")
    print("  codellama:7b     - Specialized for code (larger)")
    print("  deepseek-coder:6.7b - Code-focused model")
    
    print("\nTo install a model with Ollama:")
    print("  ollama pull <model-name>")
    print("\nTo see all available models:")
    print("  ollama list")
    
    print("\nllama.cpp Models:")
    print("  Use any GGUF model file")
    print("  Download from: https://huggingface.co/models?search=gguf")
    print("  Example: llama-3.2-3b.Q4_K_M.gguf")

if __name__ == '__main__':
    main() 