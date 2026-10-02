"""
Performance monitoring and analytics for CodeFixer.
"""

import time
import psutil
import threading
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import matplotlib

# Charts are written to files; force a non-interactive backend so CI/headless
# runners (notably Windows Python 3.11/3.12 with broken Tk) never need tkinter.
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.figure import Figure
import seaborn as sns
import pandas as pd
from collections import defaultdict, deque
import numpy as np

@dataclass
class PerformanceMetrics:
    """Performance metrics data structure."""
    timestamp: datetime
    cpu_percent: float
    memory_mb: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_sent_mb: float
    network_recv_mb: float
    active_threads: int
    open_files: int
    linter_duration: float
    llm_duration: float
    total_duration: float
    files_processed: int
    issues_found: int
    fixes_generated: int
    llm_requests: int
    llm_tokens_used: int
    cache_hits: int
    cache_misses: int

class PerformanceMonitor:
    """Real-time performance monitoring system."""
    
    def __init__(self, sample_interval: float = 1.0, max_samples: int = 1000):
        self.sample_interval = sample_interval
        self.max_samples = max_samples
        self.metrics_history = deque(maxlen=max_samples)
        self.is_monitoring = False
        self.monitor_thread = None
        self.start_time = None
        self.end_time = None
        
        # Performance counters
        self.linter_duration = 0.0
        self.llm_duration = 0.0
        self.files_processed = 0
        self.issues_found = 0
        self.fixes_generated = 0
        self.llm_requests = 0
        self.llm_tokens_used = 0
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Initialize psutil
        self.psutil_process = psutil.Process()
        
    def start_monitoring(self):
        """Start performance monitoring."""
        if self.is_monitoring:
            return
            
        self.is_monitoring = True
        self.start_time = datetime.now()
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
    def stop_monitoring(self):
        """Stop performance monitoring."""
        self.is_monitoring = False
        self.end_time = datetime.now()
        if self.monitor_thread:
            self.monitor_thread.join()
            
    def _monitor_loop(self):
        """Main monitoring loop."""
        while self.is_monitoring:
            try:
                metrics = self._collect_metrics()
                self.metrics_history.append(metrics)
                time.sleep(self.sample_interval)
            except Exception as e:
                print(f"Performance monitoring error: {e}")
                
    def _collect_metrics(self) -> PerformanceMetrics:
        """Collect current system metrics."""
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory_info = self.psutil_process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        
        # Disk I/O (cross-platform)
        try:
            disk_io = self.psutil_process.io_counters()
            disk_io_read_mb = disk_io.read_bytes / 1024 / 1024
            disk_io_write_mb = disk_io.write_bytes / 1024 / 1024
        except Exception:
            # Fallback to system-wide if not available
            try:
                disk_io = psutil.disk_io_counters()
                disk_io_read_mb = disk_io.read_bytes / 1024 / 1024
                disk_io_write_mb = disk_io.write_bytes / 1024 / 1024
            except Exception:
                disk_io_read_mb = 0.0
                disk_io_write_mb = 0.0
        
        # Network I/O
        network_io = psutil.net_io_counters()
        network_sent_mb = network_io.bytes_sent / 1024 / 1024
        network_recv_mb = network_io.bytes_recv / 1024 / 1024
        
        # Process metrics
        active_threads = self.psutil_process.num_threads()
        try:
            open_files = len(self.psutil_process.open_files())
        except Exception:
            open_files = 0
        
        return PerformanceMetrics(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            memory_mb=memory_mb,
            disk_io_read_mb=disk_io_read_mb,
            disk_io_write_mb=disk_io_write_mb,
            network_sent_mb=network_sent_mb,
            network_recv_mb=network_recv_mb,
            active_threads=active_threads,
            open_files=open_files,
            linter_duration=self.linter_duration,
            llm_duration=self.llm_duration,
            total_duration=(datetime.now() - self.start_time).total_seconds() if self.start_time else 0,
            files_processed=self.files_processed,
            issues_found=self.issues_found,
            fixes_generated=self.fixes_generated,
            llm_requests=self.llm_requests,
            llm_tokens_used=self.llm_tokens_used,
            cache_hits=self.cache_hits,
            cache_misses=self.cache_misses
        )
        
    def update_linter_metrics(self, duration: float, files: int, issues: int):
        """Update linter-related metrics."""
        self.linter_duration += duration
        self.files_processed += files
        self.issues_found += issues
        
    def update_llm_metrics(self, duration: float, requests: int, tokens: int, fixes: int):
        """Update LLM-related metrics."""
        self.llm_duration += duration
        self.llm_requests += requests
        self.llm_tokens_used += tokens
        self.fixes_generated += fixes
        
    def update_cache_metrics(self, hits: int, misses: int):
        """Update cache-related metrics."""
        self.cache_hits += hits
        self.cache_misses += misses
        
    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        if not self.metrics_history:
            return {}
            
        metrics_list = list(self.metrics_history)
        
        # Fix: use float subtraction for duration
        if self.end_time and self.start_time:
            total_seconds = (self.end_time - self.start_time).total_seconds() if hasattr(self.end_time - self.start_time, 'total_seconds') else float(self.end_time - self.start_time)
        else:
            total_seconds = 0
        
        return {
            "duration": {
                "total_seconds": total_seconds,
                "linter_seconds": self.linter_duration,
                "llm_seconds": self.llm_duration,
                "linter_percent": (self.linter_duration / max(self.linter_duration + self.llm_duration, 1)) * 100,
                "llm_percent": (self.llm_duration / max(self.linter_duration + self.llm_duration, 1)) * 100
            },
            "throughput": {
                "files_per_second": self.files_processed / max(self.linter_duration, 1),
                "issues_per_second": self.issues_found / max(self.linter_duration, 1),
                "fixes_per_second": self.fixes_generated / max(self.llm_duration, 1),
                "llm_requests_per_second": self.llm_requests / max(self.llm_duration, 1)
            },
            "efficiency": {
                "cache_hit_rate": self.cache_hits / max(self.cache_hits + self.cache_misses, 1) * 100,
                "fix_rate": self.fixes_generated / max(self.issues_found, 1) * 100,
                "tokens_per_fix": self.llm_tokens_used / max(self.fixes_generated, 1)
            },
            "system": {
                "avg_cpu_percent": np.mean([m.cpu_percent for m in metrics_list]),
                "max_cpu_percent": np.max([m.cpu_percent for m in metrics_list]),
                "avg_memory_mb": np.mean([m.memory_mb for m in metrics_list]),
                "max_memory_mb": np.max([m.memory_mb for m in metrics_list]),
                "avg_threads": np.mean([m.active_threads for m in metrics_list]),
                "max_threads": np.max([m.active_threads for m in metrics_list])
            },
            "totals": {
                "files_processed": self.files_processed,
                "issues_found": self.issues_found,
                "fixes_generated": self.fixes_generated,
                "llm_requests": self.llm_requests,
                "llm_tokens_used": self.llm_tokens_used,
                "cache_hits": self.cache_hits,
                "cache_misses": self.cache_misses
            }
        }

class PerformanceVisualizer:
    """Create performance visualizations and reports."""
    
    def __init__(self, monitor: PerformanceMonitor):
        self.monitor = monitor
        self.setup_plotting_style()
        
    def setup_plotting_style(self):
        """Setup matplotlib and seaborn styling."""
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
        # Set figure size and DPI for high-quality output
        plt.rcParams['figure.figsize'] = (12, 8)
        plt.rcParams['figure.dpi'] = 300
        plt.rcParams['font.size'] = 10
        
    def create_performance_dashboard(self, output_path: str = "performance_dashboard.png"):
        """Create a comprehensive performance dashboard."""
        fig = plt.figure(figsize=(20, 16))
        
        # Get metrics data
        metrics_list = list(self.monitor.metrics_history)
        if not metrics_list:
            return
            
        timestamps = [m.timestamp for m in metrics_list]
        
        # 1. System Resources (top left)
        ax1 = plt.subplot(3, 3, 1)
        ax1.plot(timestamps, [m.cpu_percent for m in metrics_list], label='CPU %', linewidth=2)
        ax1.plot(timestamps, [m.memory_mb / 100 for m in metrics_list], label='Memory (100MB)', linewidth=2)
        ax1.set_title('System Resources', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Usage')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. Processing Timeline (top center)
        ax2 = plt.subplot(3, 3, 2)
        ax2.plot(timestamps, [m.files_processed for m in metrics_list], label='Files Processed', linewidth=2)
        ax2.plot(timestamps, [m.issues_found for m in metrics_list], label='Issues Found', linewidth=2)
        ax2.set_title('Processing Progress', fontsize=14, fontweight='bold')
        ax2.set_ylabel('Count')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 3. LLM Activity (top right)
        ax3 = plt.subplot(3, 3, 3)
        ax3.plot(timestamps, [m.llm_requests for m in metrics_list], label='LLM Requests', linewidth=2)
        ax3.plot(timestamps, [m.fixes_generated for m in metrics_list], label='Fixes Generated', linewidth=2)
        ax3.set_title('LLM Activity', fontsize=14, fontweight='bold')
        ax3.set_ylabel('Count')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # 4. Disk I/O (middle left)
        ax4 = plt.subplot(3, 3, 4)
        ax4.plot(timestamps, [m.disk_io_read_mb for m in metrics_list], label='Read (MB)', linewidth=2)
        ax4.plot(timestamps, [m.disk_io_write_mb for m in metrics_list], label='Write (MB)', linewidth=2)
        ax4.set_title('Disk I/O', fontsize=14, fontweight='bold')
        ax4.set_ylabel('MB')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        # 5. Network I/O (middle center)
        ax5 = plt.subplot(3, 3, 5)
        ax5.plot(timestamps, [m.network_sent_mb for m in metrics_list], label='Sent (MB)', linewidth=2)
        ax5.plot(timestamps, [m.network_recv_mb for m in metrics_list], label='Received (MB)', linewidth=2)
        ax5.set_title('Network I/O', fontsize=14, fontweight='bold')
        ax5.set_ylabel('MB')
        ax5.legend()
        ax5.grid(True, alpha=0.3)
        
        # 6. Threads and Files (middle right)
        ax6 = plt.subplot(3, 3, 6)
        ax6.plot(timestamps, [m.active_threads for m in metrics_list], label='Active Threads', linewidth=2)
        ax6.plot(timestamps, [m.open_files for m in metrics_list], label='Open Files', linewidth=2)
        ax6.set_title('Process Resources', fontsize=14, fontweight='bold')
        ax6.set_ylabel('Count')
        ax6.legend()
        ax6.grid(True, alpha=0.3)
        
        # 7. Performance Summary (bottom left)
        ax7 = plt.subplot(3, 3, 7)
        summary = self.monitor.get_summary()
        if summary:
            categories = ['Linter', 'LLM']
            durations = [summary['duration']['linter_seconds'], summary['duration']['llm_seconds']]
            colors = ['#ff7f0e', '#2ca02c']
            ax7.bar(categories, durations, color=colors, alpha=0.7)
            ax7.set_title('Time Distribution', fontsize=14, fontweight='bold')
            ax7.set_ylabel('Seconds')
            for i, v in enumerate(durations):
                ax7.text(i, v + 0.1, f'{v:.1f}s', ha='center', va='bottom', fontweight='bold')
        
        # 8. Efficiency Metrics (bottom center)
        ax8 = plt.subplot(3, 3, 8)
        if summary:
            metrics = ['Cache Hit Rate', 'Fix Rate', 'Files/sec']
            values = [
                summary['efficiency']['cache_hit_rate'],
                summary['efficiency']['fix_rate'],
                summary['throughput']['files_per_second']
            ]
            colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
            bars = ax8.bar(metrics, values, color=colors, alpha=0.7)
            ax8.set_title('Efficiency Metrics', fontsize=14, fontweight='bold')
            ax8.set_ylabel('Rate (%)')
            for bar, value in zip(bars, values):
                ax8.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                        f'{value:.1f}%', ha='center', va='bottom', fontweight='bold')
        
        # 9. Summary Statistics (bottom right)
        ax9 = plt.subplot(3, 3, 9)
        ax9.axis('off')
        if summary:
            stats_text = f"""
Performance Summary

Duration: {summary['duration']['total_seconds']:.1f}s
Files Processed: {summary['totals']['files_processed']}
Issues Found: {summary['totals']['issues_found']}
Fixes Generated: {summary['totals']['fixes_generated']}
LLM Requests: {summary['totals']['llm_requests']}
Tokens Used: {summary['totals']['llm_tokens_used']:,}

Throughput:
• Files/sec: {summary['throughput']['files_per_second']:.1f}
• Issues/sec: {summary['throughput']['issues_per_second']:.1f}
• Fixes/sec: {summary['throughput']['fixes_per_second']:.1f}

Efficiency:
• Cache Hit Rate: {summary['efficiency']['cache_hit_rate']:.1f}%
• Fix Rate: {summary['efficiency']['fix_rate']:.1f}%
• Tokens per Fix: {summary['efficiency']['tokens_per_fix']:.0f}
            """
            ax9.text(0.05, 0.95, stats_text, transform=ax9.transAxes, fontsize=10,
                    verticalalignment='top', fontfamily='monospace',
                    bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8))
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return output_path
        
    def create_language_breakdown_chart(self, languages_data: Dict[str, int], output_path: str = "language_breakdown.png"):
        """Create language breakdown visualization."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        
        # Pie chart
        languages = list(languages_data.keys())
        counts = list(languages_data.values())
        colors = plt.cm.Set3(np.linspace(0, 1, len(languages)))
        
        ax1.pie(counts, labels=languages, autopct='%1.1f%%', colors=colors, startangle=90)
        ax1.set_title('Files by Language', fontsize=16, fontweight='bold')
        
        # Bar chart
        bars = ax2.bar(languages, counts, color=colors, alpha=0.7)
        ax2.set_title('File Count by Language', fontsize=16, fontweight='bold')
        ax2.set_ylabel('Number of Files')
        ax2.tick_params(axis='x', rotation=45)
        
        # Add value labels on bars
        for bar, count in zip(bars, counts):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                    str(count), ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return output_path
        
    def create_issue_analysis_chart(self, issues_data: Dict[str, List[Dict]], output_path: str = "issue_analysis.png"):
        """Create issue analysis visualization."""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # Collect data
        severities = defaultdict(int)
        categories = defaultdict(int)
        files_with_issues = defaultdict(int)
        issue_types = defaultdict(int)
        
        for file_path, issues in issues_data.items():
            files_with_issues[Path(file_path).suffix] += 1
            for issue in issues:
                severities[issue.get('severity', 'unknown')] += 1
                categories[issue.get('category', 'unknown')] += 1
                issue_types[issue.get('code', 'unknown')] += 1
        
        # 1. Severity distribution
        if severities:
            ax1.pie(severities.values(), labels=severities.keys(), autopct='%1.1f%%', startangle=90)
            ax1.set_title('Issues by Severity', fontsize=14, fontweight='bold')
        
        # 2. Category distribution
        if categories:
            bars = ax2.bar(categories.keys(), categories.values(), alpha=0.7)
            ax2.set_title('Issues by Category', fontsize=14, fontweight='bold')
            ax2.set_ylabel('Count')
            ax2.tick_params(axis='x', rotation=45)
        
        # 3. Files with issues by extension
        if files_with_issues:
            bars = ax3.bar(files_with_issues.keys(), files_with_issues.values(), alpha=0.7)
            ax3.set_title('Files with Issues by Extension', fontsize=14, fontweight='bold')
            ax3.set_ylabel('Count')
            ax3.tick_params(axis='x', rotation=45)
        
        # 4. Top issue types
        if issue_types:
            top_issues = dict(sorted(issue_types.items(), key=lambda x: x[1], reverse=True)[:10])
            bars = ax4.bar(range(len(top_issues)), top_issues.values(), alpha=0.7)
            ax4.set_title('Top 10 Issue Types', fontsize=14, fontweight='bold')
            ax4.set_ylabel('Count')
            ax4.set_xticks(range(len(top_issues)))
            ax4.set_xticklabels(list(top_issues.keys()), rotation=45, ha='right')
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return output_path

class AnalyticsReporter:
    """Generate comprehensive analytics reports."""
    
    def __init__(self, monitor: PerformanceMonitor, visualizer: PerformanceVisualizer):
        self.monitor = monitor
        self.visualizer = visualizer
        
    def generate_report(self, languages_data: Dict[str, int], issues_data: Dict[str, List[Dict]], 
                       output_dir: str = "analytics_report") -> str:
        """Generate a comprehensive analytics report."""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Generate visualizations
        dashboard_path = self.visualizer.create_performance_dashboard(
            str(output_path / "performance_dashboard.png")
        )
        language_path = self.visualizer.create_language_breakdown_chart(
            languages_data, str(output_path / "language_breakdown.png")
        )
        issue_path = self.visualizer.create_issue_analysis_chart(
            issues_data, str(output_path / "issue_analysis.png")
        )
        
        # Generate HTML report
        html_report = self._generate_html_report(languages_data, issues_data)
        html_path = output_path / "report.html"
        with open(html_path, 'w') as f:
            f.write(html_report)
        
        # Generate JSON data
        json_data = {
            "performance_summary": self.monitor.get_summary(),
            "languages": languages_data,
            "issues": issues_data,
            "timestamp": datetime.now().isoformat()
        }
        json_path = output_path / "data.json"
        with open(json_path, 'w') as f:
            json.dump(json_data, f, indent=2, default=str)
        
        return str(output_path)
        
    def _generate_html_report(self, languages_data: Dict[str, int], issues_data: Dict[str, List[Dict]]) -> str:
        """Generate HTML report."""
        summary = self.monitor.get_summary()
        
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CodeFixer Analytics Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background: white;
            border-radius: 8px;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1, h2, h3 {{
            color: #333;
        }}
        .metric-card {{
            background: #f8f9fa;
            border-radius: 6px;
            padding: 20px;
            margin: 10px 0;
            border-left: 4px solid #007bff;
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            color: #007bff;
        }}
        .metric-label {{
            color: #666;
            font-size: 0.9em;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .chart-container {{
            text-align: center;
            margin: 20px 0;
        }}
        .chart-container img {{
            max-width: 100%;
            height: auto;
            border-radius: 6px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        .table th, .table td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        .table th {{
            background-color: #f8f9fa;
            font-weight: bold;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: bold;
        }}
        .badge-success {{ background: #d4edda; color: #155724; }}
        .badge-warning {{ background: #fff3cd; color: #856404; }}
        .badge-danger {{ background: #f8d7da; color: #721c24; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔧 CodeFixer Analytics Report</h1>
        <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <h2>Performance Summary</h2>
        <div class="grid">
            <div class="metric-card">
                <div class="metric-value">{summary.get('duration', {}).get('total_seconds', 0):.1f}s</div>
                <div class="metric-label">Total Duration</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{summary.get('totals', {}).get('files_processed', 0)}</div>
                <div class="metric-label">Files Processed</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{summary.get('totals', {}).get('issues_found', 0)}</div>
                <div class="metric-label">Issues Found</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{summary.get('totals', {}).get('fixes_generated', 0)}</div>
                <div class="metric-label">Fixes Generated</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{summary.get('efficiency', {}).get('fix_rate', 0):.1f}%</div>
                <div class="metric-label">Fix Rate</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{summary.get('throughput', {}).get('files_per_second', 0):.1f}</div>
                <div class="metric-label">Files/Second</div>
            </div>
        </div>
        
        <h2>Performance Dashboard</h2>
        <div class="chart-container">
            <img src="performance_dashboard.png" alt="Performance Dashboard">
        </div>
        
        <h2>Language Breakdown</h2>
        <div class="chart-container">
            <img src="language_breakdown.png" alt="Language Breakdown">
        </div>
        
        <h2>Issue Analysis</h2>
        <div class="chart-container">
            <img src="issue_analysis.png" alt="Issue Analysis">
        </div>
        
        <h2>Detailed Metrics</h2>
        <table class="table">
            <thead>
                <tr>
                    <th>Metric</th>
                    <th>Value</th>
                    <th>Description</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Linter Duration</td>
                    <td>{summary.get('duration', {}).get('linter_seconds', 0):.1f}s</td>
                    <td>Time spent running linters</td>
                </tr>
                <tr>
                    <td>LLM Duration</td>
                    <td>{summary.get('duration', {}).get('llm_seconds', 0):.1f}s</td>
                    <td>Time spent generating fixes</td>
                </tr>
                <tr>
                    <td>LLM Requests</td>
                    <td>{summary.get('totals', {}).get('llm_requests', 0)}</td>
                    <td>Number of LLM API calls</td>
                </tr>
                <tr>
                    <td>Tokens Used</td>
                    <td>{summary.get('totals', {}).get('llm_tokens_used', 0):,}</td>
                    <td>Total tokens consumed</td>
                </tr>
                <tr>
                    <td>Cache Hit Rate</td>
                    <td>{summary.get('efficiency', {}).get('cache_hit_rate', 0):.1f}%</td>
                    <td>Percentage of cache hits</td>
                </tr>
                <tr>
                    <td>Average CPU</td>
                    <td>{summary.get('system', {}).get('avg_cpu_percent', 0):.1f}%</td>
                    <td>Average CPU usage</td>
                </tr>
                <tr>
                    <td>Peak Memory</td>
                    <td>{summary.get('system', {}).get('max_memory_mb', 0):.1f}MB</td>
                    <td>Peak memory usage</td>
                </tr>
            </tbody>
        </table>
        
        <h2>Languages Detected</h2>
        <table class="table">
            <thead>
                <tr>
                    <th>Language</th>
                    <th>Files</th>
                    <th>Percentage</th>
                </tr>
            </thead>
            <tbody>
                {self._generate_language_table_rows(languages_data)}
            </tbody>
        </table>
        
        <h2>Top Issues by File</h2>
        <table class="table">
            <thead>
                <tr>
                    <th>File</th>
                    <th>Issues</th>
                    <th>Severity Breakdown</th>
                </tr>
            </thead>
            <tbody>
                {self._generate_issues_table_rows(issues_data)}
            </tbody>
        </table>
    </div>
</body>
</html>
        """
        return html
        
    def _generate_language_table_rows(self, languages_data: Dict[str, int]) -> str:
        """Generate language table rows."""
        total_files = sum(languages_data.values())
        rows = []
        for lang, count in sorted(languages_data.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_files * 100) if total_files > 0 else 0
            rows.append(f"""
                <tr>
                    <td>{lang.title()}</td>
                    <td>{count}</td>
                    <td>{percentage:.1f}%</td>
                </tr>
            """)
        return ''.join(rows)
        
    def _generate_issues_table_rows(self, issues_data: Dict[str, List[Dict]]) -> str:
        """Generate issues table rows."""
        rows = []
        for file_path, issues in sorted(issues_data.items(), key=lambda x: len(x[1]), reverse=True)[:20]:
            severity_counts = defaultdict(int)
            for issue in issues:
                severity_counts[issue.get('severity', 'unknown')] += 1
            
            severity_badges = []
            for severity, count in severity_counts.items():
                badge_class = {
                    'high': 'badge-danger',
                    'medium': 'badge-warning',
                    'low': 'badge-success'
                }.get(severity, 'badge-warning')
                severity_badges.append(f'<span class="badge {badge_class}">{severity}: {count}</span>')
            
            rows.append(f"""
                <tr>
                    <td>{file_path}</td>
                    <td>{len(issues)}</td>
                    <td>{' '.join(severity_badges)}</td>
                </tr>
            """)
        return ''.join(rows) 