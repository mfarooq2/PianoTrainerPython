import pygame
from pygame import Rect, Surface
import time
from typing import Dict, List, Tuple, Optional

from modules.core.app_state import AppState, AppMode
from modules.utility.config import Config


class UIRenderer:
    """
    Handles rendering of UI elements for different application modes.
    This includes status bars, titles, help screens, and mode-specific overlays.
    """
    
    def __init__(self, config: Config, app_state: AppState):
        """
        Initialize the UI renderer with configuration and application state.
        
        Args:
            config: Application configuration
            app_state: Current application state
        """
        self.config = config
        self.app_state = app_state
        self.fonts = {}
        self.load_fonts()
        
    def load_fonts(self):
        """Load and cache fonts used in the UI"""
        self.fonts['small'] = pygame.font.Font(None, 22)
        self.fonts['medium'] = pygame.font.Font(None, 28)
        self.fonts['large'] = pygame.font.Font(None, 36)
        self.fonts['title'] = pygame.font.Font(None, 48)
        
    def render_status_bar(self, screen: Surface, midi_info: Dict = None):
        """
        Render the status bar at the bottom of the screen.
        
        Args:
            screen: Pygame surface to render on
            midi_info: Dictionary containing MIDI playback information
        """
        # Draw status bar background
        status_bar_rect = Rect(0, screen.get_height() - 30, screen.get_width(), 30)
        pygame.draw.rect(screen, (40, 40, 40), status_bar_rect)
        
        # Render application mode
        mode_text = f"Mode: {self.app_state.current_mode.name}"
        mode_surface = self.fonts['small'].render(mode_text, True, (200, 200, 200))
        screen.blit(mode_surface, (10, screen.get_height() - 25))
        
        # Render MIDI file info if available
        if midi_info and 'filename' in midi_info:
            file_text = f"File: {midi_info['filename']}"
            file_surface = self.fonts['small'].render(file_text, True, (200, 200, 200))
            screen.blit(file_surface, (200, screen.get_height() - 25))
            
            if 'position' in midi_info and 'duration' in midi_info:
                time_text = f"Time: {self._format_time(midi_info['position'])}/{self._format_time(midi_info['duration'])}"
                time_surface = self.fonts['small'].render(time_text, True, (200, 200, 200))
                screen.blit(time_surface, (450, screen.get_height() - 25))
                
        # Render help hint
        help_text = "Press F1 for help"
        help_surface = self.fonts['small'].render(help_text, True, (200, 200, 200))
        screen.blit(help_surface, (screen.get_width() - help_surface.get_width() - 10, 
                                   screen.get_height() - 25))
    
    def render_title(self, screen: Surface, title: str, subtitle: str = None):
        """
        Render a title and optional subtitle centered at the top of the screen.
        
        Args:
            screen: Pygame surface to render on
            title: Main title text
            subtitle: Optional subtitle text
        """
        # Render main title
        title_surface = self.fonts['title'].render(title, True, (255, 255, 255))
        title_rect = title_surface.get_rect(centerx=screen.get_width() // 2, y=20)
        screen.blit(title_surface, title_rect)
        
        # Render subtitle if provided
        if subtitle:
            subtitle_surface = self.fonts['medium'].render(subtitle, True, (200, 200, 200))
            subtitle_rect = subtitle_surface.get_rect(centerx=screen.get_width() // 2, 
                                                     y=title_rect.bottom + 10)
            screen.blit(subtitle_surface, subtitle_rect)
    
    def render_mode_overlay(self, screen: Surface):
        """
        Render mode-specific UI overlays based on current application mode.
        
        Args:
            screen: Pygame surface to render on
        """
        if self.app_state.current_mode == AppMode.FREESTYLE:
            self._render_freestyle_overlay(screen)
        elif self.app_state.current_mode == AppMode.LEARNING:
            self._render_learning_overlay(screen)
        elif self.app_state.current_mode == AppMode.ANALYSIS:
            self._render_analysis_overlay(screen)
    
    def _render_freestyle_overlay(self, screen: Surface):
        """Render UI overlay for freestyle mode"""
        info_text = "Freestyle Mode - Play any keys or load a MIDI file"
        info_surface = self.fonts['medium'].render(info_text, True, (200, 200, 255))
        screen.blit(info_surface, (20, 80))
    
    def _render_learning_overlay(self, screen: Surface):
        """Render UI overlay for learning mode"""
        # This will be minimal as the note falling visualization will be the focus
        if self.app_state.is_paused:
            pause_text = "PAUSED - Press Space to continue"
            pause_surface = self.fonts['large'].render(pause_text, True, (255, 255, 0))
            pause_rect = pause_surface.get_rect(center=(screen.get_width() // 2, 
                                                      screen.get_height() // 2 - 100))
            screen.blit(pause_surface, pause_rect)
    
    def _render_analysis_overlay(self, screen: Surface):
        """Render UI overlay for analysis mode"""
        info_text = "Analysis Mode - Notes and chord detection"
        info_surface = self.fonts['medium'].render(info_text, True, (200, 255, 200))
        screen.blit(info_surface, (20, 80))
        
        # Additional analysis information would be rendered here
    
    def render_help_screen(self, screen: Surface):
        """
        Render the help screen overlay with keyboard shortcuts and instructions.
        
        Args:
            screen: Pygame surface to render on
        """
        # Create semi-transparent overlay
        overlay = Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))  # Black with 80% opacity
        screen.blit(overlay, (0, 0))
        
        # Render help title
        help_title = "Piano Trainer - Help & Keyboard Shortcuts"
        title_surface = self.fonts['title'].render(help_title, True, (255, 255, 255))
        title_rect = title_surface.get_rect(centerx=screen.get_width() // 2, y=40)
        screen.blit(title_surface, title_rect)
        
        # Define help sections and content
        sections = [
            ("General Controls", [
                "F1: Toggle Help Screen",
                "ESC: Quit Application",
                "Tab: Cycle Between Modes",
                "Space: Pause/Resume",
                "Ctrl+O: Open MIDI File",
            ]),
            ("Playback Controls", [
                "P: Play/Pause MIDI",
                "S: Stop MIDI Playback",
                "Left/Right Arrows: Rewind/Fast Forward",
                "Ctrl+Left/Right: Jump to Previous/Next Section",
            ]),
            ("Learning Mode", [
                "1-5: Set Difficulty Level",
                "R: Restart Current Exercise",
                "Ctrl+R: Reset Score",
                "Ctrl+S: Save Progress",
            ]),
            ("Visualization Options", [
                "C: Toggle Chord Detection",
                "N: Toggle Note Names",
                "G: Toggle Piano Guide",
                "Ctrl+Up/Down: Adjust Falling Speed",
            ]),
        ]
        
        # Calculate layout
        section_width = screen.get_width() // 2 - 40
        y_offset = title_rect.bottom + 30
        
        # Render each section
        for i, (section_title, items) in enumerate(sections):
            # Determine position (2 columns)
            col = i % 2
            row = i // 2
            x = 40 + col * (section_width + 40)
            y = y_offset + row * 180
            
            # Render section title
            section_surface = self.fonts['large'].render(section_title, True, (255, 220, 150))
            screen.blit(section_surface, (x, y))
            
            # Render section items
            for j, item in enumerate(items):
                item_surface = self.fonts['medium'].render(item, True, (220, 220, 220))
                screen.blit(item_surface, (x + 10, y + 40 + j * 30))
        
        # Render footer with version info
        version_text = f"Piano Trainer v{self.config.version} - Press F1 to close help"
        version_surface = self.fonts['small'].render(version_text, True, (150, 150, 150))
        version_rect = version_surface.get_rect(centerx=screen.get_width() // 2, 
                                               bottom=screen.get_height() - 20)
        screen.blit(version_surface, version_rect)
    
    def render_loading_screen(self, screen: Surface, message: str, progress: float = None):
        """
        Render a loading screen with optional progress bar.
        
        Args:
            screen: Pygame surface to render on
            message: Loading message to display
            progress: Optional progress value between 0.0 and 1.0
        """
        # Clear screen
        screen.fill((0, 0, 0))
        
        # Render loading message
        loading_surface = self.fonts['large'].render(message, True, (255, 255, 255))
        loading_rect = loading_surface.get_rect(center=(screen.get_width() // 2, 
                                                     screen.get_height() // 2 - 40))
        screen.blit(loading_surface, loading_rect)
        
        # Render progress bar if progress is provided
        if progress is not None:
            bar_width = 400
            bar_height = 20
            bar_rect = Rect((screen.get_width() - bar_width) // 2,
                           screen.get_height() // 2 + 20,
                           bar_width, bar_height)
            
            # Draw progress bar background
            pygame.draw.rect(screen, (60, 60, 60), bar_rect)
            
            # Draw progress bar fill
            fill_width = int(bar_width * max(0, min(1, progress)))
            fill_rect = Rect(bar_rect.left, bar_rect.top, fill_width, bar_height)
            pygame.draw.rect(screen, (100, 180, 255), fill_rect)
            
            # Draw progress text
            progress_text = f"{int(progress * 100)}%"
            progress_surface = self.fonts['small'].render(progress_text, True, (255, 255, 255))
            progress_rect = progress_surface.get_rect(center=bar_rect.center)
            screen.blit(progress_surface, progress_rect)
        
        # Update the display
        pygame.display.flip()
    
    def _format_time(self, seconds: float) -> str:
        """
        Format time in seconds to MM:SS format.
        
        Args:
            seconds: Time in seconds
            
        Returns:
            Formatted time string
        """
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"

