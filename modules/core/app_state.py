"""
Application State Management Module

This module handles the application's state, mode transitions, and global state variables.
It provides a centralized way to manage the application's current mode, settings, and state transitions.
"""

from enum import Enum, auto
from typing import Dict, Any, Optional, Callable, List
import logging

from modules.utility.config import Config


class AppMode(Enum):
    """Enum representing the different application modes."""
    FREESTYLE = auto()  # Free playing mode without guidance
    LEARNING = auto()   # Learning mode with falling notes
    ANALYSIS = auto()   # Analysis view for MIDI files


class AppState:
    """
    Manages the application state, mode transitions, and global state.
    
    This class is responsible for:
    - Tracking the current application mode
    - Managing mode transitions
    - Maintaining global state variables
    - Providing access to configuration
    """
    
    def __init__(self, config: Config):
        """
        Initialize the application state.
        
        Args:
            config: The application configuration
        """
        self.config = config
        self.current_mode = AppMode.FREESTYLE  # Default mode
        self.previous_mode = None
        
        # Global state variables
        self.state: Dict[str, Any] = {
            "is_playing": False,
            "current_midi_file": None,
            "active_notes": set(),
            "score": 0,
            "midi_input_device": None,
            "midi_output_device": None,
            "current_tempo": 120,
            "volume": 100,
        }
        
        # Mode-specific state variables
        self.mode_states: Dict[AppMode, Dict[str, Any]] = {
            AppMode.FREESTYLE: {
                "show_note_names": True,
                "highlight_octaves": False,
            },
            AppMode.LEARNING: {
                "falling_speed": config.get("learning.falling_speed", 5),
                "note_hit_window": config.get("learning.note_hit_window", 150),  # milliseconds
                "difficulty": config.get("learning.difficulty", "medium"),
                "current_level": 1,
                "mistakes": 0,
                "success_rate": 0.0,
            },
            AppMode.ANALYSIS: {
                "show_note_statistics": True,
                "show_chord_analysis": True,
                "highlight_patterns": True,
                "current_position": 0,
            }
        }
        
        # Mode transition callbacks
        self.mode_change_callbacks: List[Callable[[AppMode, AppMode], None]] = []
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.info("AppState initialized with default mode: %s", self.current_mode)
    
    def change_mode(self, new_mode: AppMode) -> None:
        """
        Change the application mode and trigger mode change callbacks.
        
        Args:
            new_mode: The new mode to transition to
        """
        if new_mode == self.current_mode:
            return
            
        self.logger.info("Mode change: %s -> %s", self.current_mode, new_mode)
        self.previous_mode = self.current_mode
        self.current_mode = new_mode
        
        # Execute mode change callbacks
        for callback in self.mode_change_callbacks:
            try:
                callback(self.previous_mode, self.current_mode)
            except Exception as e:
                self.logger.error("Error in mode change callback: %s", str(e))
    
    def register_mode_change_callback(self, callback: Callable[[AppMode, AppMode], None]) -> None:
        """
        Register a callback to be executed when the mode changes.
        
        Args:
            callback: Function to be called with previous and new mode as arguments
        """
        self.mode_change_callbacks.append(callback)
    
    def get_mode_state(self, key: str, default: Any = None) -> Any:
        """
        Get a mode-specific state value.
        
        Args:
            key: The state key to retrieve
            default: Default value if key doesn't exist
            
        Returns:
            The state value or default if not found
        """
        mode_state = self.mode_states.get(self.current_mode, {})
        return mode_state.get(key, default)
    
    def set_mode_state(self, key: str, value: Any) -> None:
        """
        Set a mode-specific state value.
        
        Args:
            key: The state key to set
            value: The value to set
        """
        if self.current_mode in self.mode_states:
            self.mode_states[self.current_mode][key] = value
    
    def get_state(self, key: str, default: Any = None) -> Any:
        """
        Get a global state value.
        
        Args:
            key: The state key to retrieve
            default: Default value if key doesn't exist
            
        Returns:
            The state value or default if not found
        """
        return self.state.get(key, default)
    
    def set_state(self, key: str, value: Any) -> None:
        """
        Set a global state value.
        
        Args:
            key: The state key to set
            value: The value to set
        """
        self.state[key] = value
        self.logger.debug("State updated: %s = %s", key, value)
    
    def reset_score(self) -> None:
        """Reset the player's score."""
        self.state["score"] = 0
        self.mode_states[AppMode.LEARNING]["mistakes"] = 0
        self.mode_states[AppMode.LEARNING]["success_rate"] = 0.0
    
    def reset_to_defaults(self) -> None:
        """Reset all state values to their defaults."""
        self.__init__(self.config)
        self.logger.info("AppState reset to defaults")

