#!/usr/bin/env python3
"""
CodeFixer CLI - A local-only command-line utility for automated code fixing.
"""

import click
import os
import sys
from pathlib import Path

# Import our modules
from languages import detect_languages
from linters.python_linter import run_python_linter
from linters.js_linter import run_js_linter
from llm import generate_fix
from git_utils import create_branch, apply_fixes, push_and_pr
from logger import setup_logger

logger = setup_logger()

@click.command()
@click.option('--repo', required=True, help='Path to the git repository')
@click.option('--branch', default='codefixer-fixes', help='Branch name for fixes')
@click.option('--model', default='llama-7b', help='Local LLM model to use')
@click.option('--runner', default='llama.cpp', help='LLM runner (llama.cpp, ollama)')
@click.option('--no-push', is_flag=True, help='Skip pushing branch and creating PR')
@click.option('--dry-run', is_flag=True, help='Show what would be done without applying changes')
@click.option('--output', type=click.Choice(['text', 'json']), default='text', help='Output format')
@click.option('--verbose', '-v', is_flag=True, help='Verbose logging')
def main(repo, branch, model, runner, no_push, dry_run, output, verbose):
    """CodeFixer - Automated code fixing with local LLM."""
    
    if verbose:
        logger.setLevel('DEBUG')
    
    logger.info(f"Starting CodeFixer on repository: {repo}")
    
    # Validate repository path
    repo_path = Path(repo)
    if not repo_path.exists():
        logger.error(f"Repository path does not exist: {repo}")
        sys.exit(1)
    
    if not (repo_path / '.git').exists():
        logger.error(f"Not a git repository: {repo}")
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
        for lang, files in languages.items():
            logger.info(f"Linting {lang} files...")
            if lang == 'python':
                issues = run_python_linter(files, repo_path)
            elif lang == 'javascript':
                issues = run_js_linter(files, repo_path)
            else:
                logger.warning(f"No linter configured for {lang}")
                continue
            
            if issues:
                all_issues.update(issues)
        
        if not all_issues:
            logger.info("No linting issues found")
            return
        
        logger.info(f"Found {sum(len(issues) for issues in all_issues.values())} issues across {len(all_issues)} files")
        
        # Phase 3: Generate fixes with LLM
        logger.info("Generating fixes with LLM...")
        fixes = {}
        for file_path, issues in all_issues.items():
            logger.debug(f"Fixing {file_path}...")
            try:
                fix = generate_fix(file_path, issues, model, runner)
                if fix:
                    fixes[file_path] = fix
            except Exception as e:
                logger.error(f"Failed to generate fix for {file_path}: {e}")
        
        if not fixes:
            logger.warning("No fixes generated")
            return
        
        logger.info(f"Generated fixes for {len(fixes)} files")
        
        # Phase 4: Apply fixes and create PR
        if dry_run:
            logger.info("DRY RUN - Would apply the following fixes:")
            for file_path, fix in fixes.items():
                logger.info(f"  {file_path}: {len(fix)} changes")
            return
        
        # Create branch and apply fixes
        logger.info(f"Creating branch: {branch}")
        create_branch(repo_path, branch)
        
        logger.info("Applying fixes...")
        apply_fixes(repo_path, fixes)
        
        if not no_push:
            logger.info("Pushing branch and creating PR...")
            pr_url = push_and_pr(repo_path, branch, all_issues, fixes)
            if pr_url:
                logger.info(f"Pull request created: {pr_url}")
            else:
                logger.warning("Failed to create pull request")
        else:
            logger.info("Skipping push (--no-push flag)")
        
        logger.info("CodeFixer completed successfully")
        
    except Exception as e:
        logger.error(f"CodeFixer failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 