"""
Configuration loader for managing YAML configurations.
"""

import yaml
import os
from typing import Dict, Any, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ConfigLoader:
    """
    Handles loading and validation of configuration files.

    Features:
    - YAML configuration file loading
    - Environment variable substitution
    - Configuration validation
    - Default value handling
    """

    @staticmethod
    def load_agent_config(config_path: str) -> Dict[str, Any]:
        """
        Load agent configuration from YAML file.

        Args:
            config_path: Path to the agent configuration file

        Returns:
            Configuration dictionary

        Raises:
            ValueError: If configuration is invalid
            FileNotFoundError: If configuration file doesn't exist
        """
        try:
            config_path = Path(config_path)

            if not config_path.exists():
                raise FileNotFoundError(f"Configuration file not found: {config_path}")

            with open(config_path, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)

            if not config:
                raise ValueError(f"Empty configuration file: {config_path}")

            # Perform environment variable substitution
            config = ConfigLoader._substitute_env_vars(config)

            # Validate required fields
            ConfigLoader._validate_agent_config(config)

            # Apply defaults
            config = ConfigLoader._apply_agent_defaults(config)

            logger.debug(f"Loaded agent configuration from {config_path}")
            return config

        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in configuration file {config_path}: {e}")
        except Exception as e:
            logger.error(f"Error loading agent configuration from {config_path}: {e}")
            raise

    @staticmethod
    def load_server_config(config_path: str = None) -> Dict[str, Any]:
        """
        Load server configuration.

        Args:
            config_path: Optional path to server config file

        Returns:
            Server configuration dictionary
        """
        if config_path is None:
            config_path = os.getenv("SERVER_CONFIG", "configs/server_config.yaml")

        try:
            config_path = Path(config_path)

            if not config_path.exists():
                logger.warning(f"Server config file not found: {config_path}, using defaults")
                return ConfigLoader._get_default_server_config()

            with open(config_path, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)

            # Perform environment variable substitution
            config = ConfigLoader._substitute_env_vars(config)

            # Apply defaults
            config = ConfigLoader._apply_server_defaults(config)

            logger.debug(f"Loaded server configuration from {config_path}")
            return config

        except Exception as e:
            logger.error(f"Error loading server configuration: {e}")
            return ConfigLoader._get_default_server_config()

    @staticmethod
    def load_tool_config(config_path: str) -> Dict[str, Any]:
        """
        Load tool configuration from YAML file.

        Args:
            config_path: Path to the tool configuration file

        Returns:
            Tool configuration dictionary
        """
        try:
            config_path = Path(config_path)

            if not config_path.exists():
                raise FileNotFoundError(f"Tool configuration file not found: {config_path}")

            with open(config_path, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)

            # Perform environment variable substitution
            config = ConfigLoader._substitute_env_vars(config)

            logger.debug(f"Loaded tool configuration from {config_path}")
            return config

        except Exception as e:
            logger.error(f"Error loading tool configuration: {e}")
            raise

    @staticmethod
    def save_config(config: Dict[str, Any], config_path: str):
        """
        Save configuration to YAML file.

        Args:
            config: Configuration dictionary to save
            config_path: Path where to save the configuration
        """
        try:
            config_path = Path(config_path)
            config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(config_path, 'w', encoding='utf-8') as file:
                yaml.dump(config, file, default_flow_style=False, indent=2)

            logger.debug(f"Saved configuration to {config_path}")

        except Exception as e:
            logger.error(f"Error saving configuration to {config_path}: {e}")
            raise

    @staticmethod
    def _substitute_env_vars(config: Any) -> Any:
        """
        Recursively substitute environment variables in configuration.

        Supports ${VAR_NAME} and ${VAR_NAME:default_value} syntax.
        """
        if isinstance(config, dict):
            return {key: ConfigLoader._substitute_env_vars(value) for key, value in config.items()}
        elif isinstance(config, list):
            return [ConfigLoader._substitute_env_vars(item) for item in config]
        elif isinstance(config, str):
            return ConfigLoader._substitute_env_var_string(config)
        else:
            return config

    @staticmethod
    def _substitute_env_var_string(value: str) -> str:
        """
        Substitute environment variables in a string.

        Supports ${VAR_NAME} and ${VAR_NAME:default_value} syntax.
        """
        import re

        # Pattern for ${VAR_NAME} or ${VAR_NAME:default_value}
        pattern = r'\$\{([^}:]+)(?::([^}]*))?\}'

        def replacer(match):
            var_name = match.group(1)
            default_value = match.group(2) if match.group(2) is not None else ""
            return os.getenv(var_name, default_value)

        return re.sub(pattern, replacer, value)

    @staticmethod
    def _validate_agent_config(config: Dict[str, Any]):
        """
        Validate agent configuration has required fields.

        Args:
            config: Configuration dictionary to validate

        Raises:
            ValueError: If required fields are missing
        """
        required_fields = ["name", "type", "implementation"]

        for field in required_fields:
            if field not in config:
                raise ValueError(f"Missing required field in agent configuration: {field}")

        # Validate implementation path
        implementation = config["implementation"]
        if not isinstance(implementation, str) or "." not in implementation:
            raise ValueError(f"Invalid implementation path: {implementation}")

        # Validate tools configuration if present
        if "tools" in config:
            tools = config["tools"]
            if not isinstance(tools, list):
                raise ValueError("Tools configuration must be a list")

            for i, tool in enumerate(tools):
                if not isinstance(tool, dict):
                    raise ValueError(f"Tool configuration {i} must be a dictionary")
                if "class" not in tool:
                    raise ValueError(f"Tool configuration {i} missing required 'class' field")

    @staticmethod
    def _apply_agent_defaults(config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply default values to agent configuration.

        Args:
            config: Agent configuration dictionary

        Returns:
            Configuration with defaults applied
        """
        defaults = {
            "personality": {},
            "system_prompt": f"You are {config.get('name', 'Assistant')}, a helpful AI assistant.",
            "tools": [],
            "memory_config": {
                "remember_conversations": True,
                "context_window": 5,
                "importance_threshold": 0.5
            },
            "collaboration": {
                "can_collaborate_with": [],
                "collaboration_style": "helpful"
            },
            "max_context_length": 4000,
            "max_context_items": 100,
            "max_memories": 1000
        }

        # Merge defaults with provided config
        for key, default_value in defaults.items():
            if key not in config:
                config[key] = default_value
            elif isinstance(default_value, dict) and isinstance(config[key], dict):
                # Merge dictionaries
                config[key] = {**default_value, **config[key]}

        return config

    @staticmethod
    def _get_default_server_config() -> Dict[str, Any]:
        """Get default server configuration."""
        return {
            "server": {
                "host": "0.0.0.0",
                "port": 8000,
                "debug": False,
                "reload": False
            },
            "database": {
                "url": "sqlite:///./data/agentic.db",
                "echo": False
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            },
            "security": {
                "secret_key": "change-this-in-production",
                "access_token_expire_minutes": 30
            },
            "agents": {
                "auto_load": True,
                "config_directory": "agents/configs"
            }
        }

    @staticmethod
    def _apply_server_defaults(config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply default values to server configuration.

        Args:
            config: Server configuration dictionary

        Returns:
            Configuration with defaults applied
        """
        defaults = ConfigLoader._get_default_server_config()

        # Deep merge defaults with provided config
        def deep_merge(base: dict, update: dict) -> dict:
            result = base.copy()
            for key, value in update.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value
            return result

        return deep_merge(defaults, config)

    @staticmethod
    def validate_config_file(config_path: str) -> tuple[bool, list[str]]:
        """
        Validate a configuration file without loading it.

        Args:
            config_path: Path to the configuration file

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        try:
            config_path = Path(config_path)

            if not config_path.exists():
                errors.append(f"Configuration file not found: {config_path}")
                return False, errors

            # Try to parse YAML
            try:
                with open(config_path, 'r', encoding='utf-8') as file:
                    config = yaml.safe_load(file)
            except yaml.YAMLError as e:
                errors.append(f"Invalid YAML syntax: {e}")
                return False, errors

            if not config:
                errors.append("Configuration file is empty")
                return False, errors

            # Check if it's an agent config
            if "name" in config and "type" in config:
                try:
                    ConfigLoader._validate_agent_config(config)
                except ValueError as e:
                    errors.append(str(e))

            return len(errors) == 0, errors

        except Exception as e:
            errors.append(f"Error validating configuration: {e}")
            return False, errors

    @staticmethod
    def list_config_files(directory: str, pattern: str = "*.yaml") -> list[Path]:
        """
        List all configuration files in a directory.

        Args:
            directory: Directory to search
            pattern: File pattern to match

        Returns:
            List of configuration file paths
        """
        try:
            directory_path = Path(directory)
            if not directory_path.exists():
                return []

            return list(directory_path.glob(pattern))

        except Exception as e:
            logger.error(f"Error listing config files in {directory}: {e}")
            return []

    @staticmethod
    def get_config_info(config_path: str) -> Optional[Dict[str, Any]]:
        """
        Get basic information about a configuration file.

        Args:
            config_path: Path to the configuration file

        Returns:
            Dictionary with config info or None if invalid
        """
        try:
            is_valid, errors = ConfigLoader.validate_config_file(config_path)

            if not is_valid:
                return {
                    "path": config_path,
                    "valid": False,
                    "errors": errors
                }

            config = ConfigLoader.load_agent_config(config_path)

            return {
                "path": config_path,
                "valid": True,
                "name": config.get("name"),
                "type": config.get("type"),
                "description": config.get("description", ""),
                "tools": [tool.get("name", tool.get("class", "")) for tool in config.get("tools", [])],
                "collaboration": config.get("collaboration", {}).get("can_collaborate_with", [])
            }

        except Exception as e:
            return {
                "path": config_path,
                "valid": False,
                "errors": [str(e)]
            }
