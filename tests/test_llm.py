"""
Tests for LLM integration module.
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from llm import (
    build_prompt, 
    extract_code_from_response, 
    generate_fix,
    list_available_models,
    list_ollama_models,
    list_llamacpp_models
)


class TestLLMIntegration:
    """Test LLM integration functionality."""
    
    def test_build_prompt(self, sample_issues, temp_repo):
        """Test prompt building functionality."""
        file_path = temp_repo / "test_file.py"
        
        prompt = build_prompt(file_path, sample_issues)
        
        assert prompt is not None
        assert "test_file.py" in prompt
        assert "def hello_world()" in prompt
        assert "E302" in prompt
        assert "E501" in prompt
        assert "expected 2 blank lines" in prompt
        assert "line too long" in prompt
    
    def test_build_prompt_empty_issues(self, temp_repo):
        """Test prompt building with empty issues list."""
        file_path = temp_repo / "test_file.py"
        
        prompt = build_prompt(file_path, [])
        
        assert prompt is not None
        assert "test_file.py" in prompt
        assert "def hello_world()" in prompt
    
    def test_extract_code_from_response_success(self, mock_llm_response):
        """Test successful code extraction from LLM response."""
        extracted_code = extract_code_from_response(mock_llm_response)
        
        assert extracted_code is not None
        assert "def hello_world()" in extracted_code
        assert "print(\"Hello, World!\")" in extracted_code
        assert "return True" in extracted_code
    
    def test_extract_code_from_response_no_code_block(self):
        """Test code extraction when no code block is present."""
        response = "This is a response without any code blocks."
        
        extracted_code = extract_code_from_response(response)
        
        assert extracted_code is None
    
    def test_extract_code_from_response_multiple_blocks(self):
        """Test code extraction with multiple code blocks."""
        response = """
Here's the explanation:

```python
# First block
def helper():
    pass
```

And here's the main fix:

```python
def main():
    print("Hello")
    return True
```
"""
        
        extracted_code = extract_code_from_response(response)
        
        # Should extract the last code block
        assert extracted_code is not None
        assert "def main()" in extracted_code
        assert "print(\"Hello\")" in extracted_code
    
    def test_extract_code_from_response_different_languages(self):
        """Test code extraction with different language specifiers."""
        response = """
```javascript
function test() {
    console.log("Hello");
}
```
"""
        
        extracted_code = extract_code_from_response(response)
        
        assert extracted_code is not None
        assert "function test()" in extracted_code
        assert "console.log(\"Hello\")" in extracted_code
    
    @patch('llm.run_ollama')
    def test_generate_fix_ollama_success(self, mock_run_ollama, sample_issues, temp_repo):
        """Test successful fix generation with Ollama."""
        mock_run_ollama.return_value = """
Here's the fixed code:

```python
def hello_world():
    print("Hello, World!")
    return True
```
"""
        
        file_path = temp_repo / "test_file.py"
        result = generate_fix(file_path, sample_issues, "test-model", "ollama")
        
        assert result is not None
        assert "def hello_world()" in result
        mock_run_ollama.assert_called_once()
    
    @patch('llm.run_llama_cpp')
    def test_generate_fix_llamacpp_success(self, mock_run_llamacpp, sample_issues, temp_repo):
        """Test successful fix generation with llama.cpp."""
        mock_run_llamacpp.return_value = """
Here's the fixed code:

```python
def hello_world():
    print("Hello, World!")
    return True
```
"""
        
        file_path = temp_repo / "test_file.py"
        result = generate_fix(file_path, sample_issues, "test-model", "llama.cpp")
        
        assert result is not None
        assert "def hello_world()" in result
        mock_run_llamacpp.assert_called_once()
    
    @patch('llm.run_ollama')
    def test_generate_fix_ollama_failure(self, mock_run_ollama, sample_issues, temp_repo):
        """Test fix generation when Ollama fails."""
        mock_run_ollama.return_value = None
        
        file_path = temp_repo / "test_file.py"
        result = generate_fix(file_path, sample_issues, "test-model", "ollama")
        
        assert result is None
    
    @patch('llm.run_ollama')
    def test_generate_fix_ollama_empty_response(self, mock_run_ollama, sample_issues, temp_repo):
        """Test fix generation with empty LLM response."""
        mock_run_ollama.return_value = ""
        
        file_path = temp_repo / "test_file.py"
        result = generate_fix(file_path, sample_issues, "test-model", "ollama")
        
        assert result is None
    
    def test_generate_fix_unknown_runner(self, sample_issues, temp_repo):
        """Test fix generation with unknown runner."""
        file_path = temp_repo / "test_file.py"
        result = generate_fix(file_path, sample_issues, "test-model", "unknown")
        
        assert result is None
    
    @patch('llm.build_prompt')
    def test_generate_fix_prompt_failure(self, mock_build_prompt, sample_issues, temp_repo):
        """Test fix generation when prompt building fails."""
        mock_build_prompt.return_value = None
        
        file_path = temp_repo / "test_file.py"
        result = generate_fix(file_path, sample_issues, "test-model", "ollama")
        
        assert result is None
    
    @patch('llm.subprocess.run')
    def test_list_ollama_models_success(self, mock_subprocess):
        """Test successful listing of Ollama models."""
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = """
NAME                    ID              SIZE    MODIFIED
smollm2:135m           smollm2:135m    135M    2024-01-01 12:00:00
phi3:3b                phi3:3b         3B      2024-01-01 12:00:00
"""
        
        models = list_ollama_models()
        
        assert len(models) == 2
        assert "smollm2:135m" in models
        assert "phi3:3b" in models
        mock_subprocess.assert_called_once_with(['ollama', 'list'], capture_output=True, text=True)
    
    @patch('llm.subprocess.run')
    def test_list_ollama_models_failure(self, mock_subprocess):
        """Test listing Ollama models when command fails."""
        mock_subprocess.return_value.returncode = 1
        mock_subprocess.return_value.stderr = "Command not found"
        
        models = list_ollama_models()
        
        assert models == []
    
    @patch('llm.Path.exists')
    @patch('llm.Path.glob')
    def test_list_llamacpp_models_success(self, mock_glob, mock_exists):
        """Test successful listing of llama.cpp models."""
        mock_exists.return_value = True
        mock_glob.return_value = [
            Path("/usr/local/share/llama.cpp/models/model1.gguf"),
            Path("/usr/local/share/llama.cpp/models/model2.gguf")
        ]
        
        models = list_llamacpp_models()
        
        assert len(models) == 2
        assert "model1" in models
        assert "model2" in models
    
    @patch('llm.Path.exists')
    def test_list_llamacpp_models_no_directory(self, mock_exists):
        """Test listing llama.cpp models when directory doesn't exist."""
        mock_exists.return_value = False
        
        models = list_llamacpp_models()
        
        assert models == []
    
    @patch('llm.list_ollama_models')
    def test_list_available_models_ollama(self, mock_list_ollama):
        """Test listing available models for Ollama runner."""
        mock_list_ollama.return_value = ["model1", "model2"]
        
        models = list_available_models("ollama")
        
        assert models == ["model1", "model2"]
        mock_list_ollama.assert_called_once()
    
    @patch('llm.list_llamacpp_models')
    def test_list_available_models_llamacpp(self, mock_list_llamacpp):
        """Test listing available models for llama.cpp runner."""
        mock_list_llamacpp.return_value = ["model1", "model2"]
        
        models = list_available_models("llama.cpp")
        
        assert models == ["model1", "model2"]
        mock_list_llamacpp.assert_called_once()
    
    def test_list_available_models_unknown_runner(self):
        """Test listing available models for unknown runner."""
        models = list_available_models("unknown")
        
        assert models == []
    
    @patch('llm.run_ollama')
    def test_generate_fix_with_retry_success(self, mock_run_ollama, sample_issues, temp_repo):
        """Test fix generation with retry mechanism."""
        # First call fails, second succeeds
        mock_run_ollama.side_effect = [
            None,  # First attempt fails
            """
Here's the fixed code:

```python
def hello_world():
    print("Hello, World!")
    return True
```
"""
        ]
        
        file_path = temp_repo / "test_file.py"
        result = generate_fix(file_path, sample_issues, "test-model", "ollama", timeout=30, max_retries=3)
        
        assert result is not None
        assert "def hello_world()" in result
        assert mock_run_ollama.call_count == 2
    
    @patch('llm.run_ollama')
    def test_generate_fix_with_retry_all_fail(self, mock_run_ollama, sample_issues, temp_repo):
        """Test fix generation when all retries fail."""
        mock_run_ollama.return_value = None
        
        file_path = temp_repo / "test_file.py"
        result = generate_fix(file_path, sample_issues, "test-model", "ollama", timeout=30, max_retries=3)
        
        assert result is None
        assert mock_run_ollama.call_count == 3
    
    @patch('llm.time.sleep')  # Mock sleep to speed up tests
    @patch('llm.run_ollama')
    def test_generate_fix_retry_backoff(self, mock_run_ollama, mock_sleep, sample_issues, temp_repo):
        """Test that retry uses exponential backoff."""
        mock_run_ollama.return_value = None
        
        file_path = temp_repo / "test_file.py"
        result = generate_fix(file_path, sample_issues, "test-model", "ollama", timeout=30, max_retries=3)
        
        # Check that sleep was called with exponential backoff values
        expected_sleep_calls = [1, 2]  # 2^0, 2^1
        actual_sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
        assert actual_sleep_calls == expected_sleep_calls 