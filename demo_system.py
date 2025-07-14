"""
Comprehensive demo system for CodeFixer with visualizations and testing.
"""

import os
import tempfile
import shutil
import subprocess
import time
import json
from pathlib import Path
from typing import Dict, Any, List
import webbrowser
import threading

from performance_monitor import PerformanceMonitor, PerformanceVisualizer, AnalyticsReporter
from languages import detect_languages
from linters.python_linter import run_python_linter
from linters.js_linter import run_js_linter
from linters.html_linter import run_html_linter
from linters.css_linter import run_css_linter
from linters.yaml_linter import run_yaml_linter
from linters.env_manager import EnvManager
from llm import generate_fix, list_available_models, detect_llm_runner
from issue_deduplicator import deduplicate_issues, prioritize_issues, filter_issues_by_severity

class CodeFixerDemo:
    """Comprehensive demo system for CodeFixer."""
    
    def __init__(self):
        self.temp_dir = None
        self.monitor = PerformanceMonitor()
        self.visualizer = PerformanceVisualizer(self.monitor)
        self.reporter = AnalyticsReporter(self.monitor, self.visualizer)
        self.demo_repos = {}
        
    def create_demo_repositories(self):
        """Create various demo repositories with different languages and issues."""
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # 1. Python repository with various issues
        python_repo = self.temp_dir / "python-demo"
        python_repo.mkdir()
        self._create_python_demo(python_repo)
        self.demo_repos["python"] = python_repo
        
        # 2. JavaScript/TypeScript repository
        js_repo = self.temp_dir / "javascript-demo"
        js_repo.mkdir()
        self._create_javascript_demo(js_repo)
        self.demo_repos["javascript"] = js_repo
        
        # 3. Multi-language repository
        multi_repo = self.temp_dir / "multi-language-demo"
        multi_repo.mkdir()
        self._create_multi_language_demo(multi_repo)
        self.demo_repos["multi"] = multi_repo
        
        # 4. Go repository
        go_repo = self.temp_dir / "go-demo"
        go_repo.mkdir()
        self._create_go_demo(go_repo)
        self.demo_repos["go"] = go_repo
        
        # 5. Rust repository
        rust_repo = self.temp_dir / "rust-demo"
        rust_repo.mkdir()
        self._create_rust_demo(rust_repo)
        self.demo_repos["rust"] = rust_repo
        
        print(f"✅ Created {len(self.demo_repos)} demo repositories in {self.temp_dir}")
        
    def _create_python_demo(self, repo_path: Path):
        """Create Python demo with various issues."""
        # Main application
        (repo_path / "main.py").write_text("""
import os,sys
from typing import *

def bad_function(  ):
    x=1
    y=2
    print(x+y)
    return x+y

def unused_function():
    pass

def long_function_with_many_parameters(a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p, q, r, s, t, u, v, w, x, y, z):
    return a + b + c + d + e + f + g + h + i + j + k + l + m + n + o + p + q + r + s + t + u + v + w + x + y + z

class BadClass:
    def __init__(self):
        self.x=1
        self.y=2
    
    def method(self):
        print("This is a very long line that exceeds the maximum line length and should be flagged by the linter for being too long")
        return self.x+self.y

if __name__=="__main__":
    bad_function()
""")
        
        # Configuration files
        (repo_path / "requirements.txt").write_text("""
requests==2.31.0
pandas==2.0.0
numpy==1.24.0
""")
        
        (repo_path / "config.yaml").write_text("""
database:
  host: localhost
  port: 5432
  name: myapp
  user: admin
  password: secret123

logging:
  level: INFO
  file: app.log
""")
        
        # Initialize git
        subprocess.run(["git", "init"], cwd=repo_path, capture_output=True)
        subprocess.run(["git", "add", "."], cwd=repo_path, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_path, capture_output=True)
        
    def _create_javascript_demo(self, repo_path: Path):
        """Create JavaScript/TypeScript demo."""
        # JavaScript file
        (repo_path / "app.js").write_text("""
var x = 1;
var y = 2;
console.log(x + y);

function badFunction() {
    var unused = "this is unused";
    console.log("Hello World");
}

function longFunction(a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p, q, r, s, t, u, v, w, x, y, z) {
    return a + b + c + d + e + f + g + h + i + j + k + l + m + n + o + p + q + r + s + t + u + v + w + x + y + z;
}

if (x == 1) {
    console.log("x is 1");
}
""")
        
        # TypeScript file
        (repo_path / "typescript.ts").write_text("""
interface User {
    name: string;
    age: number;
}

function processUser(user: User): void {
    console.log(user.name);
    console.log(user.age);
}

const user: User = {
    name: "John",
    age: 30
};

processUser(user);
""")
        
        # HTML file
        (repo_path / "index.html").write_text("""
<!DOCTYPE html>
<html>
<head>
    <title>Demo App</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Welcome to CodeFixer Demo</h1>
        <p>This is a demo application with various linting issues.</p>
    </div>
    <script src="app.js"></script>
</body>
</html>
""")
        
        # CSS file
        (repo_path / "styles.css").write_text("""
body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 20px;
    background-color: #f0f0f0;
}

.container {
    max-width: 800px;
    margin: 0 auto;
    background-color: white;
    padding: 20px;
    border-radius: 5px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}

h1 {
    color: #333;
    margin-bottom: 20px;
}

p {
    line-height: 1.6;
    color: #666;
}
""")
        
        # Package.json
        (repo_path / "package.json").write_text("""
{
  "name": "codefixer-demo",
  "version": "1.0.0",
  "description": "Demo application for CodeFixer",
  "main": "app.js",
  "scripts": {
    "test": "echo \\"Error: no test specified\\" && exit 1"
  },
  "dependencies": {
    "express": "^4.18.0",
    "lodash": "^4.17.21"
  },
  "devDependencies": {
    "eslint": "^8.0.0",
    "prettier": "^2.8.0"
  }
}
""")
        
        # Initialize git
        subprocess.run(["git", "init"], cwd=repo_path, capture_output=True)
        subprocess.run(["git", "add", "."], cwd=repo_path, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_path, capture_output=True)
        
    def _create_multi_language_demo(self, repo_path: Path):
        """Create multi-language demo."""
        # Python
        (repo_path / "python_app.py").write_text("""
def hello_world():
    print("Hello from Python!")
    return True
""")
        
        # JavaScript
        (repo_path / "js_app.js").write_text("""
function helloWorld() {
    console.log("Hello from JavaScript!");
}
""")
        
        # Go
        (repo_path / "go_app.go").write_text("""
package main

import "fmt"

func main() {
    fmt.Println("Hello from Go!")
}
""")
        
        # Rust
        (repo_path / "rust_app.rs").write_text("""
fn main() {
    println!("Hello from Rust!");
}
""")
        
        # Java
        (repo_path / "JavaApp.java").write_text("""
public class JavaApp {
    public static void main(String[] args) {
        System.out.println("Hello from Java!");
    }
}
""")
        
        # Dockerfile
        (repo_path / "Dockerfile").write_text("""
FROM python:3.9
COPY . .
CMD ["python", "python_app.py"]
""")
        
        # Initialize git
        subprocess.run(["git", "init"], cwd=repo_path, capture_output=True)
        subprocess.run(["git", "add", "."], cwd=repo_path, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_path, capture_output=True)
        
    def _create_go_demo(self, repo_path: Path):
        """Create Go demo."""
        # Go module
        (repo_path / "go.mod").write_text("""
module codefixer-demo

go 1.21
""")
        
        # Main Go file
        (repo_path / "main.go").write_text("""
package main

import (
    "fmt"
    "os"
)

func main() {
    fmt.Println("Hello from Go!")
    
    // Unused variable
    unused := "this is unused"
    
    // Long function
    result := longFunction(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20)
    fmt.Println(result)
}

func longFunction(a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p, q, r, s, t int) int {
    return a + b + c + d + e + f + g + h + i + j + k + l + m + n + o + p + q + r + s + t
}
""")
        
        # Initialize git
        subprocess.run(["git", "init"], cwd=repo_path, capture_output=True)
        subprocess.run(["git", "add", "."], cwd=repo_path, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_path, capture_output=True)
        
    def _create_rust_demo(self, repo_path: Path):
        """Create Rust demo."""
        # Cargo.toml
        (repo_path / "Cargo.toml").write_text("""
[package]
name = "codefixer-demo"
version = "0.1.0"
edition = "2021"

[dependencies]
""")
        
        # Create src directory
        (repo_path / "src").mkdir(exist_ok=True)
        # Main Rust file
        (repo_path / "src/main.rs").write_text("""
fn main() {
    println!("Hello from Rust!");
    
    // Unused variable
    let unused = "this is unused";
    
    // Long function
    let result = long_function(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20);
    println!("Result: {}", result);
}

fn long_function(a: i32, b: i32, c: i32, d: i32, e: i32, f: i32, g: i32, h: i32, i: i32, j: i32, k: i32, l: i32, m: i32, n: i32, o: i32, p: i32, q: i32, r: i32, s: i32, t: i32) -> i32 {
    a + b + c + d + e + f + g + h + i + j + k + l + m + n + o + p + q + r + s + t
}
""")
        
        # Initialize git
        subprocess.run(["git", "init"], cwd=repo_path, capture_output=True)
        subprocess.run(["git", "add", "."], cwd=repo_path, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_path, capture_output=True)
        
    def run_comprehensive_demo(self):
        """Run comprehensive demo with all features."""
        print("🚀 Starting CodeFixer Comprehensive Demo")
        print("=" * 50)
        
        # Create demo repositories
        self.create_demo_repositories()
        
        # Start performance monitoring
        self.monitor.start_monitoring()
        
        all_results = {}
        
        # Test each repository
        for repo_name, repo_path in self.demo_repos.items():
            print(f"\n📁 Testing {repo_name.upper()} repository...")
            results = self._test_repository(repo_name, repo_path)
            all_results[repo_name] = results
            
        # Stop monitoring
        self.monitor.stop_monitoring()
        
        # Generate comprehensive report
        self._generate_comprehensive_report(all_results)
        
        # Show results
        self._show_demo_results(all_results)
        
    def _test_repository(self, repo_name: str, repo_path: Path) -> Dict[str, Any]:
        """Test a single repository."""
        start_time = time.time()
        
        # Detect languages
        languages = detect_languages(repo_path)
        
        # Run linters
        all_issues = {}
        env_manager = EnvManager()
        
        # Initialize linters (Go, Rust, Java not implemented in demo)
        pass
        
        linter_start = time.time()
        
        for lang, files in languages.items():
            file_paths = [str(f) for f in files]
            
            try:
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
                elif lang in ['go', 'rust', 'java']:
                    # Skip unsupported languages in demo
                    continue
                else:
                    continue
                
                all_issues.update(issues)
                
            except Exception as e:
                print(f"  ⚠️  Linting failed for {lang}: {e}")
        
        linter_duration = time.time() - linter_start
        total_files = sum(len(files) for files in languages.values())
        total_issues = sum(len(issues) for issues in all_issues.values())
        
        # Update performance metrics
        self.monitor.update_linter_metrics(linter_duration, total_files, total_issues)
        
        # Deduplicate and prioritize issues
        deduplicated_issues = {}
        for file_path, issues in all_issues.items():
            unique_issues = deduplicate_issues(issues)
            prioritized_issues = prioritize_issues(unique_issues)
            filtered_issues = filter_issues_by_severity(prioritized_issues, min_severity='low')
            
            if filtered_issues:
                deduplicated_issues[file_path] = filtered_issues
        
        # Generate fixes (simulated for demo)
        llm_start = time.time()
        fixes = {}
        llm_requests = 0
        llm_tokens = 0
        
        for file_path, issues in list(deduplicated_issues.items())[:3]:  # Limit for demo
            try:
                # Simulate LLM fix generation
                time.sleep(0.1)  # Simulate processing time
                fixes[file_path] = "// Simulated fix for demo purposes"
                llm_requests += 1
                llm_tokens += 100
            except Exception as e:
                print(f"  ⚠️  Fix generation failed for {file_path}: {e}")
        
        llm_duration = time.time() - llm_start
        self.monitor.update_llm_metrics(llm_duration, llm_requests, llm_tokens, len(fixes))
        
        total_duration = time.time() - start_time
        
        return {
            "languages": languages,
            "issues": deduplicated_issues,
            "fixes": fixes,
            "metrics": {
                "total_files": total_files,
                "total_issues": total_issues,
                "files_with_issues": len(deduplicated_issues),
                "files_fixed": len(fixes),
                "linter_duration": linter_duration,
                "llm_duration": llm_duration,
                "total_duration": total_duration
            }
        }
        
    def _generate_comprehensive_report(self, all_results: Dict[str, Dict]):
        """Generate comprehensive analytics report."""
        print("\n📊 Generating comprehensive analytics report...")
        
        # Aggregate data
        all_languages = {}
        all_issues = {}
        
        for repo_name, results in all_results.items():
            for lang, files in results["languages"].items():
                if lang not in all_languages:
                    all_languages[lang] = 0
                all_languages[lang] += len(files)
            
            for file_path, issues in results["issues"].items():
                all_issues[f"{repo_name}/{file_path}"] = issues
        
        # Generate report
        report_path = self.reporter.generate_report(all_languages, all_issues, "demo_analytics")
        
        print(f"✅ Analytics report generated: {report_path}")
        
        # Open report in browser
        html_path = Path(report_path) / "report.html"
        if html_path.exists():
            webbrowser.open(f"file://{html_path.absolute()}")
            
    def _show_demo_results(self, all_results: Dict[str, Dict]):
        """Show demo results summary."""
        print("\n" + "=" * 50)
        print("🎯 DEMO RESULTS SUMMARY")
        print("=" * 50)
        
        total_files = 0
        total_issues = 0
        total_fixes = 0
        total_duration = 0
        
        for repo_name, results in all_results.items():
            metrics = results["metrics"]
            total_files += metrics["total_files"]
            total_issues += metrics["total_issues"]
            total_fixes += metrics["files_fixed"]
            total_duration += metrics["total_duration"]
            
            print(f"\n📁 {repo_name.upper()} Repository:")
            print(f"   Files: {metrics['total_files']}")
            print(f"   Languages: {list(results['languages'].keys())}")
            print(f"   Issues: {metrics['total_issues']}")
            print(f"   Files with issues: {metrics['files_with_issues']}")
            print(f"   Files fixed: {metrics['files_fixed']}")
            print(f"   Duration: {metrics['total_duration']:.2f}s")
        
        print(f"\n📊 OVERALL SUMMARY:")
        print(f"   Total repositories: {len(all_results)}")
        print(f"   Total files: {total_files}")
        print(f"   Total issues: {total_issues}")
        print(f"   Total fixes: {total_fixes}")
        print(f"   Total duration: {total_duration:.2f}s")
        print(f"   Average files/second: {total_files/total_duration:.1f}")
        
        # Performance summary
        summary = self.monitor.get_summary()
        if summary:
            print(f"\n⚡ PERFORMANCE METRICS:")
            print(f"   Cache hit rate: {summary['efficiency']['cache_hit_rate']:.1f}%")
            print(f"   Fix rate: {summary['efficiency']['fix_rate']:.1f}%")
            print(f"   Average CPU: {summary['system']['avg_cpu_percent']:.1f}%")
            print(f"   Peak memory: {summary['system']['max_memory_mb']:.1f}MB")
        
        print(f"\n🎉 Demo completed successfully!")
        print(f"📈 Check the generated analytics report for detailed visualizations")
        
    def cleanup(self):
        """Clean up temporary files."""
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            print(f"🧹 Cleaned up temporary files: {self.temp_dir}")

def run_demo():
    """Run the comprehensive demo."""
    demo = CodeFixerDemo()
    try:
        demo.run_comprehensive_demo()
    finally:
        demo.cleanup()

if __name__ == "__main__":
    run_demo() 