import pygame
from typing import Dict, List, Optional, Tuple, Any
import time

from ..core.app_state import AppState, AppMode
from ..learning.score_tracker import ScoreTracker
from ..learning.note_generator import NoteGenerator

class UIRenderer:
    """
    Handles rendering the UI for different modes of the application.
    This includes status bars, scores, mode indicators, and other UI elements.
    """
    def __init__(self, width: int, height: int):
        """
        Initialize the UI renderer.
        
        Args:
            width: Width of the application window
            height: Height of the application window
        """
        self.width = width
        self.height = height
        self.fonts: Dict[str, pygame.font.Font] = {}
        self.colors = {
            'text': (255, 255, 255),
            'background': (30, 30, 30),
            'accent': (65, 105, 225),  # Royal blue
            'success': (50, 205, 50),  # Lime green
            'error': (220, 20, 60),    # Crimson
            'warning': (255, 165, 0),  # Orange
            'highlight': (255, 215, 0)  # Gold
        }
        self._init_fonts()
        
    def _init_fonts(self):
        """Initialize the fonts used in the UI."""
        pygame.font.init()
        try:
            # Try to load a nice font, fall back to default if not available
            self.fonts['title'] = pygame.font.SysFont("Arial", 36, bold=True)
            self.fonts['heading'] = pygame.font.SysFont("Arial", 24, bold=True)
            self.fonts['normal'] = pygame.font.SysFont("Arial", 18)
            self.fonts['small'] = pygame.font.SysFont("Arial", 14)
        except:
            # If font loading fails, use the default font
            default_font = pygame.font.Font(None, 24)
            self.fonts = {
                'title': pygame.font.Font(None, 36),
                'heading': pygame.font.Font(None, 28),
                'normal': pygame.font.Font(None, 24),
                'small': pygame.font.Font(None, 18)
            }
            
    def resize(self, width: int, height: int):
        """
        Update the renderer dimensions when the window is resized.
        
        Args:
            width: New width of the window
            height: New height of the window
        """
        self.width = width
        self.height = height
        
    def render_header(self, surface: pygame.Surface, app_state: AppState):
        """
        Render the application header with title and mode information.
        
        Args:
            surface: Pygame surface to render on
            app_state: Current application state
        """
        # Background for header
        header_rect = pygame.Rect(0, 0, self.width, 50)
        pygame.draw.rect(surface, (20, 20, 20), header_rect)
        pygame.draw.line(surface, self.colors['accent'], (0, 50), (self.width, 50), 2)
        
        # Application title
        title_text = self.fonts['title'].render("Piano Trainer", True, self.colors['text'])
        surface.blit(title_text, (20, 10))
        
        # Current mode
        mode_text = f"Mode: {app_state.mode.name.capitalize()}"
        mode_surface = self.fonts['normal'].render(mode_text, True, self.colors['accent'])
        surface.blit(mode_surface, (self.width - mode_surface.get_width() - 20, 15))
        
    def render_status_bar(self, surface: pygame.Surface, app_state: AppState):
        """
        Render the status bar at the bottom of the screen.
        
        Args:
            surface: Pygame surface to render on
            app_state: Current application state
        """
        status_height = 30
        status_rect = pygame.Rect(0, self.height - status_height, self.width, status_height)
        pygame.draw.rect(surface, (20, 20, 20), status_rect)
        pygame.draw.line(surface, self.colors['accent'], (0, self.height - status_height), (self.width, self.height - status_height), 2)
        
        # Status text varies by mode
        status_text = self._get_status_text(app_state)
        status_surface = self.fonts['small'].render(status_text, True, self.colors['text'])
        surface.blit(status_surface, (10, self.height - status_height + 7))
        
        # Help text on the right
        help_text = "Press ESC to exit, F1 for help"
        help_surface = self.fonts['small'].render(help_text, True, self.colors['text'])
        surface.blit(help_surface, (self.width - help_surface.get_width() - 10, self.height - status_height + 7))
        
    def _get_status_text(self, app_state: AppState) -> str:
        """
        Get the appropriate status text based on the current mode.
        
        Args:
            app_state: Current application state
            
        Returns:
            Status text to display
        """
        if app_state.mode == AppMode.FREESTYLE:
            if app_state.midi_input and app_state.midi_input.is_connected():
                return f"MIDI Input: {app_state.midi_input.get_device_name()}"
            else:
                return "No MIDI device connected. Use computer keyboard instead."
        elif app_state.mode == AppMode.LEARNING:
            return f"Song: {app_state.current_song_name} | Difficulty: {app_state.current_difficulty}"
        elif app_state.mode == AppMode.ANALYSIS:
            return f"Analyzing: {app_state.current_song_name}"
        else:
            return "Ready"
    
    def render_freestyle_mode(self, surface: pygame.Surface, app_state: AppState):
        """
        Render UI elements specific to freestyle mode.
        
        Args:
            surface: Pygame surface to render on
            app_state: Current application state
        """
        # In freestyle mode, we might show key labels or active notes
        self._render_keyboard_labels(surface)
        
        # Current octave indicator
        octave_text = f"Octave: {app_state.keyboard_octave}"
        octave_surface = self.fonts['normal'].render(octave_text, True, self.colors['text'])
        surface.blit(octave_surface, (20, 60))
        
    def _render_keyboard_labels(self, surface: pygame.Surface):
        """Render labels for the piano keys if needed."""
        # This would show note names on the keys
        pass
        
    def render_learning_mode(self, surface: pygame.Surface, app_state: AppState, 
                             score_tracker: ScoreTracker, note_generator: NoteGenerator):
        """
        Render UI elements specific to learning mode.
        
        Args:
            surface: Pygame surface to render on
            app_state: Current application state
            score_tracker: Score tracker instance
            note_generator: Note generator instance
        """
        # Score display
        score_text = f"Score: {score_tracker.score}"
        score_surface = self.fonts['heading'].render(score_text, True, self.colors['highlight'])
        surface.blit(score_surface, (20, 60))
        
        # Accuracy
        accuracy_text = f"Accuracy: {score_tracker.get_accuracy():.1f}%"
        accuracy_surface = self.fonts['normal'].render(accuracy_text, True, self.colors['text'])
        surface.blit(accuracy_surface, (20, 95))
        
        # Combo
        combo_color = self.colors['text']
        if score_tracker.combo >= 10:
            combo_color = self.colors['success']
        elif score_tracker.combo >= 5:
            combo_color = self.colors['accent']
            
        combo_text = f"Combo: {score_tracker.combo}"
        combo_surface = self.fonts['normal'].render(combo_text, True, combo_color)
        surface.blit(combo_surface, (20, 125))
        
        # Song progress
        if note_generator.total_notes > 0:
            progress = note_generator.notes_processed / note_generator.total_notes
            progress_text = f"Progress: {progress:.0%}"
            progress_surface = self.fonts['normal'].render(progress_text, True, self.colors['text'])
            surface.blit(progress_surface, (20, 155))
            
            # Progress bar
            progress_bar_rect = pygame.Rect(140, 155, 200, 20)
            pygame.draw.rect(surface, (60, 60, 60), progress_bar_rect)
            fill_rect = pygame.Rect(140, 155, 200 * progress, 20)
            pygame.draw.rect(surface, self.colors['accent'], fill_rect)
        
    def render_analysis_mode(self, surface: pygame.Surface, app_state: AppState):
        """
        Render UI elements specific to analysis mode.
        
        Args:
            surface: Pygame surface to render on
            app_state: Current application state
        """
        # Song information
        song_text = f"Analyzing: {app_state.current_song_name}"
        song_surface = self.fonts['heading'].render(song_text, True, self.colors['text'])
        surface.blit(song_surface, (20, 60))
        
        # Information about the MIDI file
        if app_state.midi_player and app_state.midi_player.midi_data:
            midi_info = self._get_midi_file_info(app_state)
            y_pos = 100
            
            for key, value in midi_info.items():
                info_text = f"{key}: {value}"
                info_surface = self.fonts['normal'].render(info_text, True, self.colors['text'])
                surface.blit(info_surface, (20, y_pos))
                y_pos += 30
    
    def _get_midi_file_info(self, app_state: AppState) -> Dict[str, Any]:
        """Extract information about the loaded MIDI file."""
        midi_data = app_state.midi_player.midi_data
        return {
            "Number of tracks": len(midi_data.tracks),
            "Time division": midi_data.ticks_per_beat,
            "Total notes": app_state.midi_player.total_notes,
            "Duration": f"{app_state.midi_player.get_duration():.1f} seconds",
            "BPM": app_state.midi_player.get_tempo()
        }
        
    def render_game_over(self, surface: pygame.Surface, score_tracker: ScoreTracker):
        """
        Render the game over screen with final score and stats.
        
        Args:
            surface: Pygame surface to render on
            score_tracker: Score tracker with final results
        """
        # Semi-transparent overlay
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))  # Black with alpha
        surface.blit(overlay, (0, 0))
        
        # Game over text
        game_over_text = self.fonts['title'].render("Song Complete!", True, self.colors['accent'])
        text_x = (self.width - game_over_text.get_width()) // 2
        surface.blit(game_over_text, (text_x, 150))
        
        # Stats
        stats = [
            f"Final Score: {score_tracker.score}",
            f"Accuracy: {score_tracker.get_accuracy():.1f}%",
            f"Notes Hit: {score_tracker.notes_hit}",
            f"Notes Missed: {score_tracker.notes_missed}",
            f"Max Combo: {score_tracker.max_combo}",
            f"Time: {score_tracker.get_session_time():.1f} seconds"
        ]
        
        y_pos = 220
        for stat in stats:
            stat_surface = self.fonts['heading'].render(stat, True, self.colors['text'])
            text_x = (self.width - stat_surface.get_width()) // 2
            surface.blit(stat_surface, (text_x, y_pos))
            y_pos += 40
            
        # Continue prompt
        continue_text = self.fonts['normal'].render("Press any key to continue", True, self.colors['text'])
        text_x = (self.width - continue_text.get_width()) // 2
        surface.blit(continue_text, (text_x, y_pos + 30))
        
    def render_help_screen(self, surface: pygame.Surface, app_state: AppState):
        """
        Render the help screen with key controls and instructions.
        
        Args:
            surface: Pygame surface to render on
            app_state: Current application state
        """
        # Semi-transparent overlay
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 230))  # Black with alpha
        surface.blit(overlay, (0, 0))
        
        # Help title
        help_text = self.fonts['title'].render("Piano Trainer - Help", True, self.colors['accent'])
        text_

