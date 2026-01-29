"""
Settings Manager

Handles dynamic configuration by creating an overlay on top of the base config.yaml.
Allows settings like leverage, risk, and confidence thresholds to be changed at runtime.
"""

import os
import yaml
import json
import logging
from typing import Any, Dict

class SettingsManager:
    """
    Manages application settings with hot-reloading support.
    
    Layers:
    1. Base config (config.yaml) - Static defaults
    2. Overlay (settings_overlay.json) - Dynamic user overrides
    """
    
    def __init__(self, config_path: str = "config/live_trading_config.yaml", overlay_path: str = "config/settings_overlay.json"):
        self.logger = logging.getLogger("hedgemony.settings")
        self.config_path = config_path
        self.overlay_path = overlay_path
        self._config = {}
        self.reload()
    
    def reload(self):
        """Reload configuration from disk."""
        # 1. Load base config
        base_config = {}
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    base_config = yaml.safe_load(f) or {}
            except Exception as e:
                self.logger.error(f"Failed to load base config: {e}")
        
        # 2. Load overlay
        overlay = {}
        if os.path.exists(self.overlay_path):
            try:
                with open(self.overlay_path, 'r') as f:
                    overlay = json.load(f) or {}
            except Exception as e:
                self.logger.error(f"Failed to load settings overlay: {e}")
        
        # 3. Merge (Recursive update)
        self._config = self._deep_update(base_config, overlay)
        self.logger.debug("Settings reloaded")
        
    def _deep_update(self, base: Dict, update: Dict) -> Dict:
        """Recursively update a dictionary."""
        for k, v in update.items():
            if isinstance(v, dict) and k in base and isinstance(base[k], dict):
                base[k] = self._deep_update(base[k], v)
            else:
                base[k] = v
        return base
    
    def get(self, path: str, default: Any = None) -> Any:
        """
        Get a setting value by dot-notation path.
        Example: get("trading.risk.max_leverage", 1)
        """
        keys = path.split('.')
        value = self._config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
    
    def set(self, path: str, value: Any):
        """
        Set a setting value and save to overlay.
        Example: set("trading.risk.max_leverage", 10)
        """
        # Load current overlay to preserve other overrides
        overlay = {}
        if os.path.exists(self.overlay_path):
            try:
                with open(self.overlay_path, 'r') as f:
                    overlay = json.load(f) or {}
            except:
                pass
        
        # Update overlay at path
        keys = path.split('.')
        current = overlay
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
            if not isinstance(current, dict): # Handle case where intermediate node matches a value
                current = {} 
        
        current[keys[-1]] = value
        
        # Save overlay
        try:
            with open(self.overlay_path, 'w') as f:
                json.dump(overlay, f, indent=2)
            self.reload() # Reload combined config
            return True
        except Exception as e:
            self.logger.error(f"Failed to save setting: {e}")
            return False

    def get_all(self) -> Dict:
        """Return the full merged configuration."""
        return self._config.copy()
