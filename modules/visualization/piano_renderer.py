import pygame
import numpy as np
from ..utility.config import Config
from ..utility.constants import WHITE_KEY_COLOR, BLACK_KEY_COLOR, WHITE_KEY_PRESSED_COLOR, BLACK_KEY_PRESSED_COLOR

class PianoRenderer:
    """
    Class responsible for rendering a piano keyboard on screen
    and handling key highlighting for pressed notes.
    """
    def __init__(self, config):
        """
        Initialize the piano renderer with configuration parameters.
        
        Args:
            config (Config): Application configuration
        """
        self.config = config
        self.screen_width = config.screen_width
        self.screen_height = config.screen_height
        self.piano_height = config.piano_height
        self.y_position = config.screen_height - config.piano_height
        
        # Piano key dimensions and positions
        self.white_key_width = 0
        self.white_key_height = self.piano_height
        self.black_key_width = 0
        self.black_key_height = self.piano_height * 0.6
        
        # Lists to store the positions and dimensions of each piano key
        self.white_keys = []  # (x, y, width, height, note_number)
        self.black_keys = []  # (x, y, width, height, note_number)
        
        # Map note numbers to their respective keys
        self.note_to_key = {}
        
        # Set of currently pressed keys
        self.pressed_keys = set()
        
        # Calculate the initial layout
        self.calculate_layout()
    
    def calculate_layout(self):
        """Calculate the layout of the piano keys based on the current screen dimensions."""
        # Define constants
        num_white_keys = 52  # C1 to C6 range (52 white keys)
        
        # Calculate white key dimensions
        self.white_key_width = self.screen_width / num_white_keys
        self.white_key_height = self.piano_height
        
        # Calculate black key dimensions
        self.black_key_width = self.white_key_width * 0.6
        self.black_key_height = self.piano_height * 0.6
        
        # Clear the key lists
        self.white_keys = []
        self.black_keys = []
        self.note_to_key = {}
        
        # MIDI note number for C1 (first white key)
        start_note = 24
        
        # Generate the white keys
        for i in range(num_white_keys):
            x = i * self.white_key_width
            y = self.y_position
            
            # Calculate the MIDI note number for this white key
            note_number = start_note + i
            
            # Adjust for black keys (every 2nd and 3rd, 5th, 6th, and 7th keys in an octave have black keys after them)
            if i % 7 != 2 and i % 7 != 6:
                note_number = start_note + i + (i // 7) * 5 + min(i % 7, 2) + max(0, (i % 7) - 3)
            
            self.white_keys.append((x, y, self.white_key_width, self.white_key_height, note_number))
            self.note_to_key[note_number] = ('white', len(self.white_keys) - 1)
        
        # Generate the black keys
        black_key_indices = [0, 1, 3, 4, 5]  # Indices of white keys that have black keys to their right (C, D, F, G, A)
        
        for i in range(num_white_keys - 1):
            if i % 7 in black_key_indices:
                x = (i + 0.7) * self.white_key_width - self.black_key_width / 2
                y = self.y_position
                
                # Calculate the MIDI note number for this black key
                if i % 7 < 2:
                    # C# and D#
                    note_number = start_note + i + (i // 7) * 5 + min(i % 7, 2) + max(0, (i % 7) - 3) + 1
                else:
                    # F#, G#, A#
                    note_number = start_note + i + (i // 7) * 5 + min(i % 7, 2) + max(0, (i % 7) - 3) + 1
                
                self.black_keys.append((x, y, self.black_key_width, self.black_key_height, note_number))
                self.note_to_key[note_number] = ('black', len(self.black_keys) - 1)
    
    def resize(self, screen_width, screen_height):
        """
        Resize the piano keyboard based on new screen dimensions.
        
        Args:
            screen_width (int): New screen width
            screen_height (int): New screen height
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.y_position = screen_height - self.piano_height
        
        # Recalculate the piano layout
        self.calculate_layout()
    
    def press_key(self, note_number):
        """
        Mark a piano key as pressed.
        
        Args:
            note_number (int): MIDI note number to press
        """
        if note_number in self.note_to_key:
            self.pressed_keys.add(note_number)
    
    def release_key(self, note_number):
        """
        Mark a piano key as released.
        
        Args:
            note_number (int): MIDI note number to release
        """
        if note_number in self.pressed_keys:
            self.pressed_keys.remove(note_number)
    
    def draw(self, surface):
        """
        Draw the piano keyboard on the provided surface.
        
        Args:
            surface (pygame.Surface): Surface to draw the piano on
        """
        # Draw white keys
        for i, (x, y, width, height, note_number) in enumerate(self.white_keys):
            color = WHITE_KEY_PRESSED_COLOR if note_number in self.pressed_keys else WHITE_KEY_COLOR
            pygame.draw.rect(surface, color, (x, y, width, height))
            pygame.draw.rect(surface, (0, 0, 0), (x, y, width, height), 1)
        
        # Draw black keys (on top of white keys)
        for i, (x, y, width, height, note_number) in enumerate(self.black_keys):
            color = BLACK_KEY_PRESSED_COLOR if note_number in self.pressed_keys else BLACK_KEY_COLOR
            pygame.draw.rect(surface, color, (x, y, width, height))
            pygame.draw.rect(surface, (0, 0, 0), (x, y, width, height), 1)

import pygame
from typing import Dict, List, Optional, Set, Tuple
import math

from modules.core.app_state import AppState
from modules.utility.config import Config


class PianoRenderer:
    """
    Class for rendering a piano keyboard visualization.
    Handles drawing the piano keys, highlighting pressed keys, and animating notes.
    """
    
    # Constants for piano keyboard layout
    WHITE_KEY_WIDTH = 24
    WHITE_KEY_HEIGHT = 120
    BLACK_KEY_WIDTH = 14
    BLACK_KEY_HEIGHT = 80
    
    # Keyboard layout
    WHITE_KEYS_PER_OCTAVE = 7
    KEYS_PER_OCTAVE = 12
    
    # Key colors
    WHITE_KEY_COLOR = (255, 255, 255)
    BLACK_KEY_COLOR = (0, 0, 0)
    WHITE_KEY_HIGHLIGHT_COLOR = (102, 178, 255)  # Light blue
    BLACK_KEY_HIGHLIGHT_COLOR = (51, 153, 255)   # Darker blue
    WHITE_KEY_BORDER_COLOR = (180, 180, 180)
    
    # Labels
    NOTE_NAMES = ['C', '', 'D', '', 'E', 'F', '', 'G', '', 'A', '', 'B']
    OCTAVE_START_NOTE = 0  # C is 0 in the 12-note octave
    
    def __init__(self, app_state: AppState, config: Config):
        """
        Initialize the piano keyboard renderer.
        
        Args:
            app_state: The application state object
            config: The configuration settings
        """
        self.app_state = app_state
        self.config = config
        
        # Surface to render the piano on
        self.surface: Optional[pygame.Surface] = None
        
        # Piano keyboard range
        self.min_note = 21   # A0 (lowest piano key)
        self.max_note = 108  # C8 (highest piano key)
        
        # Cache of key positions for faster rendering
        self.white_key_positions: Dict[int, pygame.Rect] = {}
        self.black_key_positions: Dict[int, pygame.Rect] = {}
        
        # For animation effects
        self.animation_frames: Dict[int, int] = {}
        self.max_animation_frames = 10
        
        # Font for note labels
        self.font: Optional[pygame.font.Font] = None
        self.show_note_labels = True
    
    def setup(self, surface: pygame.Surface):
        """
        Set up the piano renderer with the given surface.
        
        Args:
            surface: Pygame surface to render on
        """
        self.surface = surface
        self.font = pygame.font.SysFont('Arial', 10)
        
        # Calculate key positions
        self._calculate_key_positions()
    
    def _calculate_key_positions(self):
        """Calculate the positions of all piano keys."""
        if not self.surface:
            return
            
        # Clear previous positions
        self.white_key_positions.clear()
        self.black_key_positions.clear()
        
        # Get the available width for the piano
        surface_width = self.surface.get_width()
        surface_height = self.surface.get_height()
        
        # Count white keys in the range
        white_key_count = sum(1 for note in range(self.min_note, self.max_note + 1) 
                              if self._is_white_key(note))
        
        # Adjust key width if needed to fit the piano in the window
        adjusted_white_key_width = min(
            self.WHITE_KEY_WIDTH,
            surface_width / white_key_count
        )
        adjusted_black_key_width = adjusted_white_key_width * (self.BLACK_KEY_WIDTH / self.WHITE_KEY_WIDTH)
        
        # Calculate the starting x position to center the piano
        total_width = white_key_count * adjusted_white_key_width
        start_x = (surface_width - total_width) / 2
        
        # Calculate the y position to place the piano at the bottom
        y_position = surface_height - self.WHITE_KEY_HEIGHT
        
        # Calculate positions for each key
        white_key_index = 0
        
        for note in range(self.min_note, self.max_note + 1):
            if self._is_white_key(note):
                # Position white key
                x = start_x + (white_key_index * adjusted_white_key_width)
                self.white_key_positions[note] = pygame.Rect(
                    x, y_position, adjusted_white_key_width, self.WHITE_KEY_HEIGHT
                )
                white_key_index += 1
        
        # Now add black keys (so they overlap white keys)
        for note in range(self.min_note, self.max_note + 1):
            if not self._is_white_key(note):
                # Find the white key to the left
                white_key_left = note - 1
                while white_key_left >= self.min_note and not self._is_white_key(white_key_left):
                    white_key_left -= 1
                
                # Find the white key to the right
                white_key_right = note + 1
                while white_key_right <= self.max_note and not self._is_white_key(white_key_right):
                    white_key_right += 1
                
                # Position black key between white keys
                if white_key_left in self.white_key_positions and white_key_right in self.white_key_positions:
                    left_rect = self.white_key_positions[white_key_left]
                    right_rect = self.white_key_positions[white_key_right]
                    
                    # Place black key between the two white keys
                    x = left_rect.right - (adjusted_black_key_width / 2)
                    
                    # If it's a B-C or E-F boundary, adjust position
                    note_in_octave = note % self.KEYS_PER_OCTAVE
                    if note_in_octave == 3 or note_in_octave == 10:  # Between E-F or B-C
                        x = right_rect.left - (adjusted_black_key_width / 2)
                    
                    self.black_key_positions[note] = pygame.Rect(
                        x, y_position, adjusted_black_key_width, self.BLACK_KEY_HEIGHT
                    )
    
    def _is_white_key(self, note: int) -> bool:
        """
        Determine if a note is a white key.
        
        Args:
            note: MIDI note number
            
        Returns:
            True if the note is a white key, False if it's a black key
        """
        # C, D, E, F, G, A, B are white keys (0, 2, 4, 5, 7, 9, 11 in the octave)
        note_in_octave = (note % self.KEYS_PER_OCTAVE)
        return note_in_octave in [0, 2, 4, 5, 7, 9, 11]
    
    def render(self, active_notes: Set[int], playback_notes: Set[int]):
        """
        Render the piano keyboard with highlighted keys.
        
        Args:
            active_notes: Set of currently pressed MIDI notes from user input
            playback_notes: Set of notes currently being played from MIDI file
        """
        if not self.surface:
            return
            
        # Get all notes that should be highlighted (either pressed or played)
        highlighted_notes = active_notes.union(playback_notes)
        
        # Draw white keys first
        for note, rect in self.white_key_positions.items():
            if note in highlighted_notes:
                # Draw highlighted white key
                pygame.draw.rect(self.surface, self.WHITE_KEY_HIGHLIGHT_COLOR, rect)
                # Start animation for newly pressed keys
                if note not in self.animation_frames:
                    self.animation_frames[note] = self.max_animation_frames
            else:
                # Draw normal white key
                pygame.draw.rect(self.surface, self.WHITE_KEY_COLOR, rect)
            
            # Draw border for white key
            pygame.draw.rect(self.surface, self.WHITE_KEY_BORDER_COLOR, rect, 1)
            
            # Draw note label if enabled
            if self.show_note_labels:
                note_in_octave = note % self.KEYS_PER_OCTAVE
                octave = (note // self.KEYS_PER_OCTAVE) - 1  # MIDI note 0 is C-1
                
                # Only label C notes (or all white keys if configured)
                if note_in_octave == self.OCTAVE_START_NOTE:
                    label = f"C{octave}"
                    label_surface = self.font.render(label, True, (0, 0, 0))
                    label_pos = (rect.x + 2, rect.bottom - label_surface.get_height() - 2)
                    self.surface.blit(label_surface, label_pos)
        
        # Then draw black keys (so they appear on top)
        for note, rect in self.black_key_positions.items():
            if note in highlighted_notes:
                # Draw highlighted black key
                pygame.draw.rect(self.surface, self.BLACK_KEY_HIGHLIGHT_COLOR, rect)
                # Start animation for newly pressed keys
                if note not in self.animation_frames:
                    self.animation_frames[note] = self.max_animation_frames
            else:
                # Draw normal black key
                pygame.draw.rect(self.surface, self.BLACK_KEY_COLOR, rect)
        
        # Update animations
        self._update_animations()
    
    def _update_animations(self):
        """Update animations for key presses."""
        keys_to_remove = []
        
        for note, frames in self.animation_frames.items():
            frames -= 1
            
            if frames <= 0:
                keys_to_remove.append(note)
            else:
                self.animation_frames[note] = frames
                
                # Draw ripple effect or glow based on remaining frames
                if note in self.white_key_positions:
                    rect = self.white_key_positions[note]
                    alpha = int(255 * (frames / self.max_animation_frames))
                    self._draw_ripple(rect, alpha)
                elif note in self.black_key_positions:
                    rect = self.black_key_positions[note]
                    alpha = int(255 * (frames / self.max_animation_frames))
                    self._draw_ripple(rect, alpha)
        
        # Remove finished animations
        for note in keys_to_remove:
            self.animation_frames.pop(note)
    
    def _draw_ripple(self, rect: pygame.Rect, alpha: int):
        """
        Draw a ripple effect around a key.
        
        Args:
            rect: The key rectangle
            alpha: Transparency value (0-255)
        """
        if alpha <= 0:
            return
            
        # Create a surface for the ripple with transparency
        ripple_surface = pygame.Surface((rect.width + 10, rect.height + 10), pygame.SRCALPHA)
        
        # Draw the ripple (a glow around the key)
        pygame.draw.rect(
            ripple_surface, 
            (*self.WHITE_KEY_HIGHLIGHT_COLOR, alpha), 
            pygame.Rect(5, 5, rect.width, rect.height),
            3,  # Border width for glow effect
            border_radius=2
        )
        
        # Blit the ripple surface onto the main surface
        self.surface.blit(ripple_surface, (rect.x - 5, rect.y - 5))
    
    def resize(self, new_width: int, new_height: int):
        """
        Handle resizing of

