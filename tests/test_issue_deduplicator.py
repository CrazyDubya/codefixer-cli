"""
Tests for issue deduplication and prioritization module.
"""

import pytest
from issue_deduplicator import (
    deduplicate_issues,
    prioritize_issues,
    filter_issues_by_severity,
    group_issues_by_type,
    create_issue_key
)


class TestIssueDeduplication:
    """Test issue deduplication functionality."""
    
    def test_deduplicate_issues_no_duplicates(self):
        """Test deduplication when no duplicates exist."""
        issues = {
            "file1.py": [{"row": 1, "col": 1, "code": "E302", "text": "Issue 1"}],
            "file2.py": [{"row": 2, "col": 2, "code": "E501", "text": "Issue 2"}],
            "file3.py": [{"row": 3, "col": 3, "code": "F401", "text": "Issue 3"}]
        }
        
        deduplicated = deduplicate_issues(issues)
        
        assert len(deduplicated) == 3
        assert deduplicated == issues
    
    def test_deduplicate_issues_with_duplicates(self):
        """Test deduplication when duplicates exist."""
        issues = {
            "file1.py": [
                {"row": 1, "col": 1, "code": "E302", "text": "Issue 1"},
                {"row": 1, "col": 1, "code": "E302", "text": "Issue 1"},  # Duplicate
                {"row": 1, "col": 1, "code": "E302", "text": "Issue 1"},  # Another duplicate
            ],
            "file2.py": [
                {"row": 2, "col": 2, "code": "E501", "text": "Issue 2"}
            ]
        }
        
        deduplicated = deduplicate_issues(issues)
        
        assert len(deduplicated) == 2
        assert len(deduplicated["file1.py"]) == 1  # Duplicates should be merged
        assert len(deduplicated["file2.py"]) == 1
    
    def test_deduplicate_issues_similar_but_different(self):
        """Test that similar but different issues are not deduplicated."""
        issues = {
            "file1.py": [
                {"row": 1, "col": 1, "code": "E302", "text": "Issue 1"},
                {"row": 1, "col": 2, "code": "E302", "text": "Issue 1"},  # Different column
                {"row": 2, "col": 1, "code": "E302", "text": "Issue 1"},  # Different row
                {"row": 1, "col": 1, "code": "E501", "text": "Issue 1"},  # Different code
            ]
        }
        
        deduplicated = deduplicate_issues(issues)
        
        assert len(deduplicated["file1.py"]) == 4  # All should be kept as they're different
    
    def test_create_issue_key(self):
        """Test issue key creation."""
        issue = {"path": "file1.py", "row": 1, "col": 1, "code": "E302", "text": "Issue 1"}
        
        key = create_issue_key(issue)
        
        assert key == "file1.py|1|1|E302|Issue 1"
    
    def test_create_issue_key_missing_fields(self):
        """Test issue key creation with missing fields."""
        issue = {"path": "file1.py", "row": 1, "code": "E302"}  # Missing col and text
        
        key = create_issue_key(issue)
        
        assert key == "file1.py|1||E302|"


class TestIssuePrioritization:
    """Test issue prioritization functionality."""
    
    def test_prioritize_issues_security_first(self):
        """Test that security issues are prioritized highest."""
        issues = [
            {"path": "file1.py", "row": 1, "col": 1, "code": "E501", "text": "Line too long"},
            {"path": "file2.py", "row": 2, "col": 2, "code": "S101", "text": "Use of assert detected"},
            {"path": "file3.py", "row": 3, "col": 3, "code": "F401", "text": "Unused import"},
        ]
        
        prioritized = prioritize_issues(issues)
        
        # Security issue (S101) should be first
        assert prioritized[0]["code"] == "S101"
    
    def test_prioritize_issues_code_quality_second(self):
        """Test that code quality issues are prioritized second."""
        issues = [
            {"path": "file1.py", "row": 1, "col": 1, "code": "E501", "text": "Line too long"},
            {"path": "file2.py", "row": 2, "col": 2, "code": "F401", "text": "Unused import"},
            {"path": "file3.py", "row": 3, "col": 3, "code": "no-console", "text": "console.log usage"},
        ]
        
        prioritized = prioritize_issues(issues)
        
        # Code quality issues should come before formatting
        quality_codes = [issue["code"] for issue in prioritized]
        assert quality_codes.index("F401") < quality_codes.index("E501")
        assert quality_codes.index("no-console") < quality_codes.index("E501")
    
    def test_prioritize_issues_formatting_last(self):
        """Test that formatting issues are prioritized last."""
        issues = [
            {"path": "file1.py", "row": 1, "col": 1, "code": "E501", "text": "Line too long"},
            {"path": "file2.py", "row": 2, "col": 2, "code": "indent", "text": "Indentation issue"},
            {"path": "file3.py", "row": 3, "col": 3, "code": "quotes", "text": "Quote style issue"},
        ]
        
        prioritized = prioritize_issues(issues)
        
        # Formatting issues should be at the end
        formatting_codes = ["E501", "indent", "quotes"]
        for code in formatting_codes:
            assert any(issue["code"] == code for issue in prioritized)
    
    def test_prioritize_issues_security_keywords(self):
        """Test that issues with security keywords are prioritized."""
        issues = [
            {"path": "file1.py", "row": 1, "col": 1, "code": "E501", "text": "Line too long"},
            {"path": "file2.py", "row": 2, "col": 2, "code": "custom", "text": "Security vulnerability detected"},
            {"path": "file3.py", "row": 3, "col": 3, "code": "F401", "text": "Unused import"},
        ]
        
        prioritized = prioritize_issues(issues)
        
        # Security issue should be first
        assert prioritized[0]["text"] == "Security vulnerability detected"


class TestIssueFiltering:
    """Test issue filtering functionality."""
    
    def test_filter_issues_by_severity_critical(self):
        """Test filtering by critical severity."""
        issues = [
            {"path": "file1.py", "row": 1, "col": 1, "code": "E501", "text": "Line too long"},
            {"path": "file2.py", "row": 2, "col": 2, "code": "S101", "text": "Security vulnerability"},
            {"path": "file3.py", "row": 3, "col": 3, "code": "F401", "text": "Unused import"},
        ]
        
        filtered = filter_issues_by_severity(issues, "critical")
        
        # Only security issues should remain
        assert len(filtered) == 1
        assert filtered[0]["code"] == "S101"
    
    def test_filter_issues_by_severity_high(self):
        """Test filtering by high severity."""
        issues = [
            {"path": "file1.py", "row": 1, "col": 1, "code": "E501", "text": "Line too long"},
            {"path": "file2.py", "row": 2, "col": 2, "code": "S101", "text": "Security vulnerability"},
            {"path": "file3.py", "row": 3, "col": 3, "code": "F401", "text": "Unused import"},
            {"path": "file4.py", "row": 4, "col": 4, "code": "no-console", "text": "console.log usage"},
        ]
        
        filtered = filter_issues_by_severity(issues, "high")
        
        # Security and code quality issues should remain
        assert len(filtered) == 3
        codes = [issue["code"] for issue in filtered]
        assert "S101" in codes
        assert "F401" in codes
        assert "no-console" in codes
        assert "E501" not in codes  # Formatting issue should be filtered out
    
    def test_filter_issues_by_severity_medium(self):
        """Test filtering by medium severity."""
        issues = [
            {"path": "file1.py", "row": 1, "col": 1, "code": "E501", "text": "Line too long"},
            {"path": "file2.py", "row": 2, "col": 2, "code": "E111", "text": "Indentation issue"},
            {"path": "file3.py", "row": 3, "col": 3, "code": "F401", "text": "Unused import"},
        ]
        
        filtered = filter_issues_by_severity(issues, "medium")
        
        # Code quality and style issues should remain
        assert len(filtered) == 2
        codes = [issue["code"] for issue in filtered]
        assert "F401" in codes
        assert "E111" in codes
        assert "E501" not in codes  # Formatting issue should be filtered out
    
    def test_filter_issues_by_severity_low(self):
        """Test filtering by low severity (should include all)."""
        issues = [
            {"path": "file1.py", "row": 1, "col": 1, "code": "E501", "text": "Line too long"},
            {"path": "file2.py", "row": 2, "col": 2, "code": "S101", "text": "Security vulnerability"},
            {"path": "file3.py", "row": 3, "col": 3, "code": "F401", "text": "Unused import"},
        ]
        
        filtered = filter_issues_by_severity(issues, "low")
        
        # All issues should remain
        assert len(filtered) == 3
    
    def test_filter_issues_by_severity_unknown(self):
        """Test filtering with unknown severity level."""
        issues = [
            {"path": "file1.py", "row": 1, "col": 1, "code": "E501", "text": "Line too long"},
        ]
        
        filtered = filter_issues_by_severity(issues, "unknown")
        
        # Should default to low severity (include all)
        assert len(filtered) == 1


class TestIssueGrouping:
    """Test issue grouping functionality."""
    
    def test_group_issues_by_type(self):
        """Test grouping issues by type."""
        issues = [
            {"path": "file1.py", "row": 1, "col": 1, "code": "S101", "text": "Security issue"},
            {"path": "file2.py", "row": 2, "col": 2, "code": "F401", "text": "Unused import"},
            {"path": "file3.py", "row": 3, "col": 3, "code": "E111", "text": "Indentation issue"},
            {"path": "file4.py", "row": 4, "col": 4, "code": "E501", "text": "Line too long"},
            {"path": "file5.py", "row": 5, "col": 5, "code": "no-console", "text": "console.log usage"},
        ]
        
        grouped = group_issues_by_type(issues)
        
        assert "security" in grouped
        assert "unused_code" in grouped
        assert "style" in grouped
        assert "formatting" in grouped
        assert "debugging" in grouped
        
        assert len(grouped["security"]) == 1
        assert len(grouped["unused_code"]) == 1
        assert len(grouped["style"]) == 1
        assert len(grouped["formatting"]) == 1
        assert len(grouped["debugging"]) == 1
    
    def test_group_issues_by_type_empty(self):
        """Test grouping empty issues list."""
        issues = []
        
        grouped = group_issues_by_type(issues)
        
        assert grouped == {}
    
    def test_group_issues_by_type_unknown_codes(self):
        """Test grouping issues with unknown codes."""
        issues = [
            {"path": "file1.py", "row": 1, "col": 1, "code": "UNKNOWN", "text": "Unknown issue"},
            {"path": "file2.py", "row": 2, "col": 2, "code": "CUSTOM", "text": "Custom issue"},
        ]
        
        grouped = group_issues_by_type(issues)
        
        assert "other" in grouped
        assert len(grouped["other"]) == 2
    
    def test_group_issues_by_type_mixed_categories(self):
        """Test grouping issues from mixed categories."""
        issues = [
            {"path": "file1.py", "row": 1, "col": 1, "code": "S101", "text": "Security issue"},
            {"path": "file2.py", "row": 2, "col": 2, "code": "S105", "text": "Another security issue"},
            {"path": "file3.py", "row": 3, "col": 3, "code": "F401", "text": "Unused import"},
            {"path": "file4.py", "row": 4, "col": 4, "code": "F403", "text": "Another unused import"},
        ]
        
        grouped = group_issues_by_type(issues)
        
        assert len(grouped["security"]) == 2
        assert len(grouped["unused_code"]) == 2 