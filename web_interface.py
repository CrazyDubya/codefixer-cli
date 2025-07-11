"""
Web interface for CodeFixer.
"""

import os
import json
import tempfile
from pathlib import Path
from typing import Dict, Any, List
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
import zipfile
import shutil

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
from llm import generate_fix, list_available_models, detect_llm_runner
from issue_deduplicator import deduplicate_issues, prioritize_issues, filter_issues_by_severity

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()

@app.route('/')
def index():
    """Main page."""
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_repository():
    """Handle repository upload."""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.endswith('.zip'):
            return jsonify({'error': 'Please upload a ZIP file'}), 400
        
        # Create temporary directory for extraction
        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, secure_filename(file.filename))
        file.save(zip_path)
        
        # Extract ZIP file
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # Find the repository root (first directory with .git or containing source files)
        repo_path = find_repository_root(temp_dir)
        
        if not repo_path:
            return jsonify({'error': 'No valid repository found in ZIP'}), 400
        
        # Store repository path in session
        session_id = request.form.get('session_id', 'default')
        session_data = {
            'repo_path': str(repo_path),
            'temp_dir': temp_dir
        }
        
        # In a real implementation, you'd store this in a database or cache
        app.config['sessions'] = getattr(app.config, 'sessions', {})
        app.config['sessions'][session_id] = session_data
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'message': 'Repository uploaded successfully'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analyze', methods=['POST'])
def analyze_repository():
    """Analyze repository for languages and issues."""
    try:
        session_id = request.json.get('session_id', 'default')
        session_data = app.config.get('sessions', {}).get(session_id)
        
        if not session_data:
            return jsonify({'error': 'No repository found. Please upload first.'}), 400
        
        repo_path = Path(session_data['repo_path'])
        
        # Detect languages
        languages = detect_languages(repo_path)
        
        # Run linters
        all_issues = {}
        env_manager = EnvironmentManager()
        
        # Initialize new linters
        go_linter = GoLinter(env_manager)
        rust_linter = RustLinter(env_manager)
        java_linter = JavaLinter(env_manager)
        
        for lang, files in languages.items():
            file_paths = [str(f) for f in files]
            
            if lang == 'python':
                issues = run_python_linter(file_paths, repo_path)
            elif lang == 'javascript':
                issues = run_js_linter(file_paths, repo_path)
            elif lang == 'html':
                issues = run_html_linter(file_paths, repo_path)
            elif lang == 'css':
                issues = run_css_linter(file_paths, repo_path)
            elif lang == 'yaml':
                issues = run_yaml_linter(file_paths, repo_path)
            elif lang == 'go':
                issues = go_linter.lint_files(repo_path, file_paths)
            elif lang == 'rust':
                issues = rust_linter.lint_files(repo_path, file_paths)
            elif lang == 'java':
                issues = java_linter.lint_files(repo_path, file_paths)
            else:
                continue
            
            all_issues.update(issues)
        
        # Deduplicate and prioritize issues
        deduplicated_issues = {}
        for file_path, issues in all_issues.items():
            unique_issues = deduplicate_issues(issues)
            prioritized_issues = prioritize_issues(unique_issues)
            filtered_issues = filter_issues_by_severity(prioritized_issues, min_severity='low')
            
            if filtered_issues:
                deduplicated_issues[file_path] = filtered_issues
        
        # Update session data
        session_data['languages'] = {lang: [str(f) for f in files] for lang, files in languages.items()}
        session_data['issues'] = deduplicated_issues
        app.config['sessions'][session_id] = session_data
        
        return jsonify({
            'success': True,
            'languages': list(languages.keys()),
            'total_files': sum(len(files) for files in languages.values()),
            'total_issues': sum(len(issues) for issues in deduplicated_issues.values()),
            'files_with_issues': len(deduplicated_issues)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/fix', methods=['POST'])
def fix_issues():
    """Generate fixes for issues."""
    try:
        session_id = request.json.get('session_id', 'default')
        model = request.json.get('model', 'smollm2:135m')
        runner = request.json.get('runner', 'auto')
        timeout = request.json.get('timeout', 30)
        
        session_data = app.config.get('sessions', {}).get(session_id)
        
        if not session_data or 'issues' not in session_data:
            return jsonify({'error': 'No analysis found. Please analyze first.'}), 400
        
        repo_path = Path(session_data['repo_path'])
        issues = session_data['issues']
        
        # Generate fixes
        fixes = {}
        for file_path, file_issues in issues.items():
            fix = generate_fix(Path(file_path), file_issues, model, runner, timeout)
            if fix:
                fixes[file_path] = fix
        
        # Update session data
        session_data['fixes'] = fixes
        app.config['sessions'][session_id] = session_data
        
        return jsonify({
            'success': True,
            'files_fixed': len(fixes),
            'total_files_with_issues': len(issues)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/models', methods=['GET'])
def get_models():
    """Get available models for the specified runner."""
    try:
        runner = request.args.get('runner', 'auto')
        models = list_available_models(runner)
        
        return jsonify({
            'success': True,
            'runner': runner,
            'models': models
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download', methods=['POST'])
def download_fixes():
    """Download fixed files as ZIP."""
    try:
        session_id = request.json.get('session_id', 'default')
        session_data = app.config.get('sessions', {}).get(session_id)
        
        if not session_data or 'fixes' not in session_data:
            return jsonify({'error': 'No fixes found. Please generate fixes first.'}), 400
        
        repo_path = Path(session_data['repo_path'])
        fixes = session_data['fixes']
        
        # Create temporary ZIP file
        zip_path = tempfile.mktemp(suffix='.zip')
        
        with zipfile.ZipFile(zip_path, 'w') as zip_file:
            for file_path, fixed_content in fixes.items():
                # Add fixed file to ZIP
                zip_file.writestr(f"fixed/{file_path}", fixed_content)
                
                # Also add original file for comparison
                original_path = repo_path / file_path
                if original_path.exists():
                    zip_file.write(original_path, f"original/{file_path}")
        
        return send_file(zip_path, as_attachment=True, download_name='codefixer-fixes.zip')
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cleanup', methods=['POST'])
def cleanup_session():
    """Clean up session data and temporary files."""
    try:
        session_id = request.json.get('session_id', 'default')
        session_data = app.config.get('sessions', {}).get(session_id)
        
        if session_data and 'temp_dir' in session_data:
            shutil.rmtree(session_data['temp_dir'], ignore_errors=True)
        
        # Remove session data
        if 'sessions' in app.config:
            app.config['sessions'].pop(session_id, None)
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def find_repository_root(directory: str) -> Path:
    """Find the repository root in the extracted directory."""
    for root, dirs, files in os.walk(directory):
        # Check if this directory contains a .git folder
        if '.git' in dirs:
            return Path(root)
        
        # Check if this directory contains source files
        source_files = [f for f in files if f.endswith(('.py', '.js', '.ts', '.java', '.go', '.rs'))]
        if source_files:
            return Path(root)
    
    return None

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 