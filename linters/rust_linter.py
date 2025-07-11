"""
Rust linter module using clippy.
"""

import os
import subprocess
import json
from typing import List, Dict, Any, Optional
from .env_manager import EnvironmentManager


class RustLinter:
    """Rust linter using clippy."""
    
    def __init__(self, env_manager: EnvironmentManager):
        self.env_manager = env_manager
        self.linter_name = "clippy"
        
    def setup_environment(self, repo_path: str) -> str:
        """Set up Rust environment with clippy."""
        env_path = self.env_manager.get_env_path(repo_path, "rust")
        
        if not self.env_manager.env_exists(env_path):
            self.env_manager.create_env(env_path)
            
            # Install rustup and clippy
            try:
                # Install rustup if not available
                subprocess.run([
                    "curl", "--proto", "=https", "--tlsv1.2", "-sSf", 
                    "https://sh.rustup.rs", "|", "sh", "-s", "--", "-y"
                ], cwd=env_path, check=True, shell=True, capture_output=True)
                
                # Add clippy component
                rustup_path = os.path.join(env_path, ".cargo", "bin", "rustup")
                subprocess.run([
                    rustup_path, "component", "add", "clippy"
                ], cwd=env_path, check=True, capture_output=True)
                
            except subprocess.CalledProcessError:
                raise RuntimeError("Failed to install Rust and clippy")
        
        return env_path
    
    def create_config(self, repo_path: str) -> str:
        """Create clippy configuration file."""
        config_content = """# Clippy configuration
# This file configures clippy lints for the project

# Allow all lints by default
# Warnings will be treated as errors
# This is a strict configuration for maximum code quality

# Disable some overly strict lints that might be too opinionated
# Uncomment and modify as needed for your project

# [profile.dev]
# opt-level = 0
# debug = true

# [profile.release]
# opt-level = 3
# debug = false

# [profile.test]
# opt-level = 0
# debug = true

# Clippy configuration
[workspace]
members = ["."]

[package]
name = "codefixer-rust"
version = "0.1.0"
edition = "2021"

[dependencies]

# Clippy lints configuration
# These are the default clippy lints that will be enabled
# You can customize this list based on your project needs

# Performance lints
# - clippy::perf

# Correctness lints  
# - clippy::correctness

# Style lints
# - clippy::style

# Complexity lints
# - clippy::complexity

# Suspicious lints
# - clippy::suspicious

# Pedantic lints
# - clippy::pedantic

# Nursery lints (experimental)
# - clippy::nursery

# Cargo lints
# - clippy::cargo
"""
        
        config_path = os.path.join(repo_path, "Cargo.toml")
        if not os.path.exists(config_path):
            with open(config_path, 'w') as f:
                f.write(config_content)
        
        return config_path
    
    def lint_files(self, repo_path: str, files: List[str]) -> List[Dict[str, Any]]:
        """Lint Rust files using clippy."""
        if not files:
            return []
        
        env_path = self.setup_environment(repo_path)
        config_path = self.create_config(repo_path)
        
        issues = []
        
        try:
            # Run clippy on the entire project
            cargo_path = os.path.join(env_path, ".cargo", "bin", "cargo")
            result = subprocess.run([
                cargo_path, "clippy",
                "--message-format=json",
                "--all-targets",
                "--all-features"
            ], cwd=repo_path, capture_output=True, text=True, timeout=300)
            
            # Parse JSON output
            for line in result.stdout.split('\n'):
                if line.strip():
                    try:
                        message = json.loads(line)
                        if message.get("reason") == "compiler-message":
                            level = message.get("message", {}).get("level", "warning")
                            spans = message.get("message", {}).get("spans", [])
                            message_text = message.get("message", {}).get("message", "")
                            code = message.get("message", {}).get("code", {}).get("code", "")
                            
                            for span in spans:
                                file_path = span.get("file_name", "")
                                if file_path and any(f in file_path for f in files):
                                    issues.append({
                                        "file": file_path,
                                        "line": span.get("line_start", 0),
                                        "column": span.get("column_start", 0),
                                        "message": message_text,
                                        "code": code,
                                        "severity": self._map_severity(level),
                                        "category": self._categorize_issue(code)
                                    })
                    except json.JSONDecodeError:
                        continue
        
        except subprocess.TimeoutExpired:
            raise RuntimeError("clippy timed out")
        except Exception as e:
            raise RuntimeError(f"clippy failed: {e}")
        
        return issues
    
    def _map_severity(self, level: str) -> str:
        """Map clippy severity to standard severity."""
        severity_map = {
            "error": "high",
            "warning": "medium",
            "note": "low",
            "help": "low"
        }
        return severity_map.get(level.lower(), "medium")
    
    def _categorize_issue(self, code: str) -> str:
        """Categorize issue based on clippy code."""
        security_codes = {"clippy::security"}
        formatting_codes = {"clippy::style"}
        performance_codes = {"clippy::perf"}
        complexity_codes = {"clippy::complexity"}
        
        if any(sec in code.lower() for sec in security_codes):
            return "security"
        elif any(fmt in code.lower() for fmt in formatting_codes):
            return "formatting"
        elif any(perf in code.lower() for perf in performance_codes):
            return "performance"
        elif any(comp in code.lower() for comp in complexity_codes):
            return "code_quality"
        else:
            return "code_quality" 