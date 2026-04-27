"""
Configuration Manager for Room Availability App
-----------------------------------------------

Handles storing and retrieving the ICS URL/file path locally.
Creates a .app_config directory in the user's home directory to store settings.
"""

import os
import json
from pathlib import Path
from typing import Optional


class ConfigManager:
    """Manages application configuration, particularly the ICS URL."""
    
    def __init__(self):
        """Initialize the config manager with app-specific directory."""
        self.config_dir = Path.home() / ".room_availability_app"
        self.config_file = self.config_dir / "config.json"
        self.ics_cache_dir = self.config_dir / "ics_cache"
        
        # Create directories if they don't exist
        self.config_dir.mkdir(exist_ok=True)
        self.ics_cache_dir.mkdir(exist_ok=True)
    
    def has_ics_configured(self) -> bool:
        """Check if an ICS URL has already been configured."""
        if not self.config_file.exists():
            return False
        
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                return bool(config.get('ics_url'))
        except (json.JSONDecodeError, IOError):
            return False
    
    def get_ics_url(self) -> Optional[str]:
        """Retrieve the stored ICS URL."""
        if not self.config_file.exists():
            return None
        
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                return config.get('ics_url')
        except (json.JSONDecodeError, IOError):
            return None
    
    def set_ics_url(self, url: str) -> None:
        """Save the ICS URL to local configuration."""
        config = {}
        
        # Load existing config if it exists
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
            except (json.JSONDecodeError, IOError):
                config = {}
        
        # Update with new URL
        config['ics_url'] = url
        
        # Save back to file
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def get_ics_cache_path(self) -> Path:
        """Get the path where cached ICS file is stored."""
        return self.ics_cache_dir / "calendar.ics"
    
    def save_ics_file(self, ics_data: bytes) -> Path:
        """Save downloaded ICS data to local cache."""
        cache_path = self.get_ics_cache_path()
        with open(cache_path, 'wb') as f:
            f.write(ics_data)
        return cache_path
    
    def get_cached_ics(self) -> Optional[bytes]:
        """Retrieve cached ICS file if it exists."""
        cache_path = self.get_ics_cache_path()
        if cache_path.exists():
            try:
                with open(cache_path, 'rb') as f:
                    return f.read()
            except IOError:
                return None
        return None
    
    def clear_ics_data(self) -> None:
        """Clear the ICS URL and cached calendar file."""
        # Remove the ICS URL from config
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                config['ics_url'] = None
                with open(self.config_file, 'w') as f:
                    json.dump(config, f, indent=2)
            except (json.JSONDecodeError, IOError):
                pass
        
        # Remove the cached ICS file
        cache_path = self.get_ics_cache_path()
        if cache_path.exists():
            try:
                cache_path.unlink()
            except OSError:
                pass
