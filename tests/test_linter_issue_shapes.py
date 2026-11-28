"""Issues from the Go linter (line/column/message) must survive deduplication
and reach the prompt with their position and text."""
from linters.go_linter import GoLinter
from issue_deduplicator import deduplicate_issues
from llm import _format_issues_compressed

LINES = [
    "main.go:10:6: exported function `Foo` should have comment or be unexported (golint)",
    "main.go:42:2: exported function `Bar` should have comment or be unexported (golint)",
    "main.go:77:9: exported var `Baz` should have comment or be unexported (golint)",
]


def _issues():
    linter = GoLinter.__new__(GoLinter)
    return [linter._parse_text_line(line) for line in LINES]


def test_go_issues_on_different_lines_are_not_merged():
    out = deduplicate_issues({"main.go": _issues()})["main.go"]
    assert len(out) == 3


def test_go_issue_position_and_text_reach_the_prompt():
    out = deduplicate_issues({"main.go": _issues()})["main.go"]
    text = _format_issues_compressed(out)
    assert "Line 10, Column 6" in text
    assert "exported function `Foo`" in text


def test_row_col_text_issues_unchanged():
    issue = {"row": 3, "col": 4, "code": "E1", "text": "x"}
    out = deduplicate_issues({"a.py": [issue]})["a.py"]
    assert out == [issue]
