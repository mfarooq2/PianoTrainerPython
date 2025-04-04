#!/usr/bin/env python3
import sys
import os
import pygame
import argparse
from pygame.locals import *

# Import custom modules
from ui.piano_view import PianoView
from audio.sound_engine import SoundEngine
from practice_modes.regular_practice import RegularPracticeMode
from practice_modes.midi_practice.midi_practice import MIDIPracticeMode
from midi_processing.midi_loader import MIDILoader

class EnhancedPianoTrainer:
    def __init__(self):
        """Initialize the Enhanced Piano Trainer application."""
        # Initialize pygame
        pygame.init()
        pygame.display.set_caption("Enhanced Piano Trainer")
        
        # Initialize screen
        self.screen_width = 1280
        self.screen_height = 720
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        
        # Initialize clock for controlling frame rate
        self.clock = pygame.time.Clock()
        self.fps = 60
        
        # Initialize components
        self.sound_engine = SoundEngine(os.path.join("media", "samples"))
        self.piano_view = PianoView(self.screen, self.screen_width, self.screen_height)
        self.midi_loader = MIDILoader(os.path.join("media", "midi"))
        
        # Initialize practice modes
        self.regular_practice = RegularPracticeMode(self.piano_view, self.sound_engine)
        self.midi_practice = MIDIPracticeMode(self.piano_view, self.sound_engine, self.midi_loader)
        
        # Set default active mode
        self.active_mode = self.regular_practice
        
        # Menu state
        self.in_menu = True
        self.menu_options = [
            "Regular Practice", 
            "MIDI Practice", 
            "Settings", 
            "Exit"
        ]
        self.selected_option = 0
        
        # Font for UI
        self.font = pygame.font.SysFont("Arial", 30)
        self.title_font = pygame.font.SysFont("Arial", 50, bold=True)
        
        # Color definitions
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.BLUE = (0, 0, 255)
        self.LIGHT_BLUE = (100, 100, 255)
        self.GRAY = (150, 150, 150)
        
        # Application state
        self.running = True
    
    def handle_events(self):
        """Handle pygame events."""
        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False
                
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    if not self.in_menu:
                        self.in_menu = True
                    else:
                        self.running = False
                
                # Menu navigation
                if self.in_menu:
                    if event.key == K_UP:
                        self.selected_option = (self.selected_option - 1) % len(self.menu_options)
                    elif event.key == K_DOWN:
                        self.selected_option = (self.selected_option + 1) % len(self.menu_options)
                    elif event.key == K_RETURN:
                        self.execute_menu_option(self.selected_option)
                else:
                    # Pass events to active mode
                    self.active_mode.handle_event(event)
    
    def execute_menu_option(self, option):
        """Execute the selected menu option."""
        if option == 0:  # Regular Practice
            self.active_mode = self.regular_practice
            self.in_menu = False
        elif option == 1:  # MIDI Practice
            self.active_mode = self.midi_practice
            self.in_menu = False
        elif option == 2:  # Settings
            # Will implement settings later
            pass
        elif option == 3:  # Exit
            self.running = False
    
    def draw_menu(self):
        """Draw the main menu."""
        self.screen.fill(self.BLACK)
        
        # Draw title
        title = self.title_font.render("Enhanced Piano Trainer", True, self.WHITE)
        title_rect = title.get_rect(center=(self.screen_width // 2, 100))
        self.screen.blit(title, title_rect)
        
        # Draw menu options
        for i, option in enumerate(self.menu_options):
            color = self.LIGHT_BLUE if i == self.selected_option else self.WHITE
            text = self.font.render(option, True, color)
            text_rect = text.get_rect(center=(self.screen_width // 2, 250 + i * 60))
            self.screen.blit(text, text_rect)
        
        # Draw instructions
        instructions = self.font.render("Use UP/DOWN arrows to navigate, ENTER to select", True, self.GRAY)
        instructions_rect = instructions.get_rect(center=(self.screen_width // 2, self.screen_height - 100))
        self.screen.blit(instructions, instructions_rect)
        
        pygame.display.flip()
    
    def run(self):
        """Main application loop."""
        while self.running:
            self.handle_events()
            
            if self.in_menu:
                self.draw_menu()
            else:
                # Update and render active mode
                self.active_mode.update()
                self.active_mode.render()
            
            self.clock.tick(self.fps)
        
        # Cleanup
        pygame.quit()
        sys.exit()


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Enhanced Piano Trainer")
    parser.add_argument("--midi", type=str, help="Path to MIDI file to load on startup")
    parser.add_argument("--mode", type=str, choices=["regular", "midi"], 
                        default="regular", help="Practice mode to start with")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    app = EnhancedPianoTrainer()
    
    # Handle command line arguments
    if args.midi:
        app.midi_practice.load_midi(args.midi)
        app.active_mode = app.midi_practice
        app.in_menu = False
    
    if args.mode == "midi" and not args.midi:
        app.active_mode = app.midi_practice
        app.in_menu = False
    
    # Run the application
    app.run()

