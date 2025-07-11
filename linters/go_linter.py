"""
Go linter module using golangci-lint.
"""

import os
import subprocess
import json
import tempfile
from typing import List, Dict, Any, Optional
from .env_manager import EnvironmentManager


class GoLinter:
    """Go linter using golangci-lint."""
    
    def __init__(self, env_manager: EnvironmentManager):
        self.env_manager = env_manager
        self.linter_name = "golangci-lint"
        
    def setup_environment(self, repo_path: str) -> str:
        """Set up Go environment with golangci-lint."""
        env_path = self.env_manager.get_env_path(repo_path, "go")
        
        if not self.env_manager.env_exists(env_path):
            self.env_manager.create_env(env_path)
            
            # Install golangci-lint
            try:
                subprocess.run([
                    "go", "install", "github.com/golangci/golangci-lint/cmd/golangci-lint@latest"
                ], cwd=env_path, check=True, capture_output=True)
            except subprocess.CalledProcessError:
                # Try alternative installation method
                try:
                    subprocess.run([
                        "curl", "-sSfL", "https://raw.githubusercontent.com/golangci/golangci-lint/master/install.sh",
                        "|", "sh", "-s", "--", "-b", os.path.join(env_path, "bin")
                    ], cwd=env_path, check=True, shell=True, capture_output=True)
                except subprocess.CalledProcessError:
                    raise RuntimeError("Failed to install golangci-lint")
        
        return env_path
    
    def create_config(self, repo_path: str) -> str:
        """Create golangci-lint configuration file."""
        config_content = """# golangci-lint configuration
run:
  timeout: 5m
  go: "1.21"
  modules-download-mode: readonly

linters:
  enable:
    - gofmt
    - goimports
    - govet
    - errcheck
    - staticcheck
    - unused
    - gosimple
    - structcheck
    - varcheck
    - ineffassign
    - deadcode
    - typecheck
    - gocyclo
    - goconst
    - dupl
    - misspell
    - unparam
    - nakedret
    - prealloc
    - gocritic
    - gosec
    - maligned
    - depguard
    - noctx
    - rowserrcheck
    - sqlclosecheck
    - gochecknoinits
    - gochecknoglobals
    - gomnd
    - gomoddirectives
    - gomodguard
    - goprintffuncname
    - gosec
    - gosimple
    - govet
    - ineffassign
    - lll
    - misspell
    - nakedret
    - noctx
    - nolintlint
    - prealloc
    - rowserrcheck
    - sqlclosecheck
    - staticcheck
    - structcheck
    - stylecheck
    - typecheck
    - unconvert
    - unparam
    - unused
    - varcheck
    - whitespace

linters-settings:
  gocyclo:
    min-complexity: 15
  dupl:
    threshold: 100
  goconst:
    min-len: 2
    min-occurrences: 3
  misspell:
    locale: US
  lll:
    line-length: 140
  gomnd:
    checks: argument,case,condition,operation,return,assign
  gocritic:
    enabled-tags:
      - diagnostic
      - experimental
      - opinionated
      - performance
      - style
    disabled-checks:
      - dupImport # https://github.com/go-critic/go-critic/issues/845
      - ifElseChain
      - octalLiteral
      - whyNoLint
      - wrapperFunc

issues:
  exclude-rules:
    - path: _test\\.go
      linters:
        - gomnd
        - goconst
        - gocyclo
        - gosec
        - gocritic
        - gochecknoinits
        - gochecknoglobals
        - gomnd
        - goprintffuncname
        - gosec
        - gosimple
        - govet
        - ineffassign
        - lll
        - misspell
        - nakedret
        - noctx
        - nolintlint
        - prealloc
        - rowserrcheck
        - sqlclosecheck
        - staticcheck
        - structcheck
        - stylecheck
        - typecheck
        - unconvert
        - unparam
        - unused
        - varcheck
        - whitespace
  max-issues-per-linter: 0
  max-same-issues: 0
"""
        
        config_path = os.path.join(repo_path, ".golangci.yml")
        with open(config_path, 'w') as f:
            f.write(config_content)
        
        return config_path
    
    def lint_files(self, repo_path: str, files: List[str]) -> List[Dict[str, Any]]:
        """Lint Go files using golangci-lint."""
        if not files:
            return []
        
        env_path = self.setup_environment(repo_path)
        config_path = self.create_config(repo_path)
        
        issues = []
        
        try:
            # Run golangci-lint on the entire repository
            result = subprocess.run([
                os.path.join(env_path, "bin", "golangci-lint"), "run",
                "--config", config_path,
                "--out-format", "json"
            ], cwd=repo_path, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                return []
            
            try:
                lint_output = json.loads(result.stdout)
                for issue in lint_output.get("Issues", []):
                    file_path = issue.get("Pos", {}).get("Filename", "")
                    if file_path and any(f in file_path for f in files):
                        issues.append({
                            "file": file_path,
                            "line": issue.get("Pos", {}).get("Line", 0),
                            "column": issue.get("Pos", {}).get("Column", 0),
                            "message": issue.get("Text", ""),
                            "code": issue.get("FromLinter", ""),
                            "severity": self._map_severity(issue.get("Severity", "medium")),
                            "category": self._categorize_issue(issue.get("FromLinter", ""))
                        })
            except json.JSONDecodeError:
                # Fallback to parsing text output
                for line in result.stdout.split('\n'):
                    if line.strip() and any(f in line for f in files):
                        parsed = self._parse_text_line(line)
                        if parsed:
                            issues.append(parsed)
        
        except subprocess.TimeoutExpired:
            raise RuntimeError("golangci-lint timed out")
        except Exception as e:
            raise RuntimeError(f"golangci-lint failed: {e}")
        
        return issues
    
    def _map_severity(self, severity: str) -> str:
        """Map golangci-lint severity to standard severity."""
        severity_map = {
            "error": "high",
            "warning": "medium",
            "info": "low"
        }
        return severity_map.get(severity.lower(), "medium")
    
    def _categorize_issue(self, linter: str) -> str:
        """Categorize issue based on linter."""
        security_linters = {"gosec"}
        formatting_linters = {"gofmt", "goimports"}
        quality_linters = {"govet", "errcheck", "staticcheck", "unused", "gosimple"}
        
        if linter in security_linters:
            return "security"
        elif linter in formatting_linters:
            return "formatting"
        elif linter in quality_linters:
            return "code_quality"
        else:
            return "code_quality"
    
    def _parse_text_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse golangci-lint text output line."""
        # Example: main.go:10:6: exported function `Foo` should have comment or be unexported (golint)
        try:
            parts = line.split(':', 3)
            if len(parts) >= 4:
                file_path = parts[0]
                line_num = int(parts[1])
                col_num = int(parts[2])
                message = parts[3].strip()
                
                # Extract linter name from message
                linter = "unknown"
                if '(' in message:
                    linter = message.split('(')[-1].rstrip(')')
                    message = message.split('(')[0].strip()
                
                return {
                    "file": file_path,
                    "line": line_num,
                    "column": col_num,
                    "message": message,
                    "code": linter,
                    "severity": self._map_severity("medium"),
                    "category": self._categorize_issue(linter)
                }
        except (ValueError, IndexError):
            pass
        
        return None 