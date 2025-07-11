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
    template_path = Path("templates/fix_prompt.txt")
    
    if template_path.exists():
        try:
            with open(template_path, "r") as f:
                return f.read()
        except Exception as e:
            logger.warning(f"Failed to load prompt template: {e}")
    
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
    
    # Format issues
    issues_text = ""
    for issue in issues:
        issues_text += f"Line {issue.get('row', '?')}, Column {issue.get('col', '?')}: {issue.get('code', 'unknown')} - {issue.get('text', '')}\n"
    
    # Load and format prompt template
    template = load_prompt_template()
    prompt = template.format(
        code=code,
        issues=issues_text.strip()
    )
    
    return prompt

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
        
        # Run inference
        result = subprocess.run([
            llama_executable,
            "-m", model,
            "-p", prompt,
            "--temp", "0.1",
            "--repeat_penalty", "1.1",
            "--ctx_size", "4096"
        ], capture_output=True, text=True, timeout=60)
        
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
        
        # Run inference
        result = subprocess.run([
            "ollama", "run", model, prompt
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            logger.error(f"Ollama failed: {result.stderr}")
            return None
        
        return result.stdout.strip()
        
    except subprocess.TimeoutExpired:
        logger.error("Ollama inference timed out")
        return None
    except Exception as e:
        logger.error(f"Ollama error: {e}")
        return None

def extract_code_from_response(response: str) -> str:
    """
    Extract code from LLM response.
    
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
        elif 'CORRECTED CODE:' in line or 'FIXED CODE:' in line:
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
        # Look for Python code patterns
        code_lines = []
        in_code = False
        for line in lines:
            if any(keyword in line for keyword in ['import ', 'def ', 'class ', 'if __name__']):
                in_code = True
            if in_code:
                code_lines.append(line)
    
    result = '\n'.join(code_lines)
    
    # Basic validation - ensure we have some Python code
    if not any(keyword in result for keyword in ['import', 'def', 'class', 'if', 'pass']):
        return ""
    
    return result

def generate_fix(file_path: Path, issues: List[Dict[str, Any]], model: str, runner: str = "llama.cpp") -> Optional[str]:
    """
    Generate a fix for lint issues using local LLM.
    
    Args:
        file_path: Path to the file with issues
        issues: List of linting issues
        model: Model name/path
        runner: LLM runner to use (llama.cpp, ollama)
        
    Returns:
        Fixed code or None if failed
    """
    logger.debug(f"Generating fix for {file_path} with {len(issues)} issues")
    
    # Build prompt
    prompt = build_prompt(file_path, issues)
    if not prompt:
        return None
    
    # Run LLM inference
    response = None
    if runner.lower() == "llama.cpp":
        response = run_llama_cpp(prompt, model)
    elif runner.lower() == "ollama":
        response = run_ollama(prompt, model)
    else:
        logger.error(f"Unknown LLM runner: {runner}")
        return None
    
    if not response:
        logger.error(f"Failed to generate response for {file_path}")
        return None
    
    # Extract code from response
    fixed_code = extract_code_from_response(response)
    
    if not fixed_code:
        logger.error(f"Failed to extract code from response for {file_path}")
        return None
    
    logger.debug(f"Generated fix for {file_path}")
    return fixed_code

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