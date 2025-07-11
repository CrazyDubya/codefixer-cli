"""
LLM integration module for CodeFixer.
"""

import subprocess
import json
import os
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
import time

logger = logging.getLogger(__name__)

# Default prompt template
DEFAULT_PROMPT_TEMPLATE = """You are a programming assistant. Below is a source code snippet and its lint errors:

SOURCE CODE:
{code}

LINT ISSUES:
{issues}

Please provide the corrected code with all lint issues fixed. Return only the corrected code without any explanations or markdown formatting.

CORRECTED CODE:
"""

def load_prompt_template() -> str:
    """
    Load prompt template from file or use default.
    
    Returns:
        Prompt template string
    """
    # Try multiple possible template locations
    template_paths = [
        Path("templates/fix_prompt.txt"),
        Path(__file__).parent / "templates" / "fix_prompt.txt",
        Path.cwd() / "templates" / "fix_prompt.txt"
    ]
    
    for template_path in template_paths:
        if template_path.exists():
            try:
                with open(template_path, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception as e:
                logger.warning(f"Failed to load prompt template from {template_path}: {e}")
                continue
    
    logger.info("Using default prompt template (templates/fix_prompt.txt not found)")
    return DEFAULT_PROMPT_TEMPLATE

def build_prompt(file_path: Path, issues: List[Dict[str, Any]]) -> str:
    """
    Build a prompt for the LLM based on code and lint issues.
    
    Args:
        file_path: Path to the file with issues
        issues: List of linting issues
        
    Returns:
        Formatted prompt string
    """
    try:
        # Read the source code
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
    except Exception as e:
        logger.error(f"Failed to read file {file_path}: {e}")
        return ""
    
    # Compress code if it's too long
    max_code_length = 8000  # characters
    if len(code) > max_code_length:
        logger.info(f"Code too long ({len(code)} chars), compressing...")
        code = _compress_code(code, max_code_length)
    
    # Format issues (limit to most important ones)
    issues_text = _format_issues_compressed(issues)
    
    # Load and format prompt template
    template = load_prompt_template()
    prompt = template.format(
        file_path=str(file_path),
        code=code,
        issues=issues_text.strip()
    )
    
    return prompt

def _compress_code(code: str, max_length: int) -> str:
    """Compress code while preserving important structure."""
    lines = code.split('\n')
    
    if len(lines) <= 50:  # Keep all lines if file is small
        return code
    
    # Keep first 20 lines, last 20 lines, and lines with issues
    important_lines = set()
    
    # Add first and last lines
    for i in range(min(20, len(lines))):
        important_lines.add(i)
        important_lines.add(len(lines) - 1 - i)
    
    # Add lines around issues (if we have them)
    # This would be enhanced by passing issue line numbers
    
    # Build compressed code
    compressed_lines = []
    for i, line in enumerate(lines):
        if i in important_lines:
            compressed_lines.append(line)
        elif i == 20:
            compressed_lines.append("... (compressed)")
        elif i == len(lines) - 20:
            compressed_lines.append("... (compressed)")
    
    compressed_code = '\n'.join(compressed_lines)
    
    # If still too long, truncate
    if len(compressed_code) > max_length:
        compressed_code = compressed_code[:max_length] + "\n... (truncated)"
    
    return compressed_code

def _format_issues_compressed(issues: List[Dict[str, Any]]) -> str:
    """Format issues in a compressed way."""
    if not issues:
        return ""
    
    # Limit to most important issues (prioritize by severity)
    max_issues = 10
    if len(issues) > max_issues:
        # Sort by priority (security > quality > style > formatting)
        priority_order = {
            'S': 4,  # Security
            'F': 3,  # Fatal/Quality
            'E': 2,  # Error/Style
            'W': 1,  # Warning/Formatting
        }
        
        def get_priority(issue):
            code = issue.get('code', '')
            if code:
                prefix = code[0]
                return priority_order.get(prefix, 0)
            return 0
        
        issues = sorted(issues, key=get_priority, reverse=True)[:max_issues]
        issues.append({'code': '...', 'text': f'and {len(issues) - max_issues} more issues'})
    
    # Format issues
    issues_text = ""
    for issue in issues:
        issues_text += f"Line {issue.get('row', '?')}, Column {issue.get('col', '?')}: {issue.get('code', 'unknown')} - {issue.get('text', '')}\n"
    
    return issues_text

def run_llama_cpp(prompt: str, model: str) -> Optional[str]:
    """
    Run inference with llama.cpp.
    
    Args:
        prompt: Input prompt
        model: Model name/path
        
    Returns:
        Generated text or None if failed
    """
    try:
        # Try to find llama.cpp executable
        llama_paths = [
            "./llama.cpp/main",
            "./llama.cpp/build/bin/main",
            "llama-cpp-python",
            "llama"
        ]
        
        llama_executable = None
        for path in llama_paths:
            try:
                subprocess.run([path, "--help"], capture_output=True, check=True)
                llama_executable = path
                break
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
        
        if not llama_executable:
            logger.error("llama.cpp executable not found")
            return None
        
        # Run inference with configurable timeout
        timeout = int(os.environ.get('CODEFIXER_LLM_TIMEOUT', '60'))
        result = subprocess.run([
            llama_executable,
            "-m", model,
            "-p", prompt,
            "--temp", "0.1",
            "--repeat_penalty", "1.1",
            "--ctx_size", "4096"
        ], capture_output=True, text=True, timeout=timeout)
        
        if result.returncode != 0:
            logger.error(f"llama.cpp failed: {result.stderr}")
            return None
        
        return result.stdout.strip()
        
    except subprocess.TimeoutExpired:
        logger.error("llama.cpp inference timed out")
        return None
    except Exception as e:
        logger.error(f"llama.cpp error: {e}")
        return None

def run_ollama(prompt: str, model: str) -> Optional[str]:
    """
    Run inference with Ollama.
    
    Args:
        prompt: Input prompt
        model: Model name
        
    Returns:
        Generated text or None if failed
    """
    try:
        # Check if Ollama is available
        try:
            subprocess.run(["ollama", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("Ollama not found")
            return None
        
        # Run inference with configurable timeout
        timeout = int(os.environ.get('CODEFIXER_LLM_TIMEOUT', '60'))
        result = subprocess.run([
            "ollama", "run", model, prompt
        ], capture_output=True, text=True, timeout=timeout)
        
        if result.returncode != 0:
            logger.error(f"Ollama failed: {result.stderr}")
            return None
        
        return result.stdout.strip()
        
    except subprocess.TimeoutExpired:
        logger.error("Ollama inference timed out")
        # Retry once with a shorter timeout
        try:
            logger.info("Retrying with shorter timeout...")
            timeout = int(os.environ.get('CODEFIXER_LLM_TIMEOUT', '60')) // 2
            result = subprocess.run([
                "ollama", "run", model, prompt
            ], capture_output=True, text=True, timeout=timeout)
            
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None
    except Exception as e:
        logger.error(f"Ollama error: {e}")
        return None

def extract_code_from_response(response: str) -> str:
    """
    Extract code from LLM response (language-agnostic).
    
    Args:
        response: Raw LLM response
        
    Returns:
        Extracted code
    """
    # Remove common prefixes/suffixes
    lines = response.strip().split('\n')
    
    # Find code block markers
    start_idx = 0
    end_idx = len(lines)
    
    for i, line in enumerate(lines):
        if line.strip().startswith('```'):
            start_idx = i + 1
            break
        elif any(prefix in line.upper() for prefix in ['CORRECTED CODE:', 'FIXED CODE:', 'HERE IS THE FIX:', 'SOLUTION:']):
            start_idx = i + 1
            break
    
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip().startswith('```'):
            end_idx = i
            break
    
    # Extract code
    code_lines = lines[start_idx:end_idx]
    
    # Remove empty lines at start/end
    while code_lines and not code_lines[0].strip():
        code_lines.pop(0)
    while code_lines and not code_lines[-1].strip():
        code_lines.pop()
    
    # If no code blocks found, try to extract from the entire response
    if start_idx == 0 and end_idx == len(lines):
        # Look for common code patterns across languages
        code_lines = []
        in_code = False
        for line in lines:
            # Check for various language patterns
            if any(pattern in line for pattern in [
                'import ', 'def ', 'class ', 'if __name__',  # Python
                'function ', 'const ', 'let ', 'var ', 'export ',  # JavaScript/TypeScript
                '<!DOCTYPE', '<html', '<head', '<body',  # HTML
                '{', '}', ';', '/*', '*/'  # General code patterns
            ]):
                in_code = True
            if in_code:
                code_lines.append(line)
    
    result = '\n'.join(code_lines)
    
    # Basic validation - ensure we have some code content
    if not result.strip() or len(result.strip()) < 10:
        return None
    
    return result

def generate_fix(file_path: Path, issues: List[Dict[str, Any]], model: str = 'gemma3:1b', runner: str = 'ollama', timeout: int = 30, max_retries: int = 3) -> Optional[str]:
    """
    Generate a fix for lint issues using local LLM.
    
    Args:
        file_path: Path to the file with issues
        issues: List of linting issues
        model: LLM model to use
        runner: LLM runner ('ollama' or 'llama.cpp')
        timeout: Request timeout in seconds
        max_retries: Maximum number of retries
        
    Returns:
        Fixed code or None if failed
    """
    logger.debug(f"Generating fix for {file_path} with {len(issues)} issues")
    
    # Build prompt
    prompt = build_prompt(file_path, issues)
    if not prompt:
        return None
    
    for attempt in range(max_retries):
        try:
            logger.debug(f"LLM request attempt {attempt + 1}/{max_retries}")
            
            # Run LLM inference
            response = None
            if runner.lower() == "llama.cpp":
                response = run_llama_cpp(prompt, model)
            elif runner.lower() == "ollama":
                response = run_ollama(prompt, model)
            else:
                logger.error(f"Unknown LLM runner: {runner}")
                return None
            
            if response:
                # Extract code from response
                fixed_code = extract_code_from_response(response)
                
                if fixed_code and fixed_code != "":
                    logger.debug(f"Generated fix successfully on attempt {attempt + 1}")
                    return fixed_code
                else:
                    logger.warning(f"LLM returned empty or unchanged code on attempt {attempt + 1}")
            else:
                logger.warning(f"LLM request failed on attempt {attempt + 1}")
                
        except subprocess.TimeoutExpired:
            logger.warning(f"LLM request timed out on attempt {attempt + 1} (timeout: {timeout}s)")
        except Exception as e:
            logger.warning(f"LLM request error on attempt {attempt + 1}: {e}")
        
        # Wait before retry (exponential backoff)
        if attempt < max_retries - 1:
            wait_time = 2 ** attempt
            logger.debug(f"Waiting {wait_time}s before retry...")
            time.sleep(wait_time)
    
    logger.error(f"Failed to generate fix after {max_retries} attempts")
    return None

def validate_fix(original_code: str, fixed_code: str) -> bool:
    """
    Basic validation of generated fix.
    
    Args:
        original_code: Original source code
        fixed_code: Generated fixed code
        
    Returns:
        True if fix seems valid, False otherwise
    """
    # Basic checks
    if not fixed_code or len(fixed_code.strip()) < 10:
        return False
    
    # Check if the fix is too different (might be hallucination)
    original_lines = original_code.split('\n')
    fixed_lines = fixed_code.split('\n')
    
    # If the number of lines is very different, be suspicious
    if abs(len(original_lines) - len(fixed_lines)) > len(original_lines) * 0.5:
        logger.warning("Generated fix has very different line count")
        return False
    
    return True 

def list_available_models(runner: str = 'ollama') -> List[str]:
    """
    List available models for the specified runner.
    
    Args:
        runner: LLM runner ('ollama' or 'llama.cpp')
        
    Returns:
        List of available model names
    """
    try:
        if runner == 'ollama':
            return list_ollama_models()
        elif runner == 'llama.cpp':
            return list_llamacpp_models()
        else:
            logger.warning(f"Unknown runner: {runner}")
            return []
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        return []

def list_ollama_models() -> List[str]:
    """List available Ollama models."""
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            models = []
            for line in lines:
                if line.strip():
                    # Parse "model_name:tag" format
                    parts = line.split()
                    if parts:
                        model_name = parts[0]
                        models.append(model_name)
            return models
        else:
            logger.error(f"Failed to list Ollama models: {result.stderr}")
            return []
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running ollama list: {e}")
        return []

def list_llamacpp_models() -> List[str]:
    """List available llama.cpp models (from common model directories)."""
    try:
        # Common model directories
        model_dirs = [
            Path.home() / ".local" / "share" / "llama.cpp" / "models",
            Path.home() / "llama.cpp" / "models",
            Path("/usr/local/share/llama.cpp/models"),
            Path("/opt/llama.cpp/models")
        ]
        
        models = set()
        for model_dir in model_dirs:
            if model_dir.exists():
                for model_file in model_dir.glob("*.gguf"):
                    models.add(model_file.stem)
        
        return list(models)
    except Exception as e:
        logger.error(f"Error listing llama.cpp models: {e}")
        return [] 