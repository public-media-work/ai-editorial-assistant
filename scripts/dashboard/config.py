"""
Configuration system for the dashboard.

Provides DashboardConfig class for loading and accessing dashboard settings
with dot-path notation.
"""

import json
from pathlib import Path
from typing import Any, Optional


class DashboardConfig:
    """
    Manages dashboard configuration from JSON file with dot-path access.

    Loads configuration from a JSON file or uses defaults if file doesn't exist.
    Supports dot-path notation for accessing nested values (e.g., 'display.refresh_rate').
    """

    def __init__(self, config_path: Path) -> None:
        """
        Initialize configuration from file or defaults.

        Args:
            config_path: Path to the dashboard.json configuration file
        """
        self.config_path = Path(config_path)
        self.config = self.load_config()

    def load_config(self) -> dict:
        """
        Load configuration from JSON file or return defaults.

        If the config file exists, load it and merge with defaults.
        If it doesn't exist, return the default configuration.

        Returns:
            Configuration dictionary with all settings
        """
        if not self.config_path.exists():
            return self.get_defaults()

        try:
            with open(self.config_path, "r") as f:
                file_config = json.load(f)
            # Merge with defaults (file config takes precedence)
            defaults = self.get_defaults()
            return self._deep_merge(defaults, file_config)
        except (json.JSONDecodeError, IOError):
            return self.get_defaults()

    def get_defaults(self) -> dict:
        """
        Return the default dashboard configuration.

        Returns:
            Default configuration dictionary with all sections and settings
        """
        return {
            "display": {
                "refresh_rate": 4,
                "log_buffer_size": 8,
                "theme": "default",
                "show_sparkline": True,
                "cost_timeline_minutes": 60,
            },
            "behavior": {
                "auto_clear_completed": False,
                "auto_check_new_interval_seconds": 0,
                "pause_on_error": False,
                "max_retries": 3,
            },
            "cost": {
                "warning_threshold_per_hour": 10.0,
                "alert_threshold_per_project": 1.0,
                "show_estimates": True,
            },
            "keyboard": {
                "pause": "p",
                "skip": "s",
                "retry": "r",
                "errors": "e",
                "remove": "x",
                "restart": "d",
                "logs": "l",
                "export": "t",
                "quit": "q",
                "clear": "c",
                "new": "n",
            },
        }

    def get(self, path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot-path notation.

        Supports nested access like 'display.refresh_rate' or 'keyboard.pause'.
        Returns default value if path doesn't exist.

        Args:
            path: Dot-separated path to the configuration value
            default: Default value to return if path not found

        Returns:
            Configuration value or default value
        """
        keys = path.split(".")
        value = self.config

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return default
            else:
                return default

        return value if value is not None else default

    @staticmethod
    def _deep_merge(base: dict, override: dict) -> dict:
        """
        Deep merge override dict into base dict.

        Args:
            base: Base dictionary
            override: Dictionary with overrides

        Returns:
            Merged dictionary with override values taking precedence
        """
        result = base.copy()
        for key, value in override.items():
            if isinstance(value, dict) and key in result and isinstance(result[key], dict):
                result[key] = DashboardConfig._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
