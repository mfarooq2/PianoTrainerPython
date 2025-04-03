#!/usr/bin/env python3
"""
Piano Trainer Python Application
-------------------------------
Main entry point for the Piano Trainer application.
This file handles the main application loop, mode management,
and command-line argument parsing.

Version: 1.2.0
Author: Based on work by zane
License: MIT
"""

import os
import sys
import argparse
import logging
import pygame
import pygame.midi

# Import application modules
# These will be implemented in separate files
from modules.core.app_state import AppState
from modules.core.event_handler import EventHandler
from modules.visualization.piano_renderer import PianoRenderer
from modules.visualization.ui_renderer import UIRenderer
from modules.midi.midi_player import MidiPlayer
from modules.midi.midi_input import MidiInput
from modules.learning.note_generator import NoteGenerator
from modules.learning.score_tracker import ScoreTracker
from modules.utility.music_theory import MusicTheory
from modules.utility.config import Config

# Set up logging
def setup_logging(log_level):
    """Configure application logging"""
    log_levels = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warning': logging.WARNING,
        'error': logging.ERROR,
        'critical': logging.CRITICAL
    }
    
    level = log_levels.get(log_level.lower(), logging.INFO)
    
    if not os.path.exists('logs'):
        os.makedirs('logs')
        
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/piano_trainer.log'),
            logging.StreamHandler()
        ]
    )
    
    logging.info("Logging initialized at level: %s", log_level)

def parse_arguments():
    """Parse command-line arguments for the application"""
    parser = argparse.ArgumentParser(description='Piano Trainer Python Application')
    
    parser.add_argument(
        '--mode', 
        choices=['freestyle', 'learning', 'analysis'],
        default='freestyle',
        help='Application mode: freestyle (default), learning, or analysis'
    )
    
    parser.add_argument(
        '--midi-file',
        type=str,
        help='Path to a MIDI file to load at startup'
    )
    
    parser.add_argument(
        '--midi-input-device',
        type=int,
        help='MIDI input device ID to use (default: auto-detect)'
    )
    
    parser.add_argument(
        '--midi-output-device',
        type=int,
        help='MIDI output device ID to use (default: auto-detect)'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['debug', 'info', 'warning', 'error', 'critical'],
        default='info',
        help='Set the logging level'
    )
    
    parser.add_argument(
        '--fullscreen',
        action='store_true',
        help='Start the application in fullscreen mode'
    )
    
    parser.add_argument(
        '--difficulty',
        choices=['easy', 'medium', 'hard'],
        default='medium',
        help='Difficulty level for learning mode'
    )
    
    return parser.parse_args()

class PianoTrainerApp:
    """Main Piano Trainer application class"""
    
    def __init__(self, args):
        """Initialize the Piano Trainer application"""
        self.args = args
        self.running = False
        self.config = Config()
        
        # Initialize Pygame
        pygame.init()
        pygame.midi.init()
        
        # Set up display
        self.width, self.height = 1280, 720
        self.display_flags = pygame.HWSURFACE | pygame.DOUBLEBUF
        
        if args.fullscreen:
            self.display_flags |= pygame.FULLSCREEN
            
        self.screen = pygame.display.set_mode((self.width, self.height), self.display_flags)
        pygame.display.set_caption("Piano Trainer v1.2.0")
        
        # Initialize application state
        self.app_state = AppState(initial_mode=args.mode)
        
        # Initialize modules
        self.init_modules()
        
        logging.info("Piano Trainer initialized in %s mode", args.mode)
    
    def init_modules(self):
        """Initialize application modules"""
        # These will be implemented in separate module files
        # For now, we'll just create placeholder instances
        
        self.event_handler = EventHandler(self.app_state)
        self.piano_renderer = PianoRenderer(self.screen, self.config)
        self.ui_renderer = UIRenderer(self.screen, self.app_state, self.config)
        
        # MIDI modules
        midi_input_id = self.args.midi_input_device
        midi_output_id = self.args.midi_output_device
        
        self.midi_player = MidiPlayer(midi_output_id)
        self.midi_input = MidiInput(midi_input_id)
        
        # Learning mode modules
        self.note_generator = NoteGenerator(self.app_state)
        self.score_tracker = ScoreTracker()
        
        # Utility modules
        self.music_theory = MusicTheory()
        
        # Load MIDI file if specified
        if self.args.midi_file:
            try:
                self.midi_player.load_file(self.args.midi_file)
                logging.info("Loaded MIDI file: %s", self.args.midi_file)
            except Exception as e:
                logging.error("Failed to load MIDI file: %s", str(e))
    
    def run(self):
        """Main application loop"""
        self.running = True
        clock = pygame.time.Clock()
        
        while self.running:
            # Process events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.key == pygame.K_F1:
                        self.app_state.set_mode('freestyle')
                    elif event.key == pygame.K_F2:
                        self.app_state.set_mode('learning')
                    elif event.key == pygame.K_F3:
                        self.app_state.set_mode('analysis')
                        
                # Pass event to event handler
                self.event_handler.handle_event(event)
            
            # Process MIDI input
            midi_events = self.midi_input.get_events()
            for midi_event in midi_events:
                self.event_handler.handle_midi_event(midi_event)
            
            # Update game state based on current mode
            if self.app_state.mode == 'freestyle':
                self.update_freestyle_mode()
            elif self.app_state.mode == 'learning':
                self.update_learning_mode()
            elif self.app_state.mode == 'analysis':
                self.update_analysis_mode()
            
            # Render the current frame
            self.render()
            
            # Cap the frame rate
            clock.tick(60)
        
        # Clean up resources
        self.cleanup()
    
    def update_freestyle_mode(self):
        """Update application state in freestyle mode"""
        # In freestyle mode, we just need to update the MIDI player
        # and respond to user input
        self.midi_player.update()
    
    def update_learning_mode(self):
        """Update application state in learning mode"""
        # In learning mode, we need to:
        # 1. Update falling notes
        # 2. Check for hits/misses
        # 3. Update score
        self.note_generator.update()
        self.score_tracker.update(self.note_generator.active_notes, self.midi_input.pressed_keys)
        self.midi_player.update()
    
    def update_analysis_mode(self):
        """Update application state in analysis mode"""
        # In analysis mode, we:
        # 1. Play the MIDI file
        # 2. Show detailed information about the notes
        self.midi_player.update()
    
    def render(self):
        """Render the current frame"""
        # Clear the screen
        self.screen.fill((0, 0, 0))
        
        # Render the piano keyboard
        self.piano_renderer.render(
            self.midi_player.current_notes,
            self.midi_input.pressed_keys
        )
        
        # Render mode-specific UI elements
        if self.app_state.mode == 'freestyle':
            self.ui_renderer.render_freestyle_mode()
        elif self.app_state.mode == 'learning':
            self.ui_renderer.render_learning_mode(
                self.note_generator.active_notes,
                self.score_tracker.score,
                self.score_tracker.accuracy
            )
        elif self.app_state.mode == 'analysis':
            self.ui_renderer.render_analysis_mode(
                self.midi_player.midi_data
            )
        
        # Update the display
        pygame.display.flip()
    
    def cleanup(self):
        """Clean up resources before exiting"""
        logging.info("Shutting down Piano Trainer")
        
        # Close MIDI devices
        if hasattr(self, 'midi_player'):
            self.midi_player.cleanup()
        
        if hasattr(self, 'midi_input'):
            self.midi_input.cleanup()
        
        # Quit Pygame
        pygame.midi.quit()
        pygame.quit()

def main():
    """Application entry point"""
    # Parse command-line arguments
    args = parse_arguments()
    
    # Set up logging
    setup_logging(args.log_level)
    
    try:
        # Create and run the application
        app = PianoTrainerApp(args)
        app.run()
    except Exception as e:
        logging.critical("Unhandled exception: %s", str(e), exc_info=True)
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

