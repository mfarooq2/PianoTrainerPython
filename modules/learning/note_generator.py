import pygame
import random
from typing import List, Dict, Tuple, Optional, Set
import time

class Note:
    """
    Represents a falling note in the learning mode.
    """
    def __init__(self, note_number: int, start_time: float, 
                 velocity: int = 64, duration: float = 0.5):
        self.note_number = note_number
        self.start_time = start_time
        self.velocity = velocity
        self.duration = duration
        self.hit = False
        self.missed = False
        self.y_pos = 0  # Current y position (will be updated during animation)
        self.height = 20  # Default height in pixels
        self.should_be_removed = False

    def mark_as_hit(self):
        """Mark this note as successfully hit."""
        self.hit = True
        
    def mark_as_missed(self):
        """Mark this note as missed."""
        self.missed = True
        
    def update_position(self, current_time: float, fall_speed: float, pause_time: float = 0):
        """
        Update the y position of this note based on the current time.
        
        Args:
            current_time: Current time in seconds
            fall_speed: Speed at which notes fall (pixels per second)
            pause_time: Total time the note generator has been paused
        """
        # Adjust for any pause time
        effective_time = current_time - pause_time
        time_diff = effective_time - self.start_time
        
        # Calculate position based on time difference and fall speed
        self.y_pos = time_diff * fall_speed
        
    def should_be_played(self, current_time: float, pause_time: float = 0) -> bool:
        """
        Determine if this note should be played at the current time.
        
        Args:
            current_time: Current time in seconds
            pause_time: Total time the note generator has been paused
            
        Returns:
            True if the note should be played, False otherwise
        """
        effective_time = current_time - pause_time
        return effective_time >= self.start_time and not self.hit and not self.missed


class NoteGenerator:
    """
    Generates and manages falling notes for the learning mode.
    """
    def __init__(self, midi_data: List[Dict], fall_distance: int, 
                 fall_speed: float, screen_height: int):
        """
        Initialize the note generator.
        
        Args:
            midi_data: List of MIDI events containing note information
            fall_distance: Distance notes need to fall (usually piano height)
            fall_speed: Speed at which notes fall (pixels per second)
            screen_height: Height of the screen in pixels
        """
        self.midi_data = midi_data
        self.fall_distance = fall_distance
        self.fall_speed = fall_speed
        self.screen_height = screen_height
        
        self.active_notes: List[Note] = []
        self.upcoming_notes: List[Note] = []
        self.hit_notes: Set[int] = set()  # Note numbers that have been hit
        self.current_time = 0
        
        # Pause/resume state tracking
        self.paused = False
        self.pause_start_time = 0
        self.total_pause_time = 0
        
        # Initialize upcoming notes from MIDI data
        self._parse_midi_data()
        
    def _parse_midi_data(self):
        """Parse MIDI data to create upcoming notes."""
        self.upcoming_notes = []
        
        for event in self.midi_data:
            if event['type'] == 'note_on' and event['velocity'] > 0:
                # Create a new note
                note = Note(
                    note_number=event['note'],
                    start_time=event['time'],
                    velocity=event['velocity'],
                    duration=0.5  # Default duration, will be updated with note_off
                )
                
                # Find corresponding note_off event to determine duration
                for off_event in self.midi_data:
                    if (off_event['type'] == 'note_off' or 
                        (off_event['type'] == 'note_on' and off_event['velocity'] == 0)) and \
                       off_event['note'] == event['note'] and \
                       off_event['time'] > event['time']:
                        note.duration = off_event['time'] - event['time']
                        break
                        
                self.upcoming_notes.append(note)
        
        # Sort notes by start time
        self.upcoming_notes.sort(key=lambda x: x.start_time)
                
    def update(self, delta_time: float):
        """
        Update the state of all notes.
        
        Args:
            delta_time: Time passed since the last update in seconds
        """
        if self.paused:
            return
            
        # Update current time
        self.current_time += delta_time
        
        # Check for new notes to activate
        self._activate_new_notes()
        
        # Update positions of active notes
        for note in self.active_notes:
            note.update_position(self.current_time, self.fall_speed, self.total_pause_time)
            
            # Check if note has reached the piano (bottom of screen)
            if note.y_pos >= self.fall_distance and not note.hit and not note.missed:
                note.mark_as_missed()
                
            # Check if note should be removed (it's been hit or has fallen off screen)
            if (note.hit or (note.missed and note.y_pos > self.fall_distance + 50)):
                note.should_be_removed = True
                
        # Remove notes that should be removed
        self.active_notes = [note for note in self.active_notes 
                            if not note.should_be_removed]
                
    def _activate_new_notes(self):
        """Check for new notes to activate based on the current time."""
        # Calculate time to reach the piano
        time_to_reach_piano = self.fall_distance / self.fall_speed
        
        # Look for notes that should start falling now
        activate_before_time = self.current_time + time_to_reach_piano
        
        new_active_notes = []
        remaining_upcoming = []
        
        for note in self.upcoming_notes:
            # If the note should start falling to reach the piano at the right time
            adjusted_start_time = note.start_time + self.total_pause_time
            if adjusted_start_time <= activate_before_time:
                new_active_notes.append(note)
            else:
                remaining_upcoming.append(note)
                
        # Add new active notes
        self.active_notes.extend(new_active_notes)
        # Update upcoming notes list
        self.upcoming_notes = remaining_upcoming
        
    def handle_note_played(self, note_number: int) -> bool:
        """
        Handle a note being played by the user.
        
        Args:
            note_number: MIDI note number that was played
            
        Returns:
            True if the note was hit, False otherwise
        """
        # Find the lowest (oldest) matching note that hasn't been hit yet
        hit_zone_top = self.fall_distance - 30
        hit_zone_bottom = self.fall_distance + 10
        
        for note in self.active_notes:
            if (note.note_number == note_number and 
                not note.hit and 
                not note.missed and
                hit_zone_top <= note.y_pos <= hit_zone_bottom):
                
                note.mark_as_hit()
                self.hit_notes.add(note_number)
                return True
                
        return False
        
    def reset(self):
        """Reset the note generator to its initial state."""
        self.active_notes = []
        self.hit_notes = set()
        self.current_time = 0
        self.paused = False
        self.pause_start_time = 0
        self.total_pause_time = 0
        self._parse_midi_data()  # Reload notes from MIDI data
        
    def pause(self):
        """Pause the note generator."""
        if not self.paused:
            self.paused = True
            self.pause_start_time = time.time()
            
    def resume(self):
        """Resume the note generator after being paused."""
        if self.paused:
            self.paused = False
            pause_duration = time.time() - self.pause_start_time
            self.total_pause_time += pause_duration
            
    def is_complete(self) -> bool:
        """
        Check if all notes have been processed.
        
        Returns:
            True if all notes have been processed, False otherwise
        """
        return len(self.upcoming_notes) == 0 and len(self.active_notes) == 0
        
    def get_visible_notes(self) -> List[Note]:
        """
        Get all currently visible notes for rendering.
        
        Returns:
            List of visible notes
        """
        return self.active_notes
        
    def get_current_stats(self) -> Dict:
        """
        Get current statistics about the note generator.
        
        Returns:
            Dictionary containing statistics
        """
        total_notes = len(self.hit_notes) + sum(1 for note in self.active_notes if note.missed)
        hit_notes = len(self.hit_notes)
        
        return {
            'total_notes': total_notes,
            'hit_notes': hit_notes,
            'accuracy': hit_notes / max(total_notes, 1) * 100,
            'remaining_notes': len(self.upcoming_notes) + len(self.active_notes),
            'is_complete': self.is_complete()
        }


import pygame
import random
import time
import numpy as np
from enum import Enum

class NoteStatus(Enum):
    """Enumeration of possible note statuses."""
    FALLING = 0    # Note is falling
    HIT = 1        # Note was correctly played
    MISSED = 2     # Note was missed
    WRONG = 3      # Wrong note was played
    EXPIRED = 4    # Note has moved off screen

class FallingNote:
    """Class representing a single falling note in the learning mode."""
    def __init__(self, note_number, start_time, speed, screen_height, target_y):
        """
        Initialize a falling note.
        
        Args:
            note_number (int): MIDI note number
            start_time (float): Time when the note started falling
            speed (float): Speed of the falling note in pixels per second
            screen_height (int): Height of the screen
            target_y (int): Y position where the note should be hit
        """
        self.note_number = note_number
        self.start_time = start_time
        self.speed = speed
        self.screen_height = screen_height
        self.target_y = target_y
        self.status = NoteStatus.FALLING
        self.color = (100, 149, 237)  # Cornflower blue
        self.hit_time = None
        
        # Position is calculated based on elapsed time
        self.y = 0  # Start at the top
        
        # Timing window for "perfect" and "good" hits
        self.perfect_window = 0.05  # seconds
        self.good_window = 0.15     # seconds
    
    def update(self, current_time):
        """
        Update the note's position based on elapsed time.
        
        Args:
            current_time (float): Current time in seconds
            
        Returns:
            bool: True if the note is still active, False if it should be removed
        """
        if self.status == NoteStatus.FALLING:
            # Calculate the y position based on elapsed time
            elapsed = current_time - self.start_time
            self.y = elapsed * self.speed
            
            # Check if note has moved past the target
            if self.y > self.screen_height:
                self.status = NoteStatus.EXPIRED
                return False
        
        # Keep hit/missed notes on screen for a short time
        elif self.status in (NoteStatus.HIT, NoteStatus.MISSED, NoteStatus.WRONG):
            if current_time - self.hit_time > 0.5:  # Remove after 0.5 seconds
                return False
        
        return True
    
    def check_hit(self, note_number, current_time):
        """
        Check if the note was hit correctly.
        
        Args:
            note_number (int): MIDI note number that was played
            current_time (float): Current time in seconds
            
        Returns:
            tuple: (hit_status, score) where hit_status is one of:
                   "perfect", "good", "miss", "wrong", or None
                   and score is the point value (0 for miss/wrong)
        """
        if self.status != NoteStatus.FALLING:
            return None, 0
        
        # Calculate timing error (distance from target)
        elapsed = current_time - self.start_time
        expected_time = self.target_y / self.speed
        timing_error = abs(elapsed - expected_time)
        
        # Check if the correct note was played
        if note_number == self.note_number:
            self.hit_time = current_time
            
            # Check timing
            if timing_error <= self.perfect_window:
                self.status = NoteStatus.HIT
                self.color = (0, 255, 0)  # Green for perfect
                return "perfect", 100
            elif timing_error <= self.good_window:
                self.status = NoteStatus.HIT
                self.color = (255, 255, 0)  # Yellow for good
                return "good", 50
            else:
                # Too early or too late, but still the right note
                self.status = NoteStatus.HIT
                self.color = (255, 165, 0)  # Orange for hit but timing off
                return "hit", 25
        else:
            # Wrong note
            self.status = NoteStatus.WRONG
            self.color = (255, 0, 0)  # Red for wrong note
            self.hit_time = current_time
            return "wrong", 0
    
    def mark_as_missed(self, current_time):
        """
        Mark the note as missed (not played in time).
        
        Args:
            current_time (float): Current time in seconds
        """
        if self.status == NoteStatus.FALLING:
            self.status = NoteStatus.MISSED
            self.color = (128, 128, 128)  # Gray for missed
            self.hit_time = current_time


class NoteGenerator:
    """
    Class responsible for generating and managing falling notes in the learning mode.
    """
    def __init__(self, config, midi_player):
        """
        Initialize the note generator.
        
        Args:
            config (Config): Application configuration
            midi_player (MIDIPlayer): MIDI player instance
        """
        self.config = config
        self.midi_player = midi_player
        self.screen_width = config.screen_width
        self.screen_height = config.screen_height
        self.piano_height = config.piano_height
        
        # Target y-position is at the top of the piano
        self.target_y = self.screen_height - self.piano_height
        
        # Speed of falling notes in pixels per second
        self.note_speed = 200  # Adjust based on difficulty
        
        # List of active falling notes
        self.active_notes = []
        
        # Queue of upcoming notes from the MIDI file
        self.note_queue = []
        
        # Track learning mode stats
        self.score = 0
        self.perfect_hits = 0
        self.good_hits = 0
        self.hits = 0
        self.misses = 0
        self.wrong_notes = 0
        
        # Time management
        self.start_time = None
        self.current_time = None
        self.paused = False
        self.pause_start_time = None
        self.total_pause_time = 0
    
    def load_midi_file(self, midi_data):
        """
        Load notes from MIDI data into the note queue.
        
        Args:
            midi_data (list): List of MIDI note events from the MIDI player
        """
        self.note_queue = []
        
        for event in midi_data:
            if event['type'] == 'note_on' and event['velocity'] > 0:
                self.note_queue.append({
                    'note': event['note'],
                    'time': event['time']
                })
        
        # Sort by time
        self.note_queue.sort(key=lambda x: x['time'])
    
    def start(self):
        """Start the note generator and reset statistics."""
        self.start_time = time.time()
        self.current_time = self.start_time
        self.active_notes = []
        
        # Reset stats
        self.score = 0
        self.perfect_hits = 0
        self.good_hits = 0
        self.hits = 0
        self.misses = 0
        self.wrong_notes = 0
        
        self.paused = False
        self.total_pause_time = 0
    
    def pause(self):
        """Pause the note generator."""
        if not self.paused:
            self.paused = True
            self.pause_start_time = time.time()
    
    def resume(self):
        """Resume the note generator."""
        if self.paused:
            self.paused = False
            pause_duration = time.time() - self.pause_

