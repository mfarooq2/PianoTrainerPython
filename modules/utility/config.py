"""
Configuration Management Module

This module handles loading, saving, and accessing application settings and configuration parameters.
It provides a centralized way to manage user preferences and application settings.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, Union
from pathlib import Path


class Config:
    """
    Manages application settings and configuration parameters.
    
    This class is responsible for:
    - Loading configuration from files
    - Providing access to configuration values
    - Saving configuration changes
    - Managing default settings
    """
    
    # Default configuration values
    DEFAULT_CONFIG = {
        "app": {
            "name": "Piano Trainer",
            "version": "1.2.0",
            "author": "Moatasim Farooque",
            "window_width": 1280,
            "window_height": 720,
            "fullscreen": False,
            "fps": 60,
            "default_mode": "freestyle",
            "log_level": "INFO",
            "show_fps": False,
        },
        "midi": {
            "default_tempo": 120,
            "default_volume": 100,
            "note_on_velocity": 100,
            "use_system_midi": True,
            "midi_device_id": 0,
        },
        "keyboard": {
            "start_octave": 2,
            "num_octaves": 5,
            "key_width": 32,
            "key_height": 150,
            "show_note_names": True,
            "highlight_c_notes": True,
            "black_key_color": [40, 40, 40],
            "white_key_color": [250, 250, 250],
            "highlight_color": [0, 150, 255],
        },
        "learning": {
            "falling_speed": 5,
            "note_hit_window": 150,  # milliseconds
            "difficulty_levels": ["easy", "medium", "hard"],
            "difficulty": "medium",
            "score_multiplier": 10,
            "mistake_penalty": 5,
            "success_threshold": 0.8,  # 80% success rate to advance
        },
        "analysis": {
            "default_chunk_size": 8,  # beats
            "show_note_statistics": True,
            "show_chord_analysis": True,
            "highlight_patterns": True,
        },
        "audio": {
            "use_soundfont": True,
            "soundfont_path": "assets/soundfonts/piano.sf2",
            "master_volume": 100,
            "enable_metronome": True,
            "metronome_volume": 80,
        },
        "files": {
            "recent_files": [],
            "max_recent_files": 10,
            "auto_save": True,
            "auto_save_interval": 300,  # seconds
            "default_midi_directory": "~/Music/MIDI",
        }
    }
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_file: Path to the configuration file (optional)
        """
        self.logger = logging.getLogger(__name__)
        
        # Set up paths
        self.app_dir = self._get_app_directory()
        self.config_file = config_file or os.path.join(self.app_dir, "config.json")
        
        # Initialize configuration with defaults
        self.config = self.DEFAULT_CONFIG.copy()
        
        # Load configuration if it exists
        if os.path.exists(self.config_file):
            try:
                self.load()
            except Exception as e:
                self.logger.error("Failed to load configuration: %s", str(e))
                self.logger.info("Using default configuration")
        else:
            self.logger.info("No configuration file found, using defaults")
            # Create config directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            self.save()
    
    def _get_app_directory(self) -> str:
        """
        Get the application data directory.
        
        Returns:
            Path to the application data directory
        """
        home_dir = os.path.expanduser("~")
        
        if os.name == "posix":  # macOS or Linux
            app_dir = os.path.join(home_dir, ".piano-trainer")
        else:  # Windows
            app_dir = os.path.join(os.getenv("APPDATA", home_dir), "PianoTrainer")
        
        # Create directory if it doesn't exist
        os.makedirs(app_dir, exist_ok=True)
        
        return app_dir
    
    def load(self) -> None:
        """
        Load configuration from file.
        
        Raises:
            FileNotFoundError: If the configuration file does not exist
            json.JSONDecodeError: If the configuration file contains invalid JSON
        """
        self.logger.info("Loading configuration from %s", self.config_file)
        with open(self.config_file, "r") as f:
            loaded_config = json.load(f)
            
        # Merge loaded config with defaults to ensure all keys exist
        self._merge_configs(self.config, loaded_config)
        
    def _merge_configs(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """
        Recursively merge source configuration into target.
        
        Args:
            target: Target configuration dictionary to update
            source: Source configuration dictionary to merge from
        """
        for key, value in source.items():
            if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                self._merge_configs(target[key], value)
            else:
                target[key] = value
    
    def save(self) -> None:
        """
        Save configuration to file.
        
        Raises:
            PermissionError: If the file cannot be written to
        """
        self.logger.info("Saving configuration to %s", self.config_file)
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            with open(self.config_file, "w") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            self.logger.error("Failed to save configuration: %s", str(e))
            raise
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key_path: Dot-separated path to the configuration key (e.g., "app.window_width")
            default: Default value to return if the key does not exist
            
        Returns:
            Configuration value or default if not found
        """
        keys = key_path.split(".")
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
                
        return value
    
    def set(self, key_path: str, value: Any) -> None:
        """
        Set a configuration value.
        
        Args:
            key_path: Dot-separated path to the configuration key (e.g., "app.window_width")
            value: Value to set
            
        Raises:
            KeyError: If the key path is invalid
        """
        keys = key_path.split(".")
        config_section = self.config
        
        # Navigate to the parent dictionary
        for key in keys[:-1]:
            if key not in config_section:
                config_section[key] = {}
            config_section = config_section[key]
            
        # Set the value
        config_section[keys[-1]] = value
        
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get a configuration section.
        
        Args:
            section: Name of the configuration section
            
        Returns:
            Dictionary containing the section configuration or empty dict if not found
        """
        return self.config.get(section, {})
    
    def reset_to_defaults(self) -> None:
        """Reset all configuration values to their defaults."""
        self.config = self.DEFAULT_CONFIG.copy()
        self.save()
        self.logger.info("Configuration reset to defaults")
    
    def add_recent_file(self, file_path: str) -> None:
        """
        Add a file to the recent files list.
        
        Args:
            file_path: Path to the file to add
        """
        recent_files = self.get("files.recent_files", [])
        max_recent = self.get("files.max_recent_files", 10)
        
        # Ensure absolute path
        file_path = os.path.abspath(file_path)
        
        # Remove if already in list
        if file_path in recent_files:
            recent_files.remove(file_path)
            
        # Add to the beginning
        recent_files.insert(0, file_path)
        
        # Trim list if needed
        if len(recent_files) > max_recent:
            recent_files = recent_files[:max_recent]
            
        self.set("files.recent_files", recent_files)
        self.save()

