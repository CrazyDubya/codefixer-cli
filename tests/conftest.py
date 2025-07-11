"""
Pytest configuration and common fixtures for CodeFixer tests.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any
import subprocess
import os

@pytest.fixture
def temp_repo():
    """Create a temporary git repository for testing."""
    temp_dir = tempfile.mkdtemp()
    repo_path = Path(temp_dir)
    
    # Initialize git repository
    subprocess.run(["git", "init"], cwd=repo_path, check=True)
    
    # Create some test files
    (repo_path / "test_file.py").write_text("""
def hello_world():
    print("Hello, World!")
    return True
""")
    
    (repo_path / "bad_code.py").write_text("""
def bad_function(  ):
    x=1
    y=2
    print(x+y)
    return x+y
""")
    
    (repo_path / "test.js").write_text("""
function testFunction() {
    var x = 1;
    console.log(x);
    return x;
}
""")
    
    yield repo_path
    
    # Cleanup
    shutil.rmtree(temp_dir)

@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing."""
    return """
Here's the fixed code:

```python
def hello_world():
    print("Hello, World!")
    return True
```
"""

@pytest.fixture
def sample_issues():
    """Sample linting issues for testing."""
    return [
        {
            "path": "test_file.py",
            "row": 2,
            "col": 1,
            "code": "E302",
            "text": "expected 2 blank lines, found 1"
        },
        {
            "path": "test_file.py", 
            "row": 3,
            "col": 5,
            "code": "E501",
            "text": "line too long (80 > 79 characters)"
        }
    ]

@pytest.fixture
def mock_env_manager():
    """Mock environment manager for testing."""
    class MockEnvManager:
        def __init__(self):
            self.envs = {}
        
        def get_language_env(self, language: str, repo_path: Path) -> Path:
            temp_dir = tempfile.mkdtemp()
            self.envs[f"{language}_{repo_path.name}"] = temp_dir
            return Path(temp_dir)
        
        def cleanup_all(self):
            for env_path in self.envs.values():
                if os.path.exists(env_path):
                    shutil.rmtree(env_path)
            self.envs.clear()
    
    return MockEnvManager()

@pytest.fixture
def sample_languages():
    """Sample detected languages for testing."""
    return {
        "python": [Path("test_file.py"), Path("bad_code.py")],
        "javascript": [Path("test.js")]
    } 