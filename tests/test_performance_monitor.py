"""
Tests for performance monitoring and analytics.
"""

import pytest
import time
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

# Skip whole module when analytics extras are not installed (CI installs them via workflow).
pytest.importorskip("numpy")
pytest.importorskip("matplotlib")
pytest.importorskip("seaborn")
pytest.importorskip("pandas")
pytest.importorskip("psutil")
import numpy as np

from performance_monitor import (
    PerformanceMonitor, 
    PerformanceVisualizer, 
    AnalyticsReporter,
    PerformanceMetrics
)

class TestPerformanceMonitor:
    """Test PerformanceMonitor class."""
    
    def test_init(self):
        """Test monitor initialization."""
        monitor = PerformanceMonitor()
        assert monitor.sample_interval == 1.0
        assert monitor.max_samples == 1000
        assert not monitor.is_monitoring
        assert monitor.metrics_history.maxlen == 1000
        
    def test_start_stop_monitoring(self):
        """Test starting and stopping monitoring."""
        monitor = PerformanceMonitor(sample_interval=0.1)
        
        # Start monitoring
        monitor.start_monitoring()
        assert monitor.is_monitoring
        assert monitor.start_time is not None
        
        # Wait a bit
        time.sleep(0.2)
        
        # Stop monitoring
        monitor.stop_monitoring()
        assert not monitor.is_monitoring
        assert monitor.end_time is not None
        assert len(monitor.metrics_history) > 0
        
    def test_collect_metrics(self):
        """Test metrics collection."""
        monitor = PerformanceMonitor()
        from datetime import datetime
        monitor.start_time = datetime.now()
        
        metrics = monitor._collect_metrics()
        
        assert isinstance(metrics, PerformanceMetrics)
        assert metrics.timestamp is not None
        assert metrics.cpu_percent >= 0
        assert metrics.memory_mb >= 0
        assert metrics.active_threads > 0
        
    def test_update_linter_metrics(self):
        """Test linter metrics updates."""
        monitor = PerformanceMonitor()
        
        monitor.update_linter_metrics(1.5, 10, 25)
        
        assert monitor.linter_duration == 1.5
        assert monitor.files_processed == 10
        assert monitor.issues_found == 25
        
    def test_update_llm_metrics(self):
        """Test LLM metrics updates."""
        monitor = PerformanceMonitor()
        
        monitor.update_llm_metrics(2.0, 5, 1000, 8)
        
        assert monitor.llm_duration == 2.0
        assert monitor.llm_requests == 5
        assert monitor.llm_tokens_used == 1000
        assert monitor.fixes_generated == 8
        
    def test_update_cache_metrics(self):
        """Test cache metrics updates."""
        monitor = PerformanceMonitor()
        
        monitor.update_cache_metrics(15, 5)
        
        assert monitor.cache_hits == 15
        assert monitor.cache_misses == 5
        
    def test_get_summary_empty(self):
        """Test summary with no metrics."""
        monitor = PerformanceMonitor()
        summary = monitor.get_summary()
        assert summary == {}
        
    def test_get_summary_with_data(self):
        """Test summary with metrics data."""
        monitor = PerformanceMonitor()
        
        # Add some mock metrics
        mock_metrics = PerformanceMetrics(
            timestamp=time.time(),
            cpu_percent=50.0,
            memory_mb=100.0,
            disk_io_read_mb=10.0,
            disk_io_write_mb=5.0,
            network_sent_mb=1.0,
            network_recv_mb=2.0,
            active_threads=4,
            open_files=10,
            linter_duration=1.0,
            llm_duration=2.0,
            total_duration=3.0,
            files_processed=10,
            issues_found=25,
            fixes_generated=20,
            llm_requests=5,
            llm_tokens_used=1000,
            cache_hits=15,
            cache_misses=5
        )
        
        monitor.metrics_history.append(mock_metrics)
        monitor.start_time = time.time() - 3.0
        monitor.end_time = time.time()
        monitor.linter_duration = 1.0
        monitor.llm_duration = 2.0
        monitor.files_processed = 10
        monitor.issues_found = 25
        monitor.fixes_generated = 20
        monitor.llm_requests = 5
        monitor.llm_tokens_used = 1000
        monitor.cache_hits = 15
        monitor.cache_misses = 5
        
        summary = monitor.get_summary()
        
        assert "duration" in summary
        assert "throughput" in summary
        assert "efficiency" in summary
        assert "system" in summary
        assert "totals" in summary
        
        assert summary["duration"]["total_seconds"] > 0
        assert summary["efficiency"]["cache_hit_rate"] == 75.0  # 15/(15+5)*100
        assert summary["efficiency"]["fix_rate"] == 80.0  # 20/25*100

class TestPerformanceVisualizer:
    """Test PerformanceVisualizer class."""
    
    def test_init(self):
        """Test visualizer initialization."""
        monitor = PerformanceMonitor()
        visualizer = PerformanceVisualizer(monitor)
        assert visualizer.monitor == monitor
        
    def test_setup_plotting_style(self):
        """Test plotting style setup."""
        monitor = PerformanceMonitor()
        visualizer = PerformanceVisualizer(monitor)
        visualizer.setup_plotting_style()
        # Should not raise any exceptions
        
    @patch('matplotlib.pyplot.savefig')
    def test_create_performance_dashboard(self, mock_savefig):
        """Test performance dashboard creation."""
        monitor = PerformanceMonitor()
        visualizer = PerformanceVisualizer(monitor)
        
        # Add some mock data
        mock_metrics = PerformanceMetrics(
            timestamp=time.time(),
            cpu_percent=50.0,
            memory_mb=100.0,
            disk_io_read_mb=10.0,
            disk_io_write_mb=5.0,
            network_sent_mb=1.0,
            network_recv_mb=2.0,
            active_threads=4,
            open_files=10,
            linter_duration=1.0,
            llm_duration=2.0,
            total_duration=3.0,
            files_processed=10,
            issues_found=25,
            fixes_generated=20,
            llm_requests=5,
            llm_tokens_used=1000,
            cache_hits=15,
            cache_misses=5
        )
        
        monitor.metrics_history.append(mock_metrics)
        
        output_path = visualizer.create_performance_dashboard("test_dashboard.png")
        
        assert output_path == "test_dashboard.png"
        mock_savefig.assert_called_once()
        
    @patch('matplotlib.pyplot.savefig')
    def test_create_language_breakdown_chart(self, mock_savefig):
        """Test language breakdown chart creation."""
        monitor = PerformanceMonitor()
        visualizer = PerformanceVisualizer(monitor)
        
        languages_data = {
            "python": 10,
            "javascript": 5,
            "go": 3
        }
        
        output_path = visualizer.create_language_breakdown_chart(languages_data, "test_languages.png")
        
        assert output_path == "test_languages.png"
        mock_savefig.assert_called_once()
        
    @patch('matplotlib.pyplot.savefig')
    def test_create_issue_analysis_chart(self, mock_savefig):
        """Test issue analysis chart creation."""
        monitor = PerformanceMonitor()
        visualizer = PerformanceVisualizer(monitor)
        
        issues_data = {
            "file1.py": [
                {"severity": "high", "category": "style", "code": "E501"},
                {"severity": "medium", "category": "quality", "code": "W291"}
            ],
            "file2.js": [
                {"severity": "low", "category": "style", "code": "indent"}
            ]
        }
        
        output_path = visualizer.create_issue_analysis_chart(issues_data, "test_issues.png")
        
        assert output_path == "test_issues.png"
        mock_savefig.assert_called_once()

class TestAnalyticsReporter:
    """Test AnalyticsReporter class."""
    
    def test_init(self):
        """Test reporter initialization."""
        monitor = PerformanceMonitor()
        visualizer = PerformanceVisualizer(monitor)
        reporter = AnalyticsReporter(monitor, visualizer)
        assert reporter.monitor == monitor
        assert reporter.visualizer == visualizer
        
    @patch('pathlib.Path.mkdir')
    @patch('builtins.open')
    @patch('json.dump')
    def test_generate_report(self, mock_json_dump, mock_open, mock_mkdir):
        """Test report generation."""
        monitor = PerformanceMonitor()
        visualizer = PerformanceVisualizer(monitor)
        reporter = AnalyticsReporter(monitor, visualizer)
        
        languages_data = {"python": 10, "javascript": 5}
        issues_data = {
            "file1.py": [{"severity": "high", "code": "E501"}]
        }
        
        # Mock the visualizer methods
        visualizer.create_performance_dashboard = Mock(return_value="dashboard.png")
        visualizer.create_language_breakdown_chart = Mock(return_value="languages.png")
        visualizer.create_issue_analysis_chart = Mock(return_value="issues.png")
        
        output_path = reporter.generate_report(languages_data, issues_data, "test_report")
        
        assert "test_report" in output_path
        mock_mkdir.assert_called_once()
        mock_open.assert_called()
        mock_json_dump.assert_called_once()
        
    def test_generate_language_table_rows(self):
        """Test language table row generation."""
        monitor = PerformanceMonitor()
        visualizer = PerformanceVisualizer(monitor)
        reporter = AnalyticsReporter(monitor, visualizer)
        
        languages_data = {
            "python": 10,
            "javascript": 5,
            "go": 3
        }
        
        rows = reporter._generate_language_table_rows(languages_data)
        
        assert "python" in rows.lower()
        assert "javascript" in rows.lower()
        assert "go" in rows.lower()
        assert "10" in rows
        assert "5" in rows
        assert "3" in rows
        
    def test_generate_issues_table_rows(self):
        """Test issues table row generation."""
        monitor = PerformanceMonitor()
        visualizer = PerformanceVisualizer(monitor)
        reporter = AnalyticsReporter(monitor, visualizer)
        
        issues_data = {
            "file1.py": [
                {"severity": "high", "code": "E501"},
                {"severity": "medium", "code": "W291"}
            ],
            "file2.js": [
                {"severity": "low", "code": "indent"}
            ]
        }
        
        rows = reporter._generate_issues_table_rows(issues_data)
        
        assert "file1.py" in rows
        assert "file2.js" in rows
        assert "high" in rows
        assert "medium" in rows
        assert "low" in rows

class TestPerformanceMetrics:
    """Test PerformanceMetrics dataclass."""
    
    def test_metrics_creation(self):
        """Test metrics creation."""
        timestamp = time.time()
        metrics = PerformanceMetrics(
            timestamp=timestamp,
            cpu_percent=50.0,
            memory_mb=100.0,
            disk_io_read_mb=10.0,
            disk_io_write_mb=5.0,
            network_sent_mb=1.0,
            network_recv_mb=2.0,
            active_threads=4,
            open_files=10,
            linter_duration=1.0,
            llm_duration=2.0,
            total_duration=3.0,
            files_processed=10,
            issues_found=25,
            fixes_generated=20,
            llm_requests=5,
            llm_tokens_used=1000,
            cache_hits=15,
            cache_misses=5
        )
        
        assert metrics.timestamp == timestamp
        assert metrics.cpu_percent == 50.0
        assert metrics.memory_mb == 100.0
        assert metrics.files_processed == 10
        assert metrics.issues_found == 25
        assert metrics.fixes_generated == 20 