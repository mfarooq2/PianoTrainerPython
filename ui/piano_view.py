import pygame
import pygame.midi
from typing import Dict, List, Tuple, Optional, Union, Set

class PianoKey:
    """Class representing a single piano key with its properties and state"""
    
    def __init__(self, 
                note_number: int, 
                is_white: bool, 
                position: Tuple[int, int], 
                size: Tuple[int, int]):
        self.note_number = note_number
        self.is_white = is_white
        self.position = position  # (x, y)
        self.size = size          # (width, height)
        self.is_pressed = False
        self.highlight_color = None
        self.label = ""
    
    def contains_point(self, point: Tuple[int, int]) -> bool:
        """Check if a point is within the key's bounds"""
        x, y = point
        kx, ky = self.position
        kw, kh = self.size
        return (kx <= x <= kx + kw) and (ky <= y <= ky + kh)
    
    def draw(self, surface: pygame.Surface, 
             colors: Dict[str, Tuple[int, int, int]],
             show_labels: bool = True,
             font: Optional[pygame.font.Font] = None) -> None:
        """Draw the key on the given surface"""
        # Determine the color based on the key state
        if self.highlight_color:
            color = self.highlight_color
        elif self.is_pressed:
            color = colors['pressed'] if self.is_white else colors['black_pressed']
        else:
            color = colors['white'] if self.is_white else colors['black']
        
        # Draw the key
        pygame.draw.rect(surface, color, (*self.position, *self.size))
        
        # Draw the border
        border_color = colors['border']
        pygame.draw.rect(surface, border_color, (*self.position, *self.size), 1)
        
        # Draw the label if requested
        if show_labels and self.label and font:
            label_surface = font.render(self.label, True, colors['text'])
            label_rect = label_surface.get_rect(
                center=(self.position[0] + self.size[0] // 2,
                        self.position[1] + self.size[1] - 15)
            )
            surface.blit(label_surface, label_rect)


class PianoView:
    """A modular piano visualization component that can be used in various piano applications"""
    
    # Class constants for the piano layout
    WHITE_KEY_WIDTH = 24
    WHITE_KEY_HEIGHT = 120
    BLACK_KEY_WIDTH = 14
    BLACK_KEY_HEIGHT = 80
    BLACK_KEY_OFFSETS = {
        0: 14,   # C#
        2: 38,   # D#
        5: 86,   # F#
        7: 110,  # G#
        9: 134   # A#
    }
    
    # Piano dimensions
    PIANO_MARGIN = 10
    
    # Default colors
    DEFAULT_COLORS = {
        'white': (255, 255, 255),
        'black': (0, 0, 0),
        'pressed': (153, 217, 234),
        'black_pressed': (0, 162, 232),
        'highlight': (255, 0, 0),
        'border': (128, 128, 128),
        'text': (0, 0, 0),
        'background': (240, 240, 240)
    }
    
    # Note names
    NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    
    def __init__(self, 
                 start_note: int = 21,  # A0
                 end_note: int = 108,   # C8
                 width: Optional[int] = None,
                 height: Optional[int] = None,
                 colors: Optional[Dict[str, Tuple[int, int, int]]] = None,
                 show_labels: bool = True,
                 label_type: str = 'note_name'):  # 'note_name', 'midi_note', 'both', 'none'
        
        self.start_note = start_note
        self.end_note = end_note
        self.show_labels = show_labels
        self.label_type = label_type
        
        # Set colors, using defaults if none provided
        self.colors = self.DEFAULT_COLORS.copy()
        if colors:
            self.colors.update(colors)
        
        # Initialize the keys dictionary
        self.keys: Dict[int, PianoKey] = {}
        
        # Initialize pressed and highlighted notes
        self.pressed_notes: Set[int] = set()
        self.highlighted_notes: Dict[int, Tuple[int, int, int]] = {}
        
        # Calculate dimensions if not provided
        self._calculate_dimensions(width, height)
        
        # Initialize font
        self.font = None
        
        # Create the piano surface
        self.surface = pygame.Surface((self.width, self.height))
        
        # Initialize the piano layout
        self._init_piano_layout()
    
    def _calculate_dimensions(self, width: Optional[int], height: Optional[int]) -> None:
        """Calculate the piano dimensions based on the number of keys"""
        # Count white keys
        white_keys = sum(1 for note in range(self.start_note, self.end_note + 1) 
                         if (note % 12) not in {1, 3, 6, 8, 10})
        
        # Calculate minimum width and height
        min_width = white_keys * self.WHITE_KEY_WIDTH + 2 * self.PIANO_MARGIN
        min_height = self.WHITE_KEY_HEIGHT + 2 * self.PIANO_MARGIN
        
        # Set dimensions, using provided values or calculated minimums
        self.width = max(width or 0, min_width)
        self.height = max(height or 0, min_height)
    
    def _init_piano_layout(self) -> None:
        """Initialize the piano key layout"""
        x = self.PIANO_MARGIN
        white_index = 0
        
        # First create all white keys
        for note in range(self.start_note, self.end_note + 1):
            note_type = note % 12
            
            if note_type not in {1, 3, 6, 8, 10}:  # White keys
                position = (x, self.PIANO_MARGIN)
                size = (self.WHITE_KEY_WIDTH, self.WHITE_KEY_HEIGHT)
                self.keys[note] = PianoKey(note, True, position, size)
                
                # Set the label
                self.keys[note].label = self._get_key_label(note)
                
                x += self.WHITE_KEY_WIDTH
                white_index += 1
        
        # Then create black keys on top
        for note in range(self.start_note, self.end_note + 1):
            note_type = note % 12
            
            if note_type in {1, 3, 6, 8, 10}:  # Black keys
                # Find the position based on the adjacent white keys
                octave = (note - self.start_note) // 12
                octave_start = self.PIANO_MARGIN + octave * 7 * self.WHITE_KEY_WIDTH
                
                # Calculate x position based on the note type
                if note_type == 1:   # C#
                    x = octave_start + self.BLACK_KEY_OFFSETS[0]
                elif note_type == 3:  # D#
                    x = octave_start + self.BLACK_KEY_OFFSETS[2]
                elif note_type == 6:  # F#
                    x = octave_start + self.BLACK_KEY_OFFSETS[5]
                elif note_type == 8:  # G#
                    x = octave_start + self.BLACK_KEY_OFFSETS[7]
                elif note_type == 10:  # A#
                    x = octave_start + self.BLACK_KEY_OFFSETS[9]
                else:
                    continue  # This shouldn't happen
                
                position = (x, self.PIANO_MARGIN)
                size = (self.BLACK_KEY_WIDTH, self.BLACK_KEY_HEIGHT)
                self.keys[note] = PianoKey(note, False, position, size)
                
                # Set the label (won't be visible since it's below the key)
                self.keys[note].label = self._get_key_label(note)
    
    def _get_key_label(self, note: int) -> str:
        """Generate label for a key based on the label type setting"""
        if self.label_type == 'none':
            return ""
        
        note_name = self.NOTE_NAMES[note % 12]
        octave = (note // 12) - 1  # MIDI note 0 is C-1
        
        if self.label_type == 'note_name':
            return f"{note_name}{octave}"
        elif self.label_type == 'midi_note':
            return str(note)
        elif self.label_type == 'both':
            return f"{note_name}{octave}\n{note}"
        return ""
    
    def resize(self, width: int, height: int) -> None:
        """Resize the piano view"""
        old_width, old_height = self.width, self.height
        
        # Update dimensions
        self.width = width
        self.height = height
        
        # Calculate scale factors
        scale_x = width / old_width if old_width > 0 else 1
        scale_y = height / old_height if old_height > 0 else 1
        
        # Resize the surface
        self.surface = pygame.Surface((width, height))
        
        # Resize and reposition keys
        for key in self.keys.values():
            key.position = (int(key.position[0] * scale_x), int(key.position[1] * scale_y))
            key.size = (int(key.size[0] * scale_x), int(key.size[1] * scale_y))
    
    def set_pressed_notes(self, notes: List[int]) -> None:
        """Update the set of currently pressed notes"""
        self.pressed_notes = set(notes)
        
        # Update the pressed state of each key
        for note, key in self.keys.items():
            key.is_pressed = note in self.pressed_notes
    
    def highlight_notes(self, notes_with_colors: Dict[int, Tuple[int, int, int]]) -> None:
        """Highlight specific notes with custom colors"""
        self.highlighted_notes = notes_with_colors
        
        # Update the highlight colors of each key
        for note, key in self.keys.items():
            key.highlight_color = self.highlighted_notes.get(note, None)
    
    def clear_highlights(self) -> None:
        """Clear all highlighted notes"""
        self.highlighted_notes = {}
        for key in self.keys.values():
            key.highlight_color = None
    
    def get_note_at_position(self, pos: Tuple[int, int]) -> Optional[int]:
        """Get the note number at the given position"""
        # Check black keys first as they are on top
        for note, key in self.keys.items():
            if not key.is_white and key.contains_point(pos):
                return note
        
        # Then check white keys
        for note, key in self.keys.items():
            if key.is_white and key.contains_point(pos):
                return note
        
        return None
    
    def draw(self, target_surface: Optional[pygame.Surface] = None) -> pygame.Surface:
        """Draw the piano and return the surface"""
        # Fill the background
        self.surface.fill(self.colors['background'])
        
        # Draw white keys first
        for note in sorted(self.keys.keys()):
            key = self.keys[note]
            if key.is_white:
                key.draw(self.surface, self.colors, self.show_labels, self.font)
        
        # Then draw black keys on top
        for note in sorted(self.keys.keys()):
            key = self.keys[note]
            if not key.is_white:
                key.draw(self.surface, self.colors, self.show_labels, self.font)
        
        # If a target surface is provided, blit this piano onto it
        if target_surface:
            target_surface.blit(self.surface, (0, 0))
        
        return self.surface
    
    def set_font(self, font: pygame.font.Font) -> None:
        """Set the font used for key labels"""
        self.font = font
    
    def show_octave_markers(self, show: bool = True) -> None:
        """Toggle display of octave markers"""
        if show:
            # Create octave marker labels for C keys
            for note, key in self.keys.items():
                if note % 12 == 0 and key.is_white:  # C keys
                    octave = (note // 12) - 1  # MIDI note 0 is C-1
                    self.keys[note].label = f"C{octave}"
        else:
            # Restore original labels
            for note, key in self.keys.items():
                key.label = self._get_key_label(note)
    
    def set_label_type(self, label_type: str) -> None:
        """Change the type of labels shown on keys"""
        self.label_type = label_type
        # Update all key labels
        for note, key in self.keys.items():
            key.label = self._get_key_label(note)
    
    def set_colors(self, colors: Dict[str, Tuple[int, int, int]]) -> None:
        """Update the color scheme"""
        self.colors.update(colors)

