"""
Configuration manager for CodeFixer.
Handles user configuration files and customization of linter settings.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_CONFIG = {
    "llm": {
        "default_model": "smollm2:135m",
        "default_runner": "ollama",
        "timeout": 60,
        "retry_on_timeout": True
    },
    "linters": {
        "python": {
            "flake8": {
                "max_line_length": 88,
                "extend_ignore": ["E203", "W503", "E501"]
            },
            "black": {
                "line_length": 88
            },
            "mypy": {
                "strict": True
            }
        },
        "javascript": {
            "eslint": {
                "extends": ["eslint:recommended"],
                "rules": {
                    "indent": ["error", 2],
                    "quotes": ["error", "single"],
                    "semi": ["error", "always"]
                }
            },
            "prettier": {
                "semi": True,
                "singleQuote": True,
                "printWidth": 88
            }
        },
        "yaml": {
            "yamllint": {
                "extends": "default",
                "rules": {
                    "line-length": {"max": 88, "level": "warning"},
                    "indentation": {"spaces": 2}
                }
            }
        }
    },
    "git": {
        "default_branch": "codefixer-fixes",
        "create_pr": True,
        "auto_push": True
    },
    "output": {
        "format": "text",
        "show_issues": False,
        "show_diff": False,
        "colors": True
    }
}

def get_config_path() -> Path:
    """Get the path to the user configuration file."""
    home = Path.home()
    config_dir = home / ".codefixer"
    config_dir.mkdir(exist_ok=True)
    return config_dir / "config.json"

def load_user_config() -> Dict[str, Any]:
    """Load user configuration from file."""
    config_path = get_config_path()
    
    if not config_path.exists():
        # Create default config
        save_user_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            user_config = json.load(f)
        
        # Merge with defaults
        return merge_configs(DEFAULT_CONFIG, user_config)
        
    except Exception as e:
        logger.warning(f"Failed to load user config: {e}")
        return DEFAULT_CONFIG

def save_user_config(config: Dict[str, Any]) -> bool:
    """Save user configuration to file."""
    try:
        config_path = get_config_path()
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Failed to save user config: {e}")
        return False

def merge_configs(default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge user config with defaults."""
    result = default.copy()
    
    for key, value in user.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_configs(result[key], value)
        else:
            result[key] = value
    
    return result

def get_linter_config(language: str, linter: str) -> Dict[str, Any]:
    """Get configuration for a specific linter."""
    config = load_user_config()
    return config.get("linters", {}).get(language, {}).get(linter, {})

def get_llm_config() -> Dict[str, Any]:
    """Get LLM configuration."""
    config = load_user_config()
    return config.get("llm", {})

def get_git_config() -> Dict[str, Any]:
    """Get Git configuration."""
    config = load_user_config()
    return config.get("git", {})

def get_output_config() -> Dict[str, Any]:
    """Get output configuration."""
    config = load_user_config()
    return config.get("output", {})

def update_config(section: str, key: str, value: Any) -> bool:
    """Update a specific configuration value."""
    config = load_user_config()
    
    if section not in config:
        config[section] = {}
    
    config[section][key] = value
    
    return save_user_config(config)

def reset_config() -> bool:
    """Reset configuration to defaults."""
    return save_user_config(DEFAULT_CONFIG)

def show_config() -> None:
    """Display current configuration."""
    config = load_user_config()
    print(json.dumps(config, indent=2)) 